
from client.network.socket_client import SocketClient


class DummySock:
    def __init__(self):
        self.sent = b""

    def sendall(self, data: bytes):
        self.sent += data

    def shutdown(self, how):
        pass

    def close(self):
        pass


def test_send_json_appends_newline(monkeypatch):
    c = SocketClient(host="127.0.0.1", port=65535)
    # gắn socket giả mạo
    c._sock = DummySock()
    c.send_json({"type": "PING", "data": {}, "request_id": "t"})
    assert c._sock.sent.endswith(b"\n"), c._sock.sent
