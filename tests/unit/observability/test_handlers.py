from __future__ import annotations

import logging
from queue import SimpleQueue
from typing import Any

from asgi_correlation_id import correlation_id

from app.server.observability.handlers import CustomQueueHandler


def make_record(msg: Any) -> logging.LogRecord:
    """A structlog-shaped record: `msg` carries the raw event dict."""
    return logging.LogRecord(
        name="unit",
        level=logging.ERROR,
        pathname=__file__,
        lineno=1,
        msg=msg,
        args=(),
        exc_info=None,
        func="test",
    )


def test_prepare_resolves_exc_info_true_into_a_real_tuple() -> None:
    """`exc_info: True` becomes a real tuple while except block is alive."""
    handler = CustomQueueHandler(SimpleQueue())
    record = make_record({"event": "boom", "exc_info": True})
    boom = RuntimeError("boom")
    try:
        raise boom
    except RuntimeError:
        prepared = handler.prepare(record)
    # typeshed types LogRecord.msg as str; the structlog-shaped records
    # carry a dict, so narrow it back before indexing.
    assert isinstance(prepared.msg, dict)
    resolved = prepared.msg["exc_info"]
    assert isinstance(resolved, tuple)
    assert resolved[0] is RuntimeError
    assert isinstance(resolved[1], RuntimeError)
    assert resolved[2] is not None  # the traceback object itself
    assert isinstance(record.msg, dict)
    assert record.msg["exc_info"] is True  # the shared record stays untouched
    assert prepared.msg is not record.msg


def test_prepare_injects_request_id_from_the_emitting_thread() -> None:
    handler = CustomQueueHandler(SimpleQueue())
    token = correlation_id.set("req-42")
    try:
        prepared = handler.prepare(make_record({"event": "x"}))
    finally:
        correlation_id.reset(token)
    assert prepared.request_id == "req-42"  # type: ignore[attr-defined]


def test_prepare_without_request_id_sets_no_attribute() -> None:
    handler = CustomQueueHandler(SimpleQueue())
    prepared = handler.prepare(make_record({"event": "x"}))
    assert not hasattr(prepared, "request_id")


def test_prepare_leaves_other_messages_untouched() -> None:
    """Only the exact `{"exc_info": True}` flag triggers resolution."""
    handler = CustomQueueHandler(SimpleQueue())
    prepared_flag_off = handler.prepare(make_record({"event": "x", "exc_info": False}))
    assert prepared_flag_off.msg == {"event": "x", "exc_info": False}
    prepared_plain = handler.prepare(make_record("plain message"))
    assert prepared_plain.msg == "plain message"
