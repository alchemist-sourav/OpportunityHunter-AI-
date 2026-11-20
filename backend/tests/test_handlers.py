import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppException, DatabaseNotConfiguredError, CredentialStoreNotAvailableError
from app.core.handlers import (
    app_exception_handler,
    generic_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)


def _build_app(handler: object, exc_class: type[Exception], route: str) -> FastAPI:
    application = FastAPI()
    application.add_exception_handler(exc_class, handler)  # type: ignore[arg-type]

    if route == "/validation":

        @application.get("/items/{item_id}")
        def read_item(item_id: int) -> dict[str, int]:  # pragma: no cover
            return {"item_id": item_id}
    else:

        @application.get("/boom")
        def boom() -> dict[str, str]:  # pragma: no cover
            raise AppException("kaboom", status_code=418, error_code="teapot")

    return application


def test_app_exception_handler_returns_structured_error() -> None:
    application = _build_app(app_exception_handler, AppException, "/boom")
    with TestClient(application) as client:
        response = client.get("/boom")
    assert response.status_code == 418
    body = response.json()
    assert body["error"]["code"] == "teapot"
    assert body["error"]["message"] == "kaboom"


def test_validation_handler_returns_field_errors() -> None:
    application = _build_app(validation_exception_handler, RequestValidationError, "/validation")
    with TestClient(application, raise_server_exceptions=False) as client:
        response = client.get("/items/abc")
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert body["error"]["details"]["errors"][0]["field"].endswith("item_id")


def test_http_exception_handler_returns_error_envelope() -> None:
    application = _build_app(http_exception_handler, StarletteHTTPException, "/boom")

    @application.get("/missing")
    def missing() -> None:  # pragma: no cover
        raise StarletteHTTPException(status_code=404, detail="not found")

    with TestClient(application) as client:
        response = client.get("/missing")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "http_error"
    assert response.json()["error"]["message"] == "not found"


def test_generic_handler_hides_internal_details() -> None:
    application = _build_app(generic_exception_handler, Exception, "/boom")

    @application.get("/explode")
    def explode() -> None:  # pragma: no cover
        raise RuntimeError("secret-inner-detail")

    with TestClient(application, raise_server_exceptions=False) as client:
        response = client.get("/explode")
    assert response.status_code == 500
    body = response.json()
    assert body["error"]["code"] == "internal_error"
    assert "secret-inner-detail" not in response.text


def test_custom_exceptions_carry_phase_semantics() -> None:
    db_err = DatabaseNotConfiguredError()
    assert db_err.status_code == 503
    assert db_err.error_code == "database_not_configured"

    cred_err = CredentialStoreNotAvailableError()
    assert cred_err.status_code == 503
    assert cred_err.error_code == "credential_store_not_available"
