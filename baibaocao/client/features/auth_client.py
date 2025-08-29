# client/features/auth_client.py
from typing import Optional, Callable
from client.network.socket_client import SocketClient
from client.utils.helpers import new_request_id

class AuthClient:
    """
    API phía client để gửi AUTH_REGISTER / AUTH_LOGIN
    và lưu phiên đăng nhập tạm (in-memory).
    """

    def __init__(self, sock: SocketClient, emit_status: Optional[Callable[[str], None]] = None):
        self.sock = sock
        self.user_id: Optional[int] = None
        self.username: Optional[str] = None
        self.emit_status = emit_status or (lambda msg: None)

    # --- gửi ---
    def register(self, username: str, password: str):
        self.sock.send_json({
            "type": "AUTH_REGISTER",
            "data": {"username": username, "password": password},
            "request_id": new_request_id()
        })

    def login(self, username: str, password: str):
        self.sock.send_json({
            "type": "AUTH_LOGIN",
            "data": {"username": username, "password": password},
            "request_id": new_request_id()
        })

    # --- nhận ---
    def on_auth_ok(self, msg: dict):
        data = msg.get("data", {})
        self.user_id = data.get("user_id")
        self.username = data.get("username")
        self.emit_status(f"Đăng nhập OK: {self.username} (id={self.user_id})")

    def on_auth_fail(self, msg: dict):
        reason = (msg.get("data") or {}).get("reason", "unknown")
        self.emit_status(f"Đăng nhập/đăng ký FAIL: {reason}")
