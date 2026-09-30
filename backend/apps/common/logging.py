import json
import logging
from datetime import datetime, timezone

from apps.common.middleware import get_current_request_id


class RequestIDFilter(logging.Filter):
    """Logging filter to inject request_id from thread-local context into log record."""

    def filter(self, record):
        record.request_id = get_current_request_id() or "-"
        return True


class StructuredJSONFormatter(logging.Formatter):
    """Custom JSON formatter producing machine-readable structured logs."""

    def format(self, record):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
            "module": record.module,
            "func_name": record.funcName,
            "line_no": record.lineno,
            "process_id": record.process,
            "thread_id": record.thread,
        }

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)
