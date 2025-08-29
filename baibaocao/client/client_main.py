# client/client_main.py
import logging
import time

from client.network.protocol_handler import ProtocolHandler
from client.network.socket_client import SocketClient
from client.features.auth_client import AuthClient
from client.features.message_client import MessageClient
from client.features.friend_manager import FriendManager
from client.features.group_manager import GroupManager
from client.features.notification_manager import NotificationManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def main():
    handler = ProtocolHandler()
    sock = SocketClient()

    # ---- auth wiring ----
    auth = AuthClient(sock, emit_status=lambda s: logging.info("[AUTH] %s", s))
    handler.register("AUTH_OK", auth.on_auth_ok)
    handler.register("AUTH_FAIL", auth.on_auth_fail)

    # ---- notification ----
    notif = NotificationManager(emit=lambda ev, data: logging.info("[NOTIF] %s %s", ev, data))

    # ---- message wiring ----
    current_peer_id = {"id": None}
    current_group_id = {"id": None}

    def on_recv_1v1(data: dict):
        logging.info("[MSG_RECV] %s -> %s (#%s)%s: %s",
                     data.get("from_user_id"), data.get("to_user_id"),
                     data.get("message_id"),
                     f" [reply_to={data.get('reply_to_id')}]" if data.get("reply_to_id") else "",
                     "[RECALLED]" if data.get("recalled") else data.get("content"))
        notif.on_incoming_msg(data)

    def on_history_1v1(data: dict):
        msgs = data.get("messages") or []
        logging.info("[HISTORY] peer=%s has_more=%s", data.get("peer_id"), data.get("has_more"))
        for m in msgs:
            tag = "[RECALLED]" if m.get("recalled") else m.get("content")
            rx = m.get("reactions_summary") or {}
            logging.info(" - [%s] %s -> %s: %s %s",
                         m.get("message_id"), m.get("from_user_id"),
                         m.get("to_user_id"), tag,
                         f"(react={rx})" if rx else "")

    msg_cli = MessageClient(
        sock,
        on_recv=on_recv_1v1,
        on_history=on_history_1v1,
        on_seen_update=lambda d: logging.info("[SEEN_UPDATE] %s", d),
        on_recall_update=lambda d: logging.info("[RECALL_UPDATE] %s", d),
        on_react_update=lambda d: logging.info("[REACT_UPDATE] %s", d),
    )
    handler.register("MSG_RECV", msg_cli.handle_msg_recv)
    handler.register("MSG_HISTORY_RESULT", msg_cli.handle_history_result)
    handler.register("MSG_SEEN_UPDATE", msg_cli.handle_seen_update)
    handler.register("MSG_RECALL_UPDATE", msg_cli.handle_recall_update)
    handler.register("MSG_REACT_UPDATE", msg_cli.handle_react_update)

    # ---- groups wiring ----
    def on_group_event(ev: str, data: dict):
        logging.info("[GROUP] %s %s", ev, data)

    grp = GroupManager(sock, on_event=on_group_event)
    handler.register("GROUP_CREATED", grp.on_created)
    handler.register("GROUP_LIST_RESULT", grp.on_list_result)
    handler.register("GROUP_MSG_RECV", lambda m: (notif.on_incoming_msg(m.get("data", {})),
                                                  logging.info("[GROUP_MSG] %s", m.get("data"))))
    handler.register("GROUP_HISTORY_RESULT", lambda m: logging.info("[GROUP_HISTORY] %s", m.get("data")))

    # ---- misc handlers ----
    handler.register("PONG", lambda m: None)
    handler.register("ERROR", lambda m: logging.warning("[ERROR] %s", m.get("data")))

    sock.set_on_message(handler.handle)
    sock.start()

    try:
        time.sleep(0.3)
        logging.info("Lệnh:")
        logging.info("  reg <u> <p> | login <u> <p>")
        logging.info("  peer <user_id> | send <text> | history")
        logging.info("  reply <message_id> <text> | seen <id1> [id2] ... | recall <id> | react <id> <like|heart|smile>")
        logging.info("  group create <name> | group add <gid> <uid> | group list")
        logging.info("  group send <gid> <text> | group reply <gid> <msg_id> <text> | group history <gid>")
        logging.info("  exit")
        while True:
            cmd = input("> ").strip()
            if not cmd:
                continue
            if cmd.lower() in ("quit", "exit"):
                break

            parts = cmd.split(" ", 1)
            action = parts[0]

            if action in ("reg", "login"):
                try:
                    _, rest = cmd.split(" ", 1)
                    u, p = rest.split(" ", 1)
                except ValueError:
                    logging.info("Cú pháp: reg <u> <p> | login <u> <p>")
                    continue
                (auth.register if action == "reg" else auth.login)(u, p)

            elif action == "peer":
                try:
                    pid = int(parts[1].strip())
                except Exception:
                    logging.info("Cú pháp: peer <user_id>")
                    continue
                current_peer_id["id"] = pid
                current_group_id["id"] = None
                notif.set_active_group(None)
                notif.set_active_peer(pid)
                logging.info("Đã chọn peer_id=%s", pid)

            elif action == "send":
                if current_peer_id["id"] is None:
                    logging.info("Chưa chọn peer. Dùng: peer <user_id>")
                    continue
                content = parts[1] if len(parts) > 1 else ""
                if not content.strip():
                    logging.info("Nội dung rỗng.")
                    continue
                msg_cli.send_text(current_peer_id["id"], content)

            elif action == "history":
                if current_peer_id["id"] is None:
                    logging.info("Chưa chọn peer. Dùng: peer <user_id>")
                    continue
                msg_cli.get_history(current_peer_id["id"], before_id=None, limit=50)

            elif action == "reply":
                if current_peer_id["id"] is None:
                    logging.info("Chưa chọn peer. Dùng: peer <user_id>")
                    continue
                try:
                    msg_id_str, text = parts[1].split(" ", 1)
                    mid = int(msg_id_str)
                except Exception:
                    logging.info("Cú pháp: reply <message_id> <text>")
                    continue
                msg_cli.send_text(current_peer_id["id"], text, reply_to_id=mid)

            elif action == "seen":
                try:
                    ids = [int(x) for x in (parts[1].split() if len(parts) > 1 else [])]
                except Exception:
                    logging.info("Cú pháp: seen <id1> [id2] ...")
                    continue
                if not ids:
                    logging.info("Không có id nào.")
                    continue
                msg_cli.mark_seen(ids)
                notif.mark_seen(ids)

            elif action == "recall":
                try:
                    mid = int(parts[1].strip())
                except Exception:
                    logging.info("Cú pháp: recall <message_id>")
                    continue
                msg_cli.recall(mid)

            elif action == "react":
                try:
                    mid_str, reaction = parts[1].split()
                    mid = int(mid_str)
                except Exception:
                    logging.info("Cú pháp: react <message_id> <like|heart|smile>")
                    continue
                msg_cli.react(mid, reaction)

            elif action == "group":
                if len(parts) == 1:
                    logging.info("Cú pháp: group <create|add|list|send|reply|history> ...")
                    continue
                sub_parts = parts[1].split(" ", 1)
                subcmd = sub_parts[0]
                rest = sub_parts[1] if len(sub_parts) > 1 else ""

                if subcmd == "create":
                    name = rest.strip()
                    if not name:
                        logging.info("Cú pháp: group create <name>"); continue
                    grp.create(name)

                elif subcmd == "add":
                    try:
                        g_id_str, u_id_str = rest.split()
                        g_id, u_id = int(g_id_str), int(u_id_str)
                    except Exception:
                        logging.info("Cú pháp: group add <group_id> <user_id>"); continue
                    grp.add_member(g_id, u_id)

                elif subcmd == "list":
                    grp.list()

                elif subcmd == "send":
                    try:
                        g_id_str, text = rest.split(" ", 1)
                        g_id = int(g_id_str)
                    except Exception:
                        logging.info("Cú pháp: group send <group_id> <text>"); continue
                    grp.send_text(g_id, text)
                    current_group_id["id"] = g_id
                    current_peer_id["id"] = None
                    notif.set_active_peer(None)
                    notif.set_active_group(g_id)

                elif subcmd == "reply":
                    try:
                        g_id_str, mid_str, text = rest.split(" ", 2)
                        g_id, mid = int(g_id_str), int(mid_str)
                    except Exception:
                        logging.info("Cú pháp: group reply <group_id> <message_id> <text>"); continue
                    grp.send_text(g_id, text, reply_to_id=mid)
                    current_group_id["id"] = g_id
                    current_peer_id["id"] = None
                    notif.set_active_peer(None)
                    notif.set_active_group(g_id)

                elif subcmd == "history":
                    try:
                        g_id = int(rest.strip())
                    except Exception:
                        logging.info("Cú pháp: group history <group_id>"); continue
                    grp.get_history(g_id, before_id=None, limit=50)
                    current_group_id["id"] = g_id
                    current_peer_id["id"] = None
                    notif.set_active_peer(None)
                    notif.set_active_group(g_id)
                else:
                    logging.info("Không hiểu. Dùng: group <create|add|list|send|reply|history> ...")

            else:
                logging.info("Không hiểu. Gõ 'exit' để thoát.")
    except KeyboardInterrupt:
        pass
    finally:
        sock.stop()
        logging.info("Client stopped.")


if __name__ == "__main__":
    main()
