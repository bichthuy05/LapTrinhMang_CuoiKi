class User:
    def __init__(self, user_id, username):
        self.user_id = user_id
        self.username = username

class Message:
    def __init__(self, sender, receiver, content, timestamp):
        self.sender = sender
        self.receiver = receiver
        self.content = content
        self.timestamp = timestamp