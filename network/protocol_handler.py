
from typing import Callable, Dict
import logging

logger = logging.getLogger(__name__)


class ProtocolHandler:
    """
    Router đơn giản: map type -> handler(payload_dict).
    """

    def __init__(self):
        self._handlers: Dict[str, Callable[[dict], None]] = {}

    def register(self, msg_type: str, fn: Callable[[dict], None]):
        self._handlers[msg_type] = fn

    def unregister(self, msg_type: str):
        self._handlers.pop(msg_type, None)

    def handle(self, message: dict):
        msg_type = message.get("type")
        if not msg_type:
            logger.warning("Message missing 'type': %s", message)
            return
        fn = self._handlers.get(msg_type)
        if fn:
            try:
                fn(message)
            except Exception as e:
                logger.exception("Handler error for %s: %s", msg_type, e)
        else:
            logger.info("No handler for type=%s -> %s", msg_type, message)
