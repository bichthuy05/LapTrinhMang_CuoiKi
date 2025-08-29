# client/features/friend_manager.py
from typing import Callable, Optional, Dict, Any
from client.network.socket_client import SocketClient
from client.utils.helpers import new_request_id


class FriendManager:
    """
    API phía client cho hệ thống bạn bè.
    Gói tin:
      - FRIEND_REQUEST{to_user_id}
      - FRIEND_ACCEPT{request_id}
      - FRIEND_LIST{}
      - FRIEND_BLOCK{user_id}
      - FRIEND_UNBLOCK{user_id}

    Server phản hồi / fanout:
      - FRIEND_REQUEST_SENT{request_id, to_user_id}
      - FRIEND_REQUEST_INCOMING{request_id, from_user_id, from_username}
      - FRIEND_ACCEPTED{user_id1, user_id2}
      - FRIEND_LIST_RESULT{friends: [ {user_id, username, status} ], pending_in:[], pending_out:[]}
      - FRIEND_BLOCKED{user_id}
      - FRIEND_UNBLOCKED{user_id}
    """

    def __init__(
        self,
        sock: SocketClient,
        on_event: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ):
        self.sock = sock
        self.on_event = on_event or (lambda ev, data: None)

    # ---- senders ----
    def send_request(self, to_user_id: int):
        self.sock.send_json({
            "type": "FRIEND_REQUEST",
            "data": {"to_user_id": to_user_id},
            "request_id": new_request_id()
        })

    def accept(self, request_id: int):
        self.sock.send_json({
            "type": "FRIEND_ACCEPT",
            "data": {"request_id": request_id},
            "request_id": new_request_id()
        })

    def list(self):
        self.sock.send_json({
            "type": "FRIEND_LIST",
            "data": {},
            "request_id": new_request_id()
        })

    def block(self, user_id: int):
        self.sock.send_json({
            "type": "FRIEND_BLOCK",
            "data": {"user_id": user_id},
            "request_id": new_request_id()
        })

    def unblock(self, user_id: int):
        self.sock.send_json({
            "type": "FRIEND_UNBLOCK",
            "data": {"user_id": user_id},
            "request_id": new_request_id()
        })

    # ---- handlers (đăng ký trong ProtocolHandler) ----
    def on_request_sent(self, msg: dict):
        self.on_event("FRIEND_REQUEST_SENT", msg.get("data") or {})

    def on_request_incoming(self, msg: dict):
        self.on_event("FRIEND_REQUEST_INCOMING", msg.get("data") or {})

    def on_accepted(self, msg: dict):
        self.on_event("FRIEND_ACCEPTED", msg.get("data") or {})

    def on_list_result(self, msg: dict):
        self.on_event("FRIEND_LIST_RESULT", msg.get("data") or {})

    def on_blocked(self, msg: dict):
        self.on_event("FRIEND_BLOCKED", msg.get("data") or {})

    def on_unblocked(self, msg: dict):
        self.on_event("FRIEND_UNBLOCKED", msg.get("data") or {})
