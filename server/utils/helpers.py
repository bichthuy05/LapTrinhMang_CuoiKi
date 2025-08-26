import uuid, datetime

def generate_id() -> str:
    return str(uuid.uuid4())

def now_iso() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
