import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import settings
from app.db.session import get_sessionmaker

logger = logging.getLogger("folio")
router = APIRouter(tags=["health"])

_EXPECTED_TABLES = {
    "profiles",
    "portfolios",
    "portfolio_profiles",
    "username_history",
    "reserved_usernames",
}


@router.api_route("/health", methods=["GET", "HEAD"])
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


@router.get("/health/status")
async def status_report():
    """One-glance diagnostics: DB reachable? migrations applied? auth configured?
    Returns only booleans / table names — no secrets, no user data."""
    checks: dict = {}

    # 1) database connectivity
    db_ok = False
    try:
        async with get_sessionmaker()() as session:
            await session.execute(text("SELECT 1"))
        db_ok = True
        checks["database"] = {"ok": True}
    except Exception:
        checks["database"] = {"ok": False, "hint": "Set DATABASE_URL (Supabase pooler, port 6543)."}

    # 2) migrations / tables present
    if db_ok:
        try:
            async with get_sessionmaker()() as session:
                rows = await session.execute(
                    text(
                        "select table_name from information_schema.tables "
                        "where table_schema = 'public'"
                    )
                )
                found = {r[0] for r in rows}
            missing = sorted(_EXPECTED_TABLES - found)
            checks["migrations"] = {
                "ok": not missing,
                "missing_tables": missing,
                "hint": None if not missing else "Run the SQL files in migrations/ (0001..0003).",
            }

            # 3) reserved usernames seeded
            async with get_sessionmaker()() as session:
                seeded = (
                    await session.execute(text("select count(*) from public.reserved_usernames"))
                ).scalar_one() if not missing else 0
            checks["reserved_usernames_seeded"] = {"ok": bool(seeded), "count": int(seeded)}
        except Exception:
            checks["migrations"] = {"ok": False, "hint": "Could not read schema."}

    # 4) auth configuration (booleans only)
    checks["auth"] = {
        "ok": bool(settings.SUPABASE_URL) and (
            bool(settings.SUPABASE_JWT_SECRET) or bool(settings.SUPABASE_URL)
        ),
        "supabase_url_set": bool(settings.SUPABASE_URL),
        "jwt_secret_set": bool(settings.SUPABASE_JWT_SECRET),
        "jwks_verification": "enabled (asymmetric ES256/RS256 + HS256 fallback)",
    }

    all_ok = all(c.get("ok", False) for c in checks.values())
    return {"ok": all_ok, "app_env": settings.APP_ENV, "checks": checks}
