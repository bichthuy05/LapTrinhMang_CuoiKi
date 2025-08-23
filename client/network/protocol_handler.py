import json

class ProtocolHandler:
    @staticmethod
    def build_message(command: str, payload: dict):
        return json.dumps({
            "command": command,
            "payload": payload
        })

    @staticmethod
    def parse_message(raw_data: str):
        try:
            return json.loads(raw_data)
        except json.JSONDecodeError:
            return None
    @staticmethod
    def build_login(username, password):
        return ProtocolHandler.build_message("LOGIN", {
            "username": username,
            "password": password
        })
login_msg = ProtocolHandler.build_login("nhuan", "123456")
