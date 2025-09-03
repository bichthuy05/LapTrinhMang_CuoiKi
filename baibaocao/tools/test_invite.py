import json, uuid, time, urllib.request, urllib.parse

BASE = "http://127.0.0.1:8080"
SID_A = "11111111-1111-1111-1111-111111111111"
SID_B = "22222222-2222-2222-2222-222222222222"

def http_post(path, params, obj):
    url = f"{BASE}{path}?" + urllib.parse.urlencode(params)
    data = json.dumps(obj).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=5) as resp:
        raw = resp.read().decode()
        try:
            return json.loads(raw)
        except Exception:
            return {"_raw": raw}

def http_get(path, params):
    url = f"{BASE}{path}?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=5) as resp:
        raw = resp.read().decode()
        try:
            return json.loads(raw)
        except Exception:
            return {"_raw": raw}

def send(sid, obj):
    res = http_post("/api/send", {"sid": sid}, obj)
    print("SEND", obj["type"], "->", res)
    return res

def poll(sid, label):
    res = http_get("/api/poll", {"sid": sid})
    print("POLL", label, "->", res)
    return res

if __name__ == "__main__":
    # Register/login users
    send(SID_A, {"type": "AUTH_REGISTER", "data": {"username": "userA", "password": "a"}})
    send(SID_A, {"type": "AUTH_LOGIN", "data": {"username": "userA", "password": "a"}})

    send(SID_B, {"type": "AUTH_REGISTER", "data": {"username": "userB", "password": "b"}})
    send(SID_B, {"type": "AUTH_LOGIN", "data": {"username": "userB", "password": "b"}})

    # Create group by A
    res = send(SID_A, {"type": "GROUP_CREATE", "data": {"name": "laptrinhmang"}})
    gid = res.get("data", {}).get("group_id", 1)

    # A adds B -> should create invite
    send(SID_A, {"type": "GROUP_ADD", "data": {"group_id": gid, "user_id": 2}})

    # Poll both sides to see messages
    poll(SID_A, "A")
    poll(SID_B, "B")

    # Ask B to list invites
    send(SID_B, {"type": "GROUP_INVITE_LIST", "data": {}})
    poll(SID_B, "B after list")

    print("Done.")

