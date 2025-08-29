
from client.utils.helpers import encode_line, decode_line


def test_encode_decode_roundtrip():
    payload = {"type": "PING", "data": {}, "request_id": "1"}
    line = encode_line(payload)
    assert line.endswith(b"\n")
    assert decode_line(line) == payload
