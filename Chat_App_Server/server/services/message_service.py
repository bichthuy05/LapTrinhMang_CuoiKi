from server.models.message_model import MessageModel

class MessageService:
    def __init__(self):
        self.msg_model = MessageModel()

    def send_message(self, payload: dict):
        sender = payload.get("sender")
        receiver = payload.get("receiver")
        text = payload.get("text")
        if not all([sender, receiver, text]):
            return False, {"message": "sender/receiver/text required"}
        msg = self.msg_model.save_message(sender, receiver, text)
        return True, {"message": msg}
