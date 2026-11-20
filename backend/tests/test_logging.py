import json
import logging
import sys

from app.core.logging import JsonFormatter


def test_json_formatter_includes_standard_fields() -> None:
    record = logging.LogRecord(
        name="app.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello %s",
        args=("world",),
        exc_info=None,
        func="test_json_formatter_includes_standard_fields",
    )
    payload = json.loads(JsonFormatter().format(record))
    assert payload["message"] == "hello world"
    assert payload["level"] == "INFO"
    assert payload["logger"] == "app.test"
    assert payload["module"]
    assert payload["function"]
    assert payload["line"] == 1
    assert payload["timestamp"]
    assert "exception" not in payload


def test_json_formatter_serializes_exception() -> None:
    try:
        raise ValueError("boom")
    except ValueError:
        record = logging.LogRecord(
            name="app.test",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg="failed",
            args=(),
            exc_info=sys.exc_info(),
            func="test_json_formatter_serializes_exception",
        )
    payload = json.loads(JsonFormatter().format(record))
    assert "ValueError" in payload["exception"]
    assert "boom" in payload["exception"]
