# Minimal stub for demo
class GroupService:
    def create_group(self, payload: dict):
        name = payload.get("group_name")
        members = payload.get("members") or []
        if not name or not members:
            return False, {"message": "group_name/members required"}
        return True, {"group": {"name": name, "members": members}}
