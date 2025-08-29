# tools/mock_server.py
import socket, threading, json, hashlib, time

HOST, PORT = "127.0.0.1", 5555

# users
_users = {}         # username -> {"password_hash":..., "user_id":...}
_user_conns = {}    # user_id -> socket
_next_uid = 1
_lock = threading.Lock()

# messages (share for 1-1 and group)
# record 1-1: {"id", "from_user_id", "to_user_id", "content", "created_at", "reply_to_id", "recalled", "seen_by": set(), "reactions": {emoji: set(uids)}}
# record group: {"id", "group_id", "from_user_id", "content", "created_at", "reply_to_id", "recalled", "seen_by": set(), "reactions": {...}}
_messages = []
_next_msg_id = 1
_msg_lock = threading.Lock()

# friends
_friendships = {}       # user_id -> set(friend_user_id)
_friend_requests = []   # list[{id, from_user_id, to_user_id, status}]
_next_req_id = 1
_req_lock = threading.Lock()

# blocks
_blocked = set()        # set of tuples (blocker_id, blocked_id)
_blk_lock = threading.Lock()

# groups
_groups = {}            # group_id -> {"name": str, "owner_id": int, "avatar": str|None}
_group_members = {}     # group_id -> set(user_id)
_next_gid = 1
_grp_lock = threading.Lock()


def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def _send(conn, obj: dict):
    try:
        conn.sendall((json.dumps(obj) + "\n").encode())
    except Exception:
        pass

def _broadcast_to_user(user_id: int, obj: dict):
    conn = _user_conns.get(user_id)
    if conn:
        _send(conn, obj)

def _username_of(uid: int) -> str:
    for uname, rec in _users.items():
        if rec["user_id"] == uid:
            return uname
    return f"user_{uid}"

def _group_member_count(gid: int) -> int:
    return len(_group_members.get(gid, set()))

def _find_msg(mid: int):
    for m in _messages:
        if m["id"] == mid:
            return m
    return None

def _reactions_summary(rec):
    return {k: len(v) for k, v in rec.get("reactions", {}).items()}


def _route(conn, session: dict, msg: dict):
    global _next_uid, _next_msg_id, _next_req_id, _next_gid
    typ = msg.get("type")
    data = msg.get("data") or {}

    # ---- ping ----
    if typ == "PING":
        _send(conn, {"type": "PONG", "data": {}})
        return

    # ---- auth ----
    if typ == "AUTH_REGISTER":
        u, p = data.get("username"), data.get("password")
        if not u or not p:
            _send(conn, {"type": "AUTH_FAIL", "data": {"reason": "missing_fields"}}); return
        with _lock:
            if u in _users:
                _send(conn, {"type": "AUTH_FAIL", "data": {"reason": "user_exists"}}); return
            _users[u] = {"password_hash": _hash(p), "user_id": _next_uid}
            _friendships[_next_uid] = set()
            _next_uid += 1
        uid = _users[u]["user_id"]
        _send(conn, {"type": "AUTH_OK", "data": {"username": u, "user_id": uid}})
        return

    if typ == "AUTH_LOGIN":
        u, p = data.get("username"), data.get("password")
        rec = _users.get(u)
        if not rec or rec["password_hash"] != _hash(p):
            _send(conn, {"type": "AUTH_FAIL", "data": {"reason": "invalid_credentials"}}); return
        session["user_id"] = rec["user_id"]; session["username"] = u
        _user_conns[rec["user_id"]] = conn
        _send(conn, {"type": "AUTH_OK", "data": {"username": u, "user_id": rec["user_id"]}})
        return

    # ---- guard ----
    if not session.get("user_id"):
        _send(conn, {"type": "ERROR", "data": {"code": "UNAUTH"}})
        return
    me = session["user_id"]

    # ---- friends ----
    if typ == "FRIEND_REQUEST":
        to_uid = data.get("to_user_id")
        if not isinstance(to_uid, int) or to_uid == me:
            _send(conn, {"type": "ERROR", "data": {"code": "BAD_FRIEND_REQUEST"}}); return
        with _req_lock:
            req_id = _next_req_id; _next_req_id += 1
            _friend_requests.append({"id": req_id, "from_user_id": me, "to_user_id": to_uid, "status": "pending"})
        _send(conn, {"type": "FRIEND_REQUEST_SENT", "data": {"request_id": req_id, "to_user_id": to_uid}})
        _broadcast_to_user(to_uid, {"type": "FRIEND_REQUEST_INCOMING",
                                    "data": {"request_id": req_id, "from_user_id": me,
                                             "from_username": _username_of(me)}})
        return

    if typ == "FRIEND_ACCEPT":
        req_id = data.get("request_id")
        with _req_lock:
            req = next((r for r in _friend_requests if r["id"] == req_id), None)
            if not req or req["to_user_id"] != me or req["status"] != "pending":
                _send(conn, {"type": "ERROR", "data": {"code": "BAD_FRIEND_ACCEPT"}}); return
            req["status"] = "accepted"
        a, b = req["from_user_id"], req["to_user_id"]
        _friendships.setdefault(a, set()).add(b)
        _friendships.setdefault(b, set()).add(a)
        payload = {"type": "FRIEND_ACCEPTED", "data": {"user_id1": a, "user_id2": b}}
        _send(conn, payload)
        _broadcast_to_user(a, payload)
        return

    if typ == "FRIEND_LIST":
        friends = [{"user_id": uid, "username": _username_of(uid), "status": "accepted"}
                   for uid in sorted(_friendships.get(me, set()))]
        with _req_lock:
            pending_in = [{"request_id": r["id"], "from_user_id": r["from_user_id"],
                           "from_username": _username_of(r["from_user_id"])}
                          for r in _friend_requests if r["to_user_id"] == me and r["status"] == "pending"]
            pending_out = [{"request_id": r["id"], "to_user_id": r["to_user_id"],
                            "to_username": _username_of(r["to_user_id"])}
                           for r in _friend_requests if r["from_user_id"] == me and r["status"] == "pending"]
        _send(conn, {"type": "FRIEND_LIST_RESULT",
                     "data": {"friends": friends, "pending_in": pending_in, "pending_out": pending_out}})
        return

    if typ == "FRIEND_BLOCK":
        uid = data.get("user_id")
        if not isinstance(uid, int) or uid == me:
            _send(conn, {"type": "ERROR", "data": {"code": "BAD_BLOCK"}}); return
        with _blk_lock:
            _blocked.add((me, uid))
        _send(conn, {"type": "FRIEND_BLOCKED", "data": {"user_id": uid}})
        return

    if typ == "FRIEND_UNBLOCK":
        uid = data.get("user_id")
        with _blk_lock:
            _blocked.discard((me, uid))
        _send(conn, {"type": "FRIEND_UNBLOCKED", "data": {"user_id": uid}})
        return

    # ---- messaging 1-1 ----
    if typ == "MSG_SEND":
        to_uid = data.get("to_user_id")
        content = (data.get("content") or "").strip()
        reply_to_id = data.get("reply_to_id")
        if not to_uid or not content:
            _send(conn, {"type": "ERROR", "data": {"code": "BAD_MSG"}}); return
        with _blk_lock:
            if (to_uid, me) in _blocked:   # người nhận đã block người gửi
                _send(conn, {"type": "ERROR", "data": {"code": "BLOCKED_BY_PEER"}}); return
        with _msg_lock:
            mid = _next_msg_id; _next_msg_id += 1
            rec = {"id": mid, "from_user_id": me, "to_user_id": to_uid,
                   "content": content, "created_at": time.time(), "reply_to_id": reply_to_id,
                   "recalled": False, "seen_by": set(), "reactions": {}}
            _messages.append(rec)
        payload = {"type": "MSG_RECV",
                   "data": {"message_id": rec["id"], "from_user_id": me, "to_user_id": to_uid,
                            "content": content, "created_at": rec["created_at"], "reply_to_id": reply_to_id,
                            "recalled": False, "reactions_summary": {}}}
        _send(conn, payload)
        _broadcast_to_user(to_uid, payload)
        return

    if typ == "MSG_HISTORY":
        peer_id = data.get("peer_id"); before_id = data.get("before_id"); limit = int(data.get("limit") or 50)
        with _msg_lock:
            conv = [m for m in _messages if ("group_id" not in m) and
                   ((m["from_user_id"] == me and m["to_user_id"] == peer_id) or
                    (m["from_user_id"] == peer_id and m["to_user_id"] == me))]
            conv.sort(key=lambda x: x["id"], reverse=True)
            if before_id:
                conv = [m for m in conv if m["id"] < before_id]
            batch = conv[:limit]; has_more = len(conv) > limit
            batch_sorted = sorted(batch, key=lambda x: x["id"])
            res = {"peer_id": peer_id,
                   "messages": [{"message_id": m["id"], "from_user_id": m["from_user_id"], "to_user_id": m["to_user_id"],
                                 "content": m["content"], "created_at": m["created_at"], "reply_to_id": m.get("reply_to_id"),
                                 "recalled": m.get("recalled", False), "reactions_summary": _reactions_summary(m)}
                                for m in batch_sorted],
                   "has_more": has_more}
        _send(conn, {"type": "MSG_HISTORY_RESULT", "data": res})
        return

    # ---- groups ----
    if typ == "GROUP_CREATE":
        name = (data.get("name") or "").strip()
        avatar = data.get("avatar")
        if not name:
            _send(conn, {"type": "ERROR", "data": {"code": "BAD_GROUP_NAME"}}); return
        with _grp_lock:
            gid = _next_gid; _next_gid += 1
            _groups[gid] = {"name": name, "owner_id": me, "avatar": avatar}
            _group_members[gid] = {me}
        _send(conn, {"type": "GROUP_CREATED", "data": {"group_id": gid, "name": name}})
        return

    if typ == "GROUP_ADD":
        gid = data.get("group_id"); uid = data.get("user_id")
        info = _groups.get(gid)
        if not info or info["owner_id"] != me or not isinstance(uid, int):
            _send(conn, {"type": "ERROR", "data": {"code": "BAD_GROUP_ADD"}}); return
        with _grp_lock:
            _group_members.setdefault(gid, set()).add(uid)
        mine = [{"group_id": k, "name": v["name"], "member_count": len(_group_members.get(k, set()))}
                for k, v in _groups.items() if me in _group_members.get(k, set())]
        _send(conn, {"type": "GROUP_LIST_RESULT", "data": {"groups": mine}})
        return

    if typ == "GROUP_LIST":
        mine = [{"group_id": gid, "name": g["name"], "member_count": len(_group_members.get(gid, set()))}
                for gid, g in _groups.items() if me in _group_members.get(gid, set())]
        _send(conn, {"type": "GROUP_LIST_RESULT", "data": {"groups": mine}})
        return

    if typ == "GROUP_MSG_SEND":
        gid = data.get("group_id"); content = (data.get("content") or "").strip()
        reply_to_id = data.get("reply_to_id")
        if not isinstance(gid, int) or not content:
            _send(conn, {"type": "ERROR", "data": {"code": "BAD_GROUP_MSG"}}); return
        if me not in _group_members.get(gid, set()):
            _send(conn, {"type": "ERROR", "data": {"code": "NOT_GROUP_MEMBER"}}); return
        with _msg_lock:
            mid = _next_msg_id; _next_msg_id += 1
            rec = {"id": mid, "group_id": gid, "from_user_id": me,
                   "content": content, "created_at": time.time(), "reply_to_id": reply_to_id,
                   "recalled": False, "seen_by": set(), "reactions": {}}
            _messages.append(rec)
        payload = {"type": "GROUP_MSG_RECV",
                   "data": {"message_id": rec["id"], "group_id": gid, "from_user_id": me,
                            "content": content, "created_at": rec["created_at"], "reply_to_id": reply_to_id,
                            "recalled": False, "reactions_summary": {}}}
        for uid in list(_group_members.get(gid, set())):
            _broadcast_to_user(uid, payload)
        return

    if typ == "GROUP_HISTORY":
        gid = data.get("group_id"); before_id = data.get("before_id"); limit = int(data.get("limit") or 50)
        if me not in _group_members.get(gid, set()):
            _send(conn, {"type": "ERROR", "data": {"code": "NOT_GROUP_MEMBER"}}); return
        with _msg_lock:
            conv = [m for m in _messages if m.get("group_id") == gid]
            conv.sort(key=lambda x: x["id"], reverse=True)
            if before_id:
                conv = [m for m in conv if m["id"] < before_id]
            batch = conv[:limit]; has_more = len(conv) > limit
            batch_sorted = sorted(batch, key=lambda x: x["id"])
            res = {"group_id": gid,
                   "messages": [{"message_id": m["id"], "group_id": gid, "from_user_id": m["from_user_id"],
                                 "content": m["content"], "created_at": m["created_at"], "reply_to_id": m.get("reply_to_id"),
                                 "recalled": m.get("recalled", False), "reactions_summary": _reactions_summary(m)}
                                for m in batch_sorted],
                   "has_more": has_more}
        _send(conn, {"type": "GROUP_HISTORY_RESULT", "data": res})
        return

    # ---- interactions (seen / recall / react) ----
    if typ == "MSG_SEEN":
        ids = data.get("message_ids") or []
        updated = []
        with _msg_lock:
            for mid in ids:
                rec = _find_msg(mid)
                if not rec:
                    continue
                rec.setdefault("seen_by", set()).add(me)
                updated.append(mid)
        if not updated:
            return
        # xác định phạm vi để broadcast
        payload = {"type": "MSG_SEEN_UPDATE", "data": {"message_ids": updated, "by_user_id": me}}
        # 1-1
        peers = set()
        groups = set()
        with _msg_lock:
            for mid in updated:
                rec = _find_msg(mid)
                if not rec:
                    continue
                if "group_id" in rec:
                    groups.add(rec["group_id"])
                else:
                    other = rec["to_user_id"] if rec["from_user_id"] == me else rec["from_user_id"]
                    peers.add(other)
        # gửi cho participants
        _send(conn, payload)  # gửi lại cho chính mình (optional)
        for p in peers:
            _broadcast_to_user(p, payload | {"data": payload["data"] | {"peer_id": p}})
        for g in groups:
            members = list(_group_members.get(g, set()))
            for uid in members:
                _broadcast_to_user(uid, payload | {"data": payload["data"] | {"group_id": g}})
        return

    if typ == "MSG_RECALL":
        mid = data.get("message_id")
        with _msg_lock:
            rec = _find_msg(mid)
            if not rec or rec.get("recalled"):
                _send(conn, {"type": "ERROR", "data": {"code": "BAD_RECALL"}}); return
            if rec["from_user_id"] != me:
                _send(conn, {"type": "ERROR", "data": {"code": "NOT_OWNER"}}); return
            rec["recalled"] = True
            rec["content"] = ""  # xoá nội dung hiển thị
        payload = {"type": "MSG_RECALL_UPDATE", "data": {"message_id": mid}}
        # broadcast cho participants
        if "group_id" in rec:
            for uid in list(_group_members.get(rec["group_id"], set())):
                _broadcast_to_user(uid, payload)
        else:
            _send(conn, payload)
            _broadcast_to_user(rec["to_user_id"], payload)
        return

    if typ == "MSG_REACT":
        mid = data.get("message_id"); reaction = (data.get("reaction") or "").strip()
        if not reaction:
            _send(conn, {"type": "ERROR", "data": {"code": "BAD_REACTION"}}); return
        with _msg_lock:
            rec = _find_msg(mid)
            if not rec:
                _send(conn, {"type": "ERROR", "data": {"code": "MSG_NOT_FOUND"}}); return
            rec.setdefault("reactions", {})
            rec["reactions"].setdefault(reaction, set())
            if me in rec["reactions"][reaction]:
                rec["reactions"][reaction].remove(me)
                action = "remove"
            else:
                rec["reactions"][reaction].add(me)
                action = "add"
            counts = _reactions_summary(rec)
        payload = {"type": "MSG_REACT_UPDATE",
                   "data": {"message_id": mid, "reaction": reaction, "action": action, "by_user_id": me, "counts": counts}}
        # broadcast
        if "group_id" in rec:
            for uid in list(_group_members.get(rec["group_id"], set())):
                _broadcast_to_user(uid, payload)
        else:
            _send(conn, payload)
            other = rec["to_user_id"] if rec["from_user_id"] == me else rec["from_user_id"]
            _broadcast_to_user(other, payload)
        return

    _send(conn, {"type": "ERROR", "data": {"code": "UNKNOWN_TYPE", "got": typ}})


def handle(conn):
    buf = b""; session = {}
    try:
        while True:
            data = conn.recv(4096)
            if not data: break
            buf += data
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                if not line: continue
                try:
                    msg = json.loads(line.decode())
                except json.JSONDecodeError:
                    _send(conn, {"type": "ERROR", "data": {"code": "BAD_JSON"}}); continue
                _route(conn, session, msg)
    finally:
        uid = session.get("user_id")
        if uid and _user_conns.get(uid) is conn:
            _user_conns.pop(uid, None)
        try: conn.close()
        except Exception: pass


def main():
    with socket.create_server((HOST, PORT)) as s:
        print(f"Mock server listening on {HOST}:{PORT}")
        while True:
            conn, _ = s.accept()
            threading.Thread(target=handle, args=(conn,), daemon=True).start()


if __name__ == "__main__":
    main()
