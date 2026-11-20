import pytest

from app.core.config import Settings
from app.core.exceptions import DatabaseNotConfiguredError
from app.database import engine as engine_mod


def test_get_engine_raises_when_database_url_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(engine_mod, "get_settings", lambda: Settings(database_url=None))
    engine_mod._engine = None
    engine_mod._session_factory = None
    with pytest.raises(DatabaseNotConfiguredError):
        engine_mod.get_engine()


def test_get_session_factory_raises_when_database_url_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(engine_mod, "get_settings", lambda: Settings(database_url=None))
    engine_mod._engine = None
    engine_mod._session_factory = None
    with pytest.raises(DatabaseNotConfiguredError):
        engine_mod.get_session_factory()
