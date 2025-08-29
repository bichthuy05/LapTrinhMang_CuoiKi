# tools/http_gateway.py
import json
import os
import socket
import threading
import time
import uuid
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs


HOST, PORT = "127.0.0.1", 8080
MOCK_HOST, MOCK_PORT = "127.0.0.1", 5555


class Session:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.sock: socket.socket | None = None
        self.recv_buf = b""
        self.queue_lock = threading.Lock()
        self.queue: list[dict] = []
        self.pending_lock = threading.Lock()
        self.pending: list[dict] = []  # {expected:set[str], response:dict|None, event:Event}

    def ensure_sock(self):
        if self.sock is not None:
            return
        with self.lock:
            if self.sock is not None:
                return
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((MOCK_HOST, MOCK_PORT))
            self.sock = s
            t = threading.Thread(target=self._reader_loop, daemon=True)
            t.start()

    def _reader_loop(self):
        assert self.sock is not None
        s = self.sock
        try:
            while True:
                data = s.recv(4096)
                if not data:
                    break
                self.recv_buf += data
                while b"\n" in self.recv_buf:
                    line, self.recv_buf = self.recv_buf.split(b"\n", 1)
                    if not line:
                        continue
                    try:
                        msg = json.loads(line.decode())
                    except json.JSONDecodeError:
                        continue
                    # push to poll queue
                    with self.queue_lock:
                        self.queue.append(msg)
                    # resolve pending
                    mtype = msg.get("type")
                    if not mtype:
                        continue
                    with self.pending_lock:
                        for entry in self.pending:
                            if entry["response"] is None and mtype in entry["expected"]:
                                entry["response"] = msg
                                entry["event"].set()
                                break
        finally:
            try:
                s.close()
            except Exception:
                pass


_SESSIONS: dict[str, Session] = {}
_SESS_LOCK = threading.Lock()

_EXPECTED_BY_REQUEST = {
    "AUTH_LOGIN": {"AUTH_OK", "AUTH_FAIL"},
    "AUTH_REGISTER": {"AUTH_OK", "AUTH_FAIL"},
    "FRIEND_REQUEST": {"FRIEND_REQUEST_SENT", "ERROR"},
    "FRIEND_ACCEPT": {"FRIEND_ACCEPTED", "ERROR"},
    "FRIEND_LIST": {"FRIEND_LIST_RESULT", "ERROR"},
    "FRIEND_REMOVE": {"FRIEND_REMOVED", "ERROR"},
    "GROUP_CREATE": {"GROUP_CREATED", "ERROR"},
    "GROUP_ADD": {"GROUP_LIST_RESULT", "ERROR"},
    "GROUP_ACCEPT_INVITATION": {"GROUP_ACCEPTED", "ERROR"},
    "GROUP_REJECT_INVITATION": {"GROUP_REJECTED", "ERROR"},
    "GROUP_LIST": {"GROUP_LIST_RESULT", "ERROR"},
    "MSG_HISTORY": {"MSG_HISTORY_RESULT", "ERROR"},
    "GROUP_HISTORY": {"GROUP_HISTORY_RESULT", "ERROR"},
    "MSG_SEND": {"MSG_RECV", "ERROR"},
    "GROUP_MSG_SEND": {"GROUP_MSG_RECV", "ERROR"},
    "MSG_RECALL": {"MSG_RECALL_UPDATE", "ERROR"},
    "MSG_REACT": {"MSG_REACT_UPDATE", "ERROR"},
}


def get_session(sid: str) -> Session:
    with _SESS_LOCK:
        sess = _SESSIONS.get(sid)
        if sess is None:
            sess = Session()
            _SESSIONS[sid] = sess
        return sess


class Handler(SimpleHTTPRequestHandler):
    def _send_json(self, code: int, obj):
        payload = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _serve_static(self):
        web_root = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web")
        rel = self.path.lstrip("/") or "index.html"
        fs_path = os.path.normpath(os.path.join(web_root, rel))
        if not fs_path.startswith(web_root):
            self.send_error(403)
            return
        if not os.path.isfile(fs_path):
            self.send_error(404)
            return
        ctype = (
            "text/html" if fs_path.endswith(".html") else
            "text/css" if fs_path.endswith(".css") else
            "application/javascript" if fs_path.endswith(".js") else
            "application/octet-stream"
        )
        with open(fs_path, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/poll":
            qs = parse_qs(parsed.query)
            sid = (qs.get("sid") or [None])[0] or str(uuid.uuid4())
            sess = get_session(sid)
            sess.ensure_sock()
            with sess.queue_lock:
                items = list(sess.queue)
                sess.queue.clear()
            # include sid in response headers for debugging
            self._send_json(200, {"sid": sid, "messages": items})
            return
        self._serve_static()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/send":
            qs = parse_qs(parsed.query)
            sid = (qs.get("sid") or [None])[0] or str(uuid.uuid4())
            sess = get_session(sid)
            sess.ensure_sock()
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length) if length > 0 else b"{}"
            try:
                obj = json.loads(body.decode())
            except Exception:
                self._send_json(400, {"error": "bad_json"})
                return
            try:
                response = self._send_and_wait_response(sess, obj)
                # include sid for debugging
                if isinstance(response, dict):
                    response.setdefault("meta", {})
                    response["meta"]["sid"] = sid
                self._send_json(200, response)
            except Exception as e:
                self._send_json(500, {"error": "request_failed", "detail": str(e)})
            return
        self.send_error(404)

    def _send_and_wait_response(self, sess: Session, request: dict):
        expected = _EXPECTED_BY_REQUEST.get(request.get("type"), {"ERROR"})
        entry = {"expected": expected, "response": None, "event": threading.Event()}
        with sess.pending_lock:
            sess.pending.append(entry)
        try:
            line = (json.dumps(request) + "\n").encode()
            with sess.lock:
                assert sess.sock is not None
                sess.sock.sendall(line)
            if entry["event"].wait(timeout=5.0):
                return entry["response"] or {"type": "ERROR", "data": {"code": "EMPTY"}}
            raise Exception("Request timeout")
        finally:
            with sess.pending_lock:
                if entry in sess.pending:
                    sess.pending.remove(entry)


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print(f"HTTP gateway listening on http://{HOST}:{PORT} (proxy -> {MOCK_HOST}:{MOCK_PORT})")
    httpd = HTTPServer((HOST, PORT), Handler)
    try:
        httpd.serve_forever()
    finally:
        try:
            httpd.server_close()
        except Exception:
            pass


if __name__ == "__main__":
    main()


