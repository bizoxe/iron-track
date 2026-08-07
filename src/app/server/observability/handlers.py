from __future__ import annotations

import copy
import logging.handlers
from typing import TYPE_CHECKING, override

if TYPE_CHECKING:
    from logging import LogRecord


class CustomQueueHandler(logging.handlers.QueueHandler):
    """Prevents mutation of LogRecord objects before queuing."""

    @override
    def prepare(self, record: LogRecord) -> LogRecord:
        """Override to prevent log record mutation by the base class.

        The base class mutates log entries before sending them to the queue. This method
        creates a shallow copy of the record, calculates the message, and returns the copy.

        Args:
            record (LogRecord): The log record to be prepared.

        Returns:
            LogRecord: A shallow copy of the record with the message attribute set.
        """
        record_copy = copy.copy(record)
        record_copy.message = record.getMessage()

        return record_copy
