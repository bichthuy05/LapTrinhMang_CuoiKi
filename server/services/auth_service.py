from server.models.user_model import UserModel

class AuthService:
    def __init__(self):
        self.user_model = UserModel()

    def login(self, payload: dict):
        username = payload.get("username")
        password = payload.get("password")
        if not username or not password:
            return False, {"message": "username/password required"}
        user = self.user_model.find_by_username(username)
        if user and user["password"] == password:
            return True, {"user": {"id": user["id"], "username": user["username"]}}
        return False, {"message": "Invalid credentials"}

    def register(self, payload: dict):
        username = payload.get("username")
        password = payload.get("password")
        if not username or not password:
            return False, {"message": "username/password required"}
        if self.user_model.find_by_username(username):
            return False, {"message": "User already exists"}
        user = self.user_model.create_user(username, password)
        return True, {"user": {"id": user["id"], "username": user["username"]}}
