import logging
import re
from urllib.parse import urlparse
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.errors import register_error_handlers
from app.core.middleware import SecurityHeadersMiddleware
from app.core.rate_limit import limiter
from app.db.session import dispose_engine

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await dispose_engine()




def _cors_origin_regex() -> str:
    if settings.CORS_ORIGIN_REGEX:
        return settings.CORS_ORIGIN_REGEX
    host = ""
    try:
        host = urlparse(settings.APP_URL).hostname or ""
    except Exception:
        host = ""
    parts = [r"localhost(:\d+)?", r"127\.0\.0\.1(:\d+)?", r"([a-z0-9-]+\.)*vercel\.app"]
    if host and "vercel.app" not in host:
        parts.append(r"([a-z0-9-]+\.)*" + re.escape(host))
    return r"^https?://(" + "|".join(parts) + r")$"

app = FastAPI(
    title="Folio API",
    version="0.1.0",
    description="Folio — multi-tenant portfolio SaaS. Phase 1: Foundation.",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url=None,
    openapi_url="/openapi.json" if not settings.is_production else None,
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def _rate_limit_handler(request, exc):
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please slow down.", "code": "rate_limited"},
    )


app.add_middleware(SlowAPIMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=_cors_origin_regex(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

register_error_handlers(app)
app.include_router(api_router, prefix="/api/v1")


@app.api_route("/", methods=["GET", "HEAD"])
async def root() -> dict:
    return {"service": "folio-api", "version": "0.1.0", "status": "ok"}
