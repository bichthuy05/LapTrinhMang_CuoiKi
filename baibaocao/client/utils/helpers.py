
import json
import uuid

ENCODING = "utf-8"


def new_request_id() -> str:
    return str(uuid.uuid4())


def encode_line(obj: dict) -> bytes:
    """
    Serialize dict -> JSON string + newline, encode to bytes.
    """
    s = json.dumps(obj, ensure_ascii=False)
    if not s.endswith("\n"):
        s += "\n"
    return s.encode(ENCODING)


def decode_line(line: bytes) -> dict:
    return json.loads(line.decode(ENCODING).rstrip("\n"))
