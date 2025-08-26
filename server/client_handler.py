import threading, json, socket
from shared.protocol import parse_request, build_response, dumps_line, loads_line
from server.services.auth_service import AuthService
from server.services.message_service import MessageService
from server.services.friend_service import FriendService
from server.services.group_service import GroupService
from server.utils.logger import get_logger

logger = get_logger("server")

# Online user registry: username -> (socket, file-like writer, thread id)
ONLINE = {}
ONLINE_LOCK = threading.Lock()

auth_service = AuthService()
message_service = MessageService()
friend_service = FriendService()
group_service = GroupService()

def _send_to(writer, obj: dict):
    try:
        writer.write(dumps_line(obj))
        writer.flush()
        return True
    except Exception as e:
        logger.error(f"send_to failed: {e}")
        return False

def _push_to_user(username: str, obj: dict):
    with ONLINE_LOCK:
        entry = ONLINE.get(username)
    if not entry:
        return False
    _, writer, _ = entry
    return _send_to(writer, obj)

def handle_client(sock: socket.socket, addr: tuple):
    logger.info(f"Client thread started for {addr}")
    user = None
    f = sock.makefile('rwb')
    try:
        while True:
            line = f.readline()
            if not line:
                break
            try:
                req = loads_line(line)
                action, payload = parse_request(req)
            except Exception as e:
                logger.error(f"Invalid JSON from {addr}: {e}")
                resp = build_response(False, "invalid", None, "Invalid JSON")
                _send_to(f, resp)
                continue

            ok, data = False, {"message": "unknown action"}
            if action == "register":
                ok, data = auth_service.register(payload)
            elif action == "login":
                ok, data = auth_service.login(payload)
                if ok:
                    user = data["user"]["username"]
                    with ONLINE_LOCK:
                        ONLINE[user] = (sock, f, threading.current_thread().name)
            elif action == "send_message":
                ok, data = message_service.send_message(payload)
                if ok:
                    # push to receiver if online
                    msg = data["message"]
                    push = build_response(True, "incoming_message", msg, None)
                    _push_to_user(msg["receiver"], push)
            elif action == "add_friend":
                ok, data = friend_service.add_friend(payload)
            elif action == "create_group":
                ok, data = group_service.create_group(payload)
            else:
                ok, data = False, {"message": "Unknown action"}

            resp = build_response(ok, action, data if ok else None, None if ok else data.get("message"))
            _send_to(f, resp)
    except Exception as e:
        logger.error(f"Handler error for {addr}: {e}")
    finally:
        if user:
            with ONLINE_LOCK:
                ONLINE.pop(user, None)
        try:
            f.close()
        except Exception:
            pass
        try:
            sock.close()
        except Exception:
            pass
        logger.info(f"Client thread ended for {addr}")
