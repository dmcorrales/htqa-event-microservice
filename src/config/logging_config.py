import logging
import json
import re
from datetime import datetime, timezone

from src.config.settings import settings

_IP_PATTERN = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")


def _mask_ip(text: str) -> str:
    return _IP_PATTERN.sub(lambda m: m.group().rsplit(".", 1)[0] + ".***", text)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": _mask_ip(record.getMessage()),
        }
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        correlation_id = getattr(record, "correlation_id", None)
        if correlation_id:
            log_entry["correlation_id"] = correlation_id
        return json.dumps(log_entry)


def setup_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(settings.log_level.upper())

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
