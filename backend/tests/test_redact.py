from app.core.redact import redact_secret


def test_redact_none_returns_not_set() -> None:
    assert redact_secret(None) == "<not set>"


def test_redact_blank_returns_empty() -> None:
    assert redact_secret("") == "<empty>"
    assert redact_secret("   ") == "<empty>"


def test_redact_never_reveals_value() -> None:
    assert redact_secret("fc-live-key-12345") == "redacted"
    assert "fc-live-key-12345" not in redact_secret("fc-live-key-12345")
