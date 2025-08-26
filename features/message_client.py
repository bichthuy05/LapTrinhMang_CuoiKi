# client/features/message_client.py
from typing import Optional, Callable, Dict, Any, List
from client.network.socket_client import SocketClient
from client.utils.helpers import new_request_id

class MessageClient:
    """
    Gửi/nhận 1-1 + lịch sử + Seen/Recall/React/Reply.
    Handlers public (đăng ký với ProtocolHandler):
      - handle_msg_recv
      - handle_history_result
      - handle_seen_update
      - handle_recall_update
      - handle_react_update
    Đồng thời có alias on_msg_recv / on_history_result để tương thích bản cũ.
    """

    def __init__(
        self,
        sock: SocketClient,
        on_recv: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_history: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_seen_update: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_recall_update: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_react_update: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        self.sock = sock
        # callback nội bộ (không đụng tên method)
        self._cb_recv = on_recv or (lambda m: None)
        self._cb_history = on_history or (lambda m: None)
        self._cb_seen = on_seen_update or (lambda m: None)
        self._cb_recall = on_recall_update or (lambda m: None)
        self._cb_react = on_react_update or (lambda m: None)

    # ----------------- senders -----------------
    def send_text(self, to_user_id: int, content: str, reply_to_id: Optional[int] = None):
        self.sock.send_json({
            "type": "MSG_SEND",
            "data": {"to_user_id": to_user_id, "content": content, "reply_to_id": reply_to_id},
            "request_id": new_request_id()
        })

    def get_history(self, peer_id: int, before_id: Optional[int] = None, limit: int = 50):
        self.sock.send_json({
            "type": "MSG_HISTORY",
            "data": {"peer_id": peer_id, "before_id": before_id, "limit": limit},
            "request_id": new_request_id()
        })

    def mark_seen(self, message_ids: List[int]):
        self.sock.send_json({
            "type": "MSG_SEEN",
            "data": {"message_ids": message_ids},
            "request_id": new_request_id()
        })

    def recall(self, message_id: int):
        self.sock.send_json({
            "type": "MSG_RECALL",
            "data": {"message_id": message_id},
            "request_id": new_request_id()
        })

    def react(self, message_id: int, reaction: str):
        self.sock.send_json({
            "type": "MSG_REACT",
            "data": {"message_id": message_id, "reaction": reaction},
            "request_id": new_request_id()
        })

    # ----------------- handlers cho ProtocolHandler -----------------
    def handle_msg_recv(self, msg: dict):
        self._cb_recv(msg.get("data") or {})

    def handle_history_result(self, msg: dict):
        self._cb_history(msg.get("data") or {})

    def handle_seen_update(self, msg: dict):
        self._cb_seen(msg.get("data") or {})

    def handle_recall_update(self, msg: dict):
        self._cb_recall(msg.get("data") or {})

    def handle_react_update(self, msg: dict):
        self._cb_react(msg.get("data") or {})

    # ----------------- alias tương thích bản cũ -----------------
    def on_msg_recv(self, msg: dict):
        self.handle_msg_recv(msg)

    def on_history_result(self, msg: dict):
        self.handle_history_result(msg)
