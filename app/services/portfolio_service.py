from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models import Portfolio, PortfolioProfile
from app.schemas.portfolio import PortfolioProfileUpdate

_VALID_STATUSES = {"draft", "published", "unpublished"}


async def get_primary_portfolio(db: AsyncSession, user_id: str) -> Portfolio | None:
    stmt = (
        select(Portfolio)
        .where(
            Portfolio.user_id == uuid.UUID(user_id),
            Portfolio.deleted_at.is_(None),
        )
        .order_by(Portfolio.is_primary.desc(), Portfolio.created_at.asc())
        .limit(1)
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def ensure_primary_portfolio(db: AsyncSession, user_id: str) -> Portfolio:
    """Safety net if the signup trigger didn't create one."""
    existing = await get_primary_portfolio(db, user_id)
    if existing:
        return existing
    portfolio = Portfolio(user_id=uuid.UUID(user_id), is_primary=True, status="draft")
    db.add(portfolio)
    await db.flush()
    db.add(PortfolioProfile(portfolio_id=portfolio.id))
    await db.commit()
    await db.refresh(portfolio)
    return portfolio


async def get_owned_portfolio(db: AsyncSession, user_id: str, portfolio_id: uuid.UUID) -> Portfolio:
    """IDOR guard: return a portfolio only if it belongs to this user."""
    portfolio = await db.get(Portfolio, portfolio_id)
    if portfolio is None or portfolio.deleted_at is not None:
        raise AppError("Portfolio not found", code="not_found", status_code=404)
    if str(portfolio.user_id) != str(user_id):
        # Do not reveal that the resource exists.
        raise AppError("Portfolio not found", code="not_found", status_code=404)
    return portfolio


async def update_profile_section(
    db: AsyncSession, portfolio: Portfolio, data: PortfolioProfileUpdate
) -> Portfolio:
    section = portfolio.profile
    if section is None:
        section = PortfolioProfile(portfolio_id=portfolio.id)
        db.add(section)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(section, field, value)
    await db.commit()
    await db.refresh(portfolio)
    return portfolio


async def update_status(db: AsyncSession, portfolio: Portfolio, status: str) -> Portfolio:
    if status not in _VALID_STATUSES:
        raise AppError("Invalid status", code="invalid_status", status_code=422)
    if status == "published" and not portfolio.username:
        raise AppError(
            "Choose a username before publishing.",
            code="username_required",
            status_code=409,
        )
    portfolio.status = status
    await db.commit()
    await db.refresh(portfolio)
    return portfolio
