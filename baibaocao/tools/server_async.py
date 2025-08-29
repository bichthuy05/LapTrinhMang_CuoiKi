# tools/server_async.py
import asyncio
import json
import hashlib
import time
from typing import Dict, Set, Any


HOST, PORT = "127.0.0.1", 5555


def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


class State:
    def __init__(self) -> None:
        # users
        self.users: Dict[str, Dict[str, Any]] = {}  # username -> {password_hash, user_id}
        self.user_conns: Dict[int, asyncio.StreamWriter] = {}  # user_id -> writer
        self.next_uid: int = 1

        # messages
        self.messages: list[dict] = []
        self.next_msg_id: int = 1

        # friends
        self.friendships: Dict[int, Set[int]] = {}
        self.friend_requests: list[dict] = []  # {id, from_user_id, to_user_id, status}
        self.next_req_id: int = 1

        # blocks
        self.blocked: Set[tuple[int, int]] = set()  # (blocker_id, blocked_id)

        # groups
        self.groups: Dict[int, dict] = {}           # gid -> {name, owner_id, avatar}
        self.group_members: Dict[int, Set[int]] = {}  # gid -> set(user_id)
        self.next_gid: int = 1

    def username_of(self, uid: int) -> str:
        for uname, rec in self.users.items():
            if rec["user_id"] == uid:
                return uname
        return f"user_{uid}"

    def reactions_summary(self, rec: dict) -> Dict[str, int]:
        return {k: len(v) for k, v in rec.get("reactions", {}).items()}


STATE = State()


async def send(writer: asyncio.StreamWriter, obj: dict) -> None:
    try:
        data = (json.dumps(obj) + "\n").encode()
        writer.write(data)
        await writer.drain()
    except Exception:
        pass


async def broadcast_to_user(user_id: int, obj: dict) -> None:
    w = STATE.user_conns.get(user_id)
    if w is not None:
        await send(w, obj)


def find_msg(mid: int) -> dict | None:
    for m in STATE.messages:
        if m["id"] == mid:
            return m
    return None


async def route(session: dict, writer: asyncio.StreamWriter, msg: dict) -> None:
    typ = msg.get("type")
    data = msg.get("data") or {}

    # ping
    if typ == "PING":
        await send(writer, {"type": "PONG", "data": {}})
        return

    # auth
    if typ == "AUTH_REGISTER":
        u, p = data.get("username"), data.get("password")
        if not u or not p:
            await send(writer, {"type": "AUTH_FAIL", "data": {"reason": "missing_fields"}})
            return
        if u in STATE.users:
            await send(writer, {"type": "AUTH_FAIL", "data": {"reason": "user_exists"}})
            return
        STATE.users[u] = {"password_hash": _hash(p), "user_id": STATE.next_uid}
        STATE.friendships[STATE.next_uid] = set()
        STATE.next_uid += 1
        uid = STATE.users[u]["user_id"]
        await send(writer, {"type": "AUTH_OK", "data": {"username": u, "user_id": uid}})
        return

    if typ == "AUTH_LOGIN":
        u, p = data.get("username"), data.get("password")
        rec = STATE.users.get(u)
        if not rec or rec["password_hash"] != _hash(p):
            await send(writer, {"type": "AUTH_FAIL", "data": {"reason": "invalid_credentials"}})
            return
        session["user_id"] = rec["user_id"]
        session["username"] = u
        STATE.user_conns[rec["user_id"]] = writer
        await send(writer, {"type": "AUTH_OK", "data": {"username": u, "user_id": rec["user_id"]}})
        return

    # guard
    if not session.get("user_id"):
        await send(writer, {"type": "ERROR", "data": {"code": "UNAUTH"}})
        return
    me = session["user_id"]

    # friends
    if typ == "FRIEND_REQUEST":
        to_uid = data.get("to_user_id")
        if not isinstance(to_uid, int) or to_uid == me:
            await send(writer, {"type": "ERROR", "data": {"code": "BAD_FRIEND_REQUEST"}})
            return
        req_id = STATE.next_req_id
        STATE.next_req_id += 1
        STATE.friend_requests.append({"id": req_id, "from_user_id": me, "to_user_id": to_uid, "status": "pending"})
        await send(writer, {"type": "FRIEND_REQUEST_SENT", "data": {"request_id": req_id, "to_user_id": to_uid}})
        await broadcast_to_user(to_uid, {"type": "FRIEND_REQUEST_INCOMING",
                                         "data": {"request_id": req_id, "from_user_id": me,
                                                   "from_username": STATE.username_of(me)}})
        return

    if typ == "FRIEND_ACCEPT":
        req_id = data.get("request_id")
        req = next((r for r in STATE.friend_requests if r["id"] == req_id), None)
        if not req or req["to_user_id"] != me or req["status"] != "pending":
            await send(writer, {"type": "ERROR", "data": {"code": "BAD_FRIEND_ACCEPT"}})
            return
        req["status"] = "accepted"
        a, b = req["from_user_id"], req["to_user_id"]
        STATE.friendships.setdefault(a, set()).add(b)
        STATE.friendships.setdefault(b, set()).add(a)
        payload = {"type": "FRIEND_ACCEPTED", "data": {"user_id1": a, "user_id2": b}}
        await send(writer, payload)
        await broadcast_to_user(a, payload)
        return

    if typ == "FRIEND_REMOVE":
        uid = data.get("user_id")
        if not isinstance(uid, int) or uid == me:
            await send(writer, {"type": "ERROR", "data": {"code": "BAD_FRIEND_REMOVE"}})
            return
        # remove friendship both directions
        if me in STATE.friendships:
            STATE.friendships[me].discard(uid)
        if uid in STATE.friendships:
            STATE.friendships[uid].discard(me)
        payload = {"type": "FRIEND_REMOVED", "data": {"user_id": uid}}
        await send(writer, payload)
        await broadcast_to_user(uid, {"type": "FRIEND_REMOVED", "data": {"user_id": me}})
        return

    if typ == "FRIEND_LIST":
        friends = [{"user_id": uid, "username": STATE.username_of(uid), "status": "accepted"}
                   for uid in sorted(STATE.friendships.get(me, set()))]
        pending_in = [{"request_id": r["id"], "from_user_id": r["from_user_id"],
                       "from_username": STATE.username_of(r["from_user_id"]) }
                      for r in STATE.friend_requests if r["to_user_id"] == me and r["status"] == "pending"]
        pending_out = [{"request_id": r["id"], "to_user_id": r["to_user_id"],
                        "to_username": STATE.username_of(r["to_user_id"]) }
                       for r in STATE.friend_requests if r["from_user_id"] == me and r["status"] == "pending"]
        await send(writer, {"type": "FRIEND_LIST_RESULT",
                            "data": {"friends": friends, "pending_in": pending_in, "pending_out": pending_out}})
        return

    if typ == "FRIEND_BLOCK":
        uid = data.get("user_id")
        if not isinstance(uid, int) or uid == me:
            await send(writer, {"type": "ERROR", "data": {"code": "BAD_BLOCK"}})
            return
        STATE.blocked.add((me, uid))
        await send(writer, {"type": "FRIEND_BLOCKED", "data": {"user_id": uid}})
        return

    if typ == "FRIEND_UNBLOCK":
        uid = data.get("user_id")
        STATE.blocked.discard((me, uid))
        await send(writer, {"type": "FRIEND_UNBLOCKED", "data": {"user_id": uid}})
        return

    # 1-1 messages
    if typ == "MSG_SEND":
        to_uid = data.get("to_user_id")
        content = (data.get("content") or "").strip()
        reply_to_id = data.get("reply_to_id")
        if not to_uid or not content:
            await send(writer, {"type": "ERROR", "data": {"code": "BAD_MSG"}})
            return
        if to_uid == me:
            await send(writer, {"type": "ERROR", "data": {"code": "BAD_MSG_SELF"}})
            return
        if (to_uid, me) in STATE.blocked:
            await send(writer, {"type": "ERROR", "data": {"code": "BLOCKED_BY_PEER"}})
            return
        mid = STATE.next_msg_id
        STATE.next_msg_id += 1
        rec = {"id": mid, "from_user_id": me, "to_user_id": to_uid, "content": content,
               "created_at": time.time(), "reply_to_id": reply_to_id, "recalled": False,
               "seen_by": set(), "reactions": {}}
        STATE.messages.append(rec)
        payload = {"type": "MSG_RECV",
                   "data": {"message_id": rec["id"], "from_user_id": me, "to_user_id": to_uid,
                             "content": content, "created_at": rec["created_at"], "reply_to_id": reply_to_id,
                             "recalled": False, "reactions_summary": {}}}
        await send(writer, payload)
        await broadcast_to_user(to_uid, payload)
        return

    if typ == "MSG_HISTORY":
        peer_id = data.get("peer_id"); before_id = data.get("before_id"); limit = int(data.get("limit") or 50)
        conv = [m for m in STATE.messages if ("group_id" not in m) and
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
                              "recalled": m.get("recalled", False), "reactions_summary": STATE.reactions_summary(m)}
                             for m in batch_sorted],
               "has_more": has_more}
        await send(writer, {"type": "MSG_HISTORY_RESULT", "data": res})
        return

    # groups
    if typ == "GROUP_CREATE":
        name = (data.get("name") or "").strip(); avatar = data.get("avatar")
        if not name:
            await send(writer, {"type": "ERROR", "data": {"code": "BAD_GROUP_NAME"}})
            return
        gid = STATE.next_gid; STATE.next_gid += 1
        STATE.groups[gid] = {"name": name, "owner_id": me, "avatar": avatar}
        STATE.group_members[gid] = {me}
        await send(writer, {"type": "GROUP_CREATED", "data": {"group_id": gid, "name": name}})
        return

    if typ == "GROUP_ADD":
        gid = data.get("group_id"); uid = data.get("user_id")
        info = STATE.groups.get(gid)
        if not info or info["owner_id"] != me or not isinstance(uid, int):
            await send(writer, {"type": "ERROR", "data": {"code": "BAD_GROUP_ADD"}})
            return
        STATE.group_members.setdefault(gid, set()).add(uid)
        mine = [{"group_id": k, "name": v["name"], "member_count": len(STATE.group_members.get(k, set()))}
                for k, v in STATE.groups.items() if me in STATE.group_members.get(k, set())]
        await send(writer, {"type": "GROUP_LIST_RESULT", "data": {"groups": mine}})
        return

    if typ == "GROUP_LIST":
        mine = [{"group_id": gid, "name": g["name"], "member_count": len(STATE.group_members.get(gid, set()))}
                for gid, g in STATE.groups.items() if me in STATE.group_members.get(gid, set())]
        await send(writer, {"type": "GROUP_LIST_RESULT", "data": {"groups": mine}})
        return

    if typ == "GROUP_MSG_SEND":
        gid = data.get("group_id"); content = (data.get("content") or "").strip(); reply_to_id = data.get("reply_to_id")
        if not isinstance(gid, int) or not content:
            await send(writer, {"type": "ERROR", "data": {"code": "BAD_GROUP_MSG"}})
            return
        if me not in STATE.group_members.get(gid, set()):
            await send(writer, {"type": "ERROR", "data": {"code": "NOT_GROUP_MEMBER"}})
            return
        mid = STATE.next_msg_id; STATE.next_msg_id += 1
        rec = {"id": mid, "group_id": gid, "from_user_id": me, "content": content,
               "created_at": time.time(), "reply_to_id": reply_to_id, "recalled": False,
               "seen_by": set(), "reactions": {}}
        STATE.messages.append(rec)
        payload = {"type": "GROUP_MSG_RECV",
                   "data": {"message_id": rec["id"], "group_id": gid, "from_user_id": me,
                             "content": content, "created_at": rec["created_at"], "reply_to_id": reply_to_id,
                             "recalled": False, "reactions_summary": {}}}
        for uid in list(STATE.group_members.get(gid, set())):
            await broadcast_to_user(uid, payload)
        return

    if typ == "GROUP_HISTORY":
        gid = data.get("group_id"); before_id = data.get("before_id"); limit = int(data.get("limit") or 50)
        if me not in STATE.group_members.get(gid, set()):
            await send(writer, {"type": "ERROR", "data": {"code": "NOT_GROUP_MEMBER"}})
            return
        conv = [m for m in STATE.messages if m.get("group_id") == gid]
        conv.sort(key=lambda x: x["id"], reverse=True)
        if before_id:
            conv = [m for m in conv if m["id"] < before_id]
        batch = conv[:limit]; has_more = len(conv) > limit
        batch_sorted = sorted(batch, key=lambda x: x["id"])
        res = {"group_id": gid,
               "messages": [{"message_id": m["id"], "group_id": gid, "from_user_id": m["from_user_id"],
                              "content": m["content"], "created_at": m["created_at"], "reply_to_id": m.get("reply_to_id"),
                              "recalled": m.get("recalled", False), "reactions_summary": STATE.reactions_summary(m)}
                             for m in batch_sorted],
               "has_more": has_more}
        await send(writer, {"type": "GROUP_HISTORY_RESULT", "data": res})
        return

    # interactions
    if typ == "MSG_SEEN":
        ids = data.get("message_ids") or []
        updated: list[int] = []
        for mid in ids:
            rec = find_msg(mid)
            if not rec:
                continue
            rec.setdefault("seen_by", set()).add(me)
            updated.append(mid)
        if not updated:
            return
        payload = {"type": "MSG_SEEN_UPDATE", "data": {"message_ids": updated, "by_user_id": me}}
        peers: Set[int] = set(); groups: Set[int] = set()
        for mid in updated:
            rec = find_msg(mid)
            if not rec:
                continue
            if "group_id" in rec:
                groups.add(rec["group_id"])
            else:
                other = rec["to_user_id"] if rec["from_user_id"] == me else rec["from_user_id"]
                peers.add(other)
        await send(writer, payload)
        for p in peers:
            await broadcast_to_user(p, {"type": "MSG_SEEN_UPDATE", "data": payload["data"] | {"peer_id": p}})
        for g in groups:
            for uid in list(STATE.group_members.get(g, set())):
                await broadcast_to_user(uid, {"type": "MSG_SEEN_UPDATE", "data": payload["data"] | {"group_id": g}})
        return

    if typ == "MSG_RECALL":
        mid = data.get("message_id")
        rec = find_msg(mid)
        if not rec or rec.get("recalled"):
            await send(writer, {"type": "ERROR", "data": {"code": "BAD_RECALL"}})
            return
        if rec["from_user_id"] != me:
            await send(writer, {"type": "ERROR", "data": {"code": "NOT_OWNER"}})
            return
        rec["recalled"] = True
        rec["content"] = ""
        payload = {"type": "MSG_RECALL_UPDATE", "data": {"message_id": mid}}
        if "group_id" in rec:
            for uid in list(STATE.group_members.get(rec["group_id"], set())):
                await broadcast_to_user(uid, payload)
        else:
            await send(writer, payload)
            await broadcast_to_user(rec["to_user_id"], payload)
        return

    if typ == "MSG_REACT":
        mid = data.get("message_id"); reaction = (data.get("reaction") or "").strip()
        if not reaction:
            await send(writer, {"type": "ERROR", "data": {"code": "BAD_REACTION"}})
            return
        rec = find_msg(mid)
        if not rec:
            await send(writer, {"type": "ERROR", "data": {"code": "MSG_NOT_FOUND"}})
            return
        rec.setdefault("reactions", {})
        rec["reactions"].setdefault(reaction, set())
        if me in rec["reactions"][reaction]:
            rec["reactions"][reaction].remove(me)
            action = "remove"
        else:
            rec["reactions"][reaction].add(me)
            action = "add"
        counts = STATE.reactions_summary(rec)
        payload = {"type": "MSG_REACT_UPDATE",
                   "data": {"message_id": mid, "reaction": reaction, "action": action, "by_user_id": me, "counts": counts}}
        if "group_id" in rec:
            for uid in list(STATE.group_members.get(rec["group_id"], set())):
                await broadcast_to_user(uid, payload)
        else:
            await send(writer, payload)
            other = rec["to_user_id"] if rec["from_user_id"] == me else rec["from_user_id"]
            await broadcast_to_user(other, payload)
        return

    await send(writer, {"type": "ERROR", "data": {"code": "UNKNOWN_TYPE", "got": typ}})


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    addr = writer.get_extra_info("peername")
    session: dict = {}
    buf = b""
    try:
        while True:
            data = await reader.read(4096)
            if not data:
                break
            buf += data
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                if not line:
                    continue
                try:
                    msg = json.loads(line.decode())
                except json.JSONDecodeError:
                    await send(writer, {"type": "ERROR", "data": {"code": "BAD_JSON"}})
                    continue
                await route(session, writer, msg)
    finally:
        uid = session.get("user_id")
        if uid and STATE.user_conns.get(uid) is writer:
            STATE.user_conns.pop(uid, None)
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


async def main():
    server = await asyncio.start_server(handle_client, HOST, PORT)
    print(f"Async chat server listening on {HOST}:{PORT}")
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())


