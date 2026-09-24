from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import AppError
from app.models import Portfolio, ReservedUsername, UsernameHistory
from app.utils.username import (
    error_message,
    normalize_username,
    suggestion_candidates,
    validate_username_format,
)


async def is_reserved(db: AsyncSession, name: str) -> bool:
    row = await db.get(ReservedUsername, normalize_username(name))
    return row is not None


async def is_taken(db: AsyncSession, name: str, *, exclude_portfolio_id=None) -> bool:
    stmt = select(func.count()).select_from(Portfolio).where(
        func.lower(Portfolio.username) == normalize_username(name)
    )
    if exclude_portfolio_id is not None:
        stmt = stmt.where(Portfolio.id != exclude_portfolio_id)
    return bool((await db.execute(stmt)).scalar_one())


async def check_availability(db: AsyncSession, raw: str) -> dict:
    name = normalize_username(raw)
    ok, code = validate_username_format(name)
    if not ok:
        return {
            "username": name,
            "available": False,
            "reason": code,
            "message": error_message(code),
            "suggestions": await _available_suggestions(db, name),
        }
    if await is_reserved(db, name):
        return {
            "username": name, "available": False, "reason": "reserved",
            "message": error_message("reserved"),
            "suggestions": await _available_suggestions(db, name),
        }
    if await is_taken(db, name):
        return {
            "username": name, "available": False, "reason": "taken",
            "message": error_message("taken"),
            "suggestions": await _available_suggestions(db, name),
        }
    return {"username": name, "available": True, "reason": None, "message": None, "suggestions": []}


async def _available_suggestions(db: AsyncSession, desired: str, limit: int = 5) -> list[str]:
    out: list[str] = []
    for cand in suggestion_candidates(desired):
        if await is_reserved(db, cand) or await is_taken(db, cand):
            continue
        out.append(cand)
        if len(out) >= limit:
            break
    return out


async def set_username(db: AsyncSession, portfolio: Portfolio, raw: str) -> Portfolio:
    """Validate + apply a username change with cooldown policy and history. Atomic."""
    name = normalize_username(raw)

    ok, code = validate_username_format(name)
    if not ok:
        raise AppError(error_message(code), code=code, status_code=422)
    if await is_reserved(db, name):
        raise AppError(error_message("reserved"), code="reserved", status_code=409)
    if await is_taken(db, name, exclude_portfolio_id=portfolio.id):
        raise AppError(error_message("taken"), code="taken", status_code=409)

    if portfolio.username is not None and normalize_username(portfolio.username) == name:
        return portfolio  # no-op

    cooldown = settings.USERNAME_CHANGE_COOLDOWN_DAYS
    if cooldown > 0 and portfolio.username_changed_at is not None:
        next_allowed = portfolio.username_changed_at + timedelta(days=cooldown)
        now = datetime.now(timezone.utc)
        if now < next_allowed:
            days = (next_allowed - now).days + 1
            raise AppError(
                f"You can change your username again in {days} day(s).",
                code="cooldown",
                status_code=429,
            )

    old = portfolio.username
    portfolio.username = name
    portfolio.username_change_count = (portfolio.username_change_count or 0) + 1
    portfolio.username_changed_at = datetime.now(timezone.utc)
    db.add(UsernameHistory(portfolio_id=portfolio.id, old_username=old, new_username=name))
    await db.commit()
    await db.refresh(portfolio)
    return portfolio
