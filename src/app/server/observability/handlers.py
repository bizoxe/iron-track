from __future__ import annotations

import logging.handlers
from copy import copy
from sys import exc_info
from typing import TYPE_CHECKING, override

from asgi_correlation_id import correlation_id

if TYPE_CHECKING:
    from logging import LogRecord


class CustomQueueHandler(logging.handlers.QueueHandler):
    """Queue raw records for listener-side formatting.

    Unlike the base implementation, does not pre-format via self.format() on
    the emitting thread and keeps args/exc_info intact, so the QueueListener-side
    ProcessorFormatter performs the single rendering pass off the event loop.
    """

    @override
    def prepare(self, record: LogRecord) -> LogRecord:
        """Copy the record and capture thread-local state before queuing.

        Resolves the native ``exc_info=True`` flag to a real tuple here, on the
        emitting thread, inside the still-active except block; on the listener
        thread ``sys.exc_info()`` is empty and the traceback is unrecoverable.
        """
        record_copy = copy(record)
        msg = record_copy.msg
        if isinstance(msg, dict) and msg.get("exc_info") is True:
            record_copy.msg = {**msg, "exc_info": exc_info()}
        # Contextvars do not cross threads: pre-chain processors run on the
        # listener thread where correlation_id is never set. The request id
        # is only available here.
        if request_id := correlation_id.get():
            record_copy.request_id = request_id
        return record_copy
