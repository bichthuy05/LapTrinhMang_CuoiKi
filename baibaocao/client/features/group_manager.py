# client/features/group_manager.py
from typing import Callable, Optional, Dict, Any
from client.network.socket_client import SocketClient
from client.utils.helpers import new_request_id


class GroupManager:
    """
    API phía client cho chat nhóm.
    Gói tin gửi:
      - GROUP_CREATE{name, avatar?}
      - GROUP_ADD{group_id, user_id}  (giờ là gửi lời mời)
      - GROUP_LIST{}
      - GROUP_INVITE_LIST{}
      - GROUP_INVITE_ACCEPT{invite_id}
      - GROUP_INVITE_DECLINE{invite_id}
      - GROUP_MSG_SEND{group_id, content, reply_to_id?}
      - GROUP_HISTORY{group_id, before_id?, limit}

    Server phản hồi / fanout:
      - GROUP_CREATED{group_id, name}
      - GROUP_LIST_RESULT{groups:[{group_id,name,member_count}]}
      - GROUP_INVITE_SENT{invite_id, group_id, to_user_id}
      - GROUP_INVITE_INCOMING{invite_id, group_id, group_name, from_user_id, from_username}
      - GROUP_INVITE_LIST_RESULT{incoming:[], outgoing:[]}
      - GROUP_INVITE_ACCEPTED{invite_id, group_id, user_id}
      - GROUP_INVITE_DECLINED{invite_id, group_id, user_id}
      - GROUP_MSG_RECV{message_id, group_id, from_user_id, content, created_at, reply_to_id?}
      - GROUP_HISTORY_RESULT{group_id, messages:[...], has_more:bool}
    """

    def __init__(
        self,
        sock: SocketClient,
        on_event: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ):
        self.sock = sock
        self.on_event = on_event or (lambda ev, data: None)

    # ---- senders ----
    def create(self, name: str, avatar: str | None = None):
        self.sock.send_json({
            "type": "GROUP_CREATE",
            "data": {"name": name, "avatar": avatar},
            "request_id": new_request_id()
        })

    def add_member(self, group_id: int, user_id: int):
        self.sock.send_json({
            "type": "GROUP_ADD",
            "data": {"group_id": group_id, "user_id": user_id},
            "request_id": new_request_id()
        })

    def list(self):
        self.sock.send_json({
            "type": "GROUP_LIST",
            "data": {},
            "request_id": new_request_id()
        })

    def invite_list(self):
        self.sock.send_json({
            "type": "GROUP_INVITE_LIST",
            "data": {},
            "request_id": new_request_id()
        })

    def invite_accept(self, invite_id: int):
        self.sock.send_json({
            "type": "GROUP_INVITE_ACCEPT",
            "data": {"invite_id": invite_id},
            "request_id": new_request_id()
        })

    def invite_decline(self, invite_id: int):
        self.sock.send_json({
            "type": "GROUP_INVITE_DECLINE",
            "data": {"invite_id": invite_id},
            "request_id": new_request_id()
        })

    def send_text(self, group_id: int, content: str, reply_to_id: int | None = None):
        self.sock.send_json({
            "type": "GROUP_MSG_SEND",
            "data": {"group_id": group_id, "content": content, "reply_to_id": reply_to_id},
            "request_id": new_request_id()
        })

    def get_history(self, group_id: int, before_id: int | None = None, limit: int = 50):
        self.sock.send_json({
            "type": "GROUP_HISTORY",
            "data": {"group_id": group_id, "before_id": before_id, "limit": limit},
            "request_id": new_request_id()
        })

    # ---- handlers ----
    def on_created(self, msg: dict):
        self.on_event("GROUP_CREATED", msg.get("data") or {})

    def on_list_result(self, msg: dict):
        self.on_event("GROUP_LIST_RESULT", msg.get("data") or {})

    # ---- invite handlers ----
    def on_invite_sent(self, msg: dict):
        self.on_event("GROUP_INVITE_SENT", msg.get("data") or {})

    def on_invite_incoming(self, msg: dict):
        self.on_event("GROUP_INVITE_INCOMING", msg.get("data") or {})

    def on_invite_list_result(self, msg: dict):
        self.on_event("GROUP_INVITE_LIST_RESULT", msg.get("data") or {})

    def on_invite_accepted(self, msg: dict):
        self.on_event("GROUP_INVITE_ACCEPTED", msg.get("data") or {})

    def on_invite_declined(self, msg: dict):
        self.on_event("GROUP_INVITE_DECLINED", msg.get("data") or {})

    def on_msg_recv(self, msg: dict):
        self.on_event("GROUP_MSG_RECV", msg.get("data") or {})

    def on_history_result(self, msg: dict):
        self.on_event("GROUP_HISTORY_RESULT", msg.get("data") or {})
