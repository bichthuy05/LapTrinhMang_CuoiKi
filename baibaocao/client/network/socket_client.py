
import socket
import threading
import time
import logging
from typing import Optional, Callable
from ..utils import config
from ..utils.helpers import encode_line, decode_line

logger = logging.getLogger(__name__)


class SocketClient:
    def __init__(self, host: str = None, port: int = None):
        self.host = host or config.SERVER_HOST
        self.port = port or config.SERVER_PORT
        self._sock: Optional[socket.socket] = None
        self._recv_thread: Optional[threading.Thread] = None
        self._hb_thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._connected = threading.Event()
        self._last_pong_ts = 0.0
        self._on_message: Optional[Callable[[dict], None]] = None

    def set_on_message(self, cb: Callable[[dict], None]):
        self._on_message = cb

    # ---- lifecycle ----
    def start(self):
        self._stop.clear()
        self._connect()
        self._recv_thread = threading.Thread(target=self._recv_loop, name="recv_loop", daemon=True)
        self._recv_thread.start()
        self._hb_thread = threading.Thread(target=self._heartbeat_loop, name="heartbeat", daemon=True)
        self._hb_thread.start()

    def stop(self):
        self._stop.set()
        try:
            if self._sock:
                self._sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        finally:
            if self._sock:
                self._sock.close()
            self._sock = None

    # ---- network primitives ----
    def _connect(self):
        backoff = 1
        while not self._stop.is_set():
            try:
                s = socket.create_connection((self.host, self.port), timeout=config.CONNECT_TIMEOUT)
                s.settimeout(None)  # blocking
                self._sock = s
                self._connected.set()
                self._last_pong_ts = time.time()
                logger.info("Connected to %s:%s", self.host, self.port)
                return
            except Exception as e:
                logger.warning("Connect failed: %s; retry in %ss", e, backoff)
                self._connected.clear()
                time.sleep(backoff)
                backoff = min(backoff * 2, config.RECONNECT_MAX_BACKOFF)

    def send_json(self, obj: dict):
        data = encode_line(obj)
        try:
            if not self._sock:
                raise RuntimeError("Socket not connected")
            self._sock.sendall(data)
        except Exception as e:
            logger.warning("send_json error: %s; will try reconnect", e)
            self._connected.clear()
            self._reconnect()

    # ---- loops ----
    def _recv_loop(self):
        buf = b""
        while not self._stop.is_set():
            if not self._sock:
                self._reconnect()
                continue
            try:
                chunk = self._sock.recv(4096)
                if not chunk:
                    raise ConnectionError("peer closed")
                buf += chunk
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    if not line:
                        continue
                    msg = decode_line(line + b"\n")
                    if msg.get("type") == "PONG":
                        self._last_pong_ts = time.time()
                    if self._on_message:
                        self._on_message(msg)
            except Exception as e:
                logger.warning("recv_loop error: %s", e)
                self._connected.clear()
                self._reconnect()

    def _heartbeat_loop(self):
        while not self._stop.is_set():
            if not self._connected.is_set():
                time.sleep(1)
                continue
            self.send_json({"type": "PING", "data": {}, "request_id": "hb"})
            if time.time() - self._last_pong_ts > config.HEARTBEAT_TIMEOUT:
                logger.warning("Heartbeat timeout; reconnecting...")
                self._connected.clear()
                self._reconnect()
            time.sleep(config.HEARTBEAT_INTERVAL)

    def _reconnect(self):
        try:
            if self._sock:
                try:
                    self._sock.shutdown(socket.SHUT_RDWR)
                except Exception:
                    pass
                self._sock.close()
        finally:
            self._sock = None