from server.models.friend_model import FriendModel

class FriendService:
    def __init__(self):
        self.friend_model = FriendModel()

    def add_friend(self, payload: dict):
        user = payload.get("user")
        friend = payload.get("friend")
        if not user or not friend:
            return False, {"message": "user/friend required"}
        self.friend_model.add_friend(user, friend)
        return True, {"message": f"{friend} added"}
