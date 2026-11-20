def redact_secret(value: str | None) -> str:
    if value is None:
        return "<not set>"
    if not value.strip():
        return "<empty>"
    return "redacted"
