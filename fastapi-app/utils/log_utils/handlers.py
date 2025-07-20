from __future__ import annotations

import copy
import logging.handlers
from typing import TYPE_CHECKING, override

if TYPE_CHECKING:
    from logging import LogRecord


class CustomQueueHandler(logging.handlers.QueueHandler):
    @override
    def prepare(self, record: LogRecord) -> LogRecord:
        """By default, the QueueHandler class mutates log entries before sending them to the queue.

        Override the method of the base class.
        """
        record_copy = copy.copy(record)
        record_copy.message = record.getMessage()

        return record_copy
