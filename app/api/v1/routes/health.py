import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.db.session import get_sessionmaker

logger = logging.getLogger("folio")
router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    # No DB touch — always succeeds so the platform can detect the open port.
    return {"status": "ok"}


@router.get("/health/db")
async def health_db():
    try:
        async with get_sessionmaker()() as session:
            await session.execute(text("SELECT 1"))
    except Exception as exc:
        logger.error("DB health check failed: %s", exc)
        return JSONResponse(
            status_code=503,
            content={"status": "error", "db": "unavailable", "code": "db_unavailable"},
        )
    return {"status": "ok", "db": "ok"}
