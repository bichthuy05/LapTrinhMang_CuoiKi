# client/features/notification_manager.py
from collections import defaultdict
from typing import Optional, Callable, Dict, Any

class NotificationManager:
    """
    Đếm badge chưa đọc cho peer và group.
    - call on_incoming_msg(data) khi nhận MSG_RECV / GROUP_MSG_RECV
    - call mark_seen(ids) sau khi gửi MSG_SEEN
    - set_active_peer(peer_id) / set_active_group(group_id) để auto clear khi xem.
    """
    def __init__(self, emit: Optional[Callable[[str, Dict[str, Any]], None]] = None):
        self.emit = emit or (lambda ev, data: None)
        self.unread_peer = defaultdict(int)   # peer_id -> count
        self.unread_group = defaultdict(int)  # group_id -> count
        self.active_peer: Optional[int] = None
        self.active_group: Optional[int] = None

    def set_active_peer(self, peer_id: Optional[int]):
        self.active_peer = peer_id
        if peer_id is not None:
            self.unread_peer[peer_id] = 0
            self.emit("UNREAD_PEER", {"peer_id": peer_id, "count": 0})

    def set_active_group(self, group_id: Optional[int]):
        self.active_group = group_id
        if group_id is not None:
            self.unread_group[group_id] = 0
            self.emit("UNREAD_GROUP", {"group_id": group_id, "count": 0})

    def on_incoming_msg(self, data: Dict[str, Any]):
        if "group_id" in data:
            gid = data["group_id"]
            if gid != self.active_group:
                self.unread_group[gid] += 1
                self.emit("UNREAD_GROUP", {"group_id": gid, "count": self.unread_group[gid]})
        else:
            peer = data["from_user_id"] if self.active_peer != data.get("from_user_id") else None
            # Nếu đang xem đúng peer thì không tăng
            target_peer = data["from_user_id"]
            if target_peer != self.active_peer:
                self.unread_peer[target_peer] += 1
                self.emit("UNREAD_PEER", {"peer_id": target_peer, "count": self.unread_peer[target_peer]})

    def mark_seen(self, message_ids: list[int]):
        # Tuỳ nhu cầu: có thể reset theo current peer/group; ở đây emit tổng quát
        self.emit("SEEN_SENT", {"message_ids": message_ids})
