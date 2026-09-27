"""Safe, uniform error responses. Never leak schema, SQL, stack traces or paths."""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("folio")


def _capture(exc: Exception) -> None:
    try:
        import sentry_sdk
        sentry_sdk.capture_exception(exc)
    except Exception:  # noqa: BLE001
        pass


class AppError(Exception):
    """Domain error with a machine code and a user-safe message."""

    def __init__(self, message: str, *, code: str = "app_error", status_code: int = 400):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


def _json(status_code: int, detail: str, code: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": detail, "code": code})


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError):
        return _json(exc.status_code, exc.message, exc.code)

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException):
        detail = exc.detail if isinstance(exc.detail, str) else "Request failed"
        return _json(exc.status_code, detail, code=f"http_{exc.status_code}")

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError):
        first = exc.errors()[0] if exc.errors() else {}
        loc = ".".join(str(x) for x in first.get("loc", []))
        msg = f"{loc}: {first.get('msg', 'Invalid request')}" if loc else first.get("msg", "Invalid request")
        return _json(422, msg, code="validation_error")

    @app.exception_handler(ResponseValidationError)
    async def _response_validation_error(_: Request, exc: ResponseValidationError):
        errs = exc.errors() if hasattr(exc, "errors") else []
        first = errs[0] if errs else {}
        loc = ".".join(str(x) for x in first.get("loc", []))
        logger.exception("Response validation error at %s: %s", loc, first.get("msg"))
        return _json(500, f"response:{loc}: {first.get('msg', 'invalid')}", code="response_error")

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception):
        _capture(exc)
        logger.exception("Unhandled error: %s", exc)
        return _json(500, "Something went wrong. Please try again.", code="internal_error")
