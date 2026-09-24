from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.rate_limit import limiter
from app.core.security import CurrentUser, get_current_user
from app.db.session import get_db
from app.schemas.portfolio import (
    PortfolioOut,
    PortfolioProfileUpdate,
    StatusUpdateIn,
    UsernameSetIn,
)
from app.services import portfolio_service, profile_service, username_service

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("", response_model=PortfolioOut)
async def get_my_portfolio(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PortfolioOut:
    await profile_service.get_or_create_account(db, user)
    portfolio = await portfolio_service.ensure_primary_portfolio(db, user.id)
    return PortfolioOut.model_validate(portfolio)


@router.patch("/profile", response_model=PortfolioOut)
async def update_profile_section(
    payload: PortfolioProfileUpdate,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PortfolioOut:
    portfolio = await portfolio_service.ensure_primary_portfolio(db, user.id)
    portfolio = await portfolio_service.update_profile_section(db, portfolio, payload)
    return PortfolioOut.model_validate(portfolio)


@router.put("/username", response_model=PortfolioOut)
@limiter.limit(settings.RATE_LIMIT_USERNAME_SET)
async def set_username(
    request: Request,
    payload: UsernameSetIn,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PortfolioOut:
    portfolio = await portfolio_service.ensure_primary_portfolio(db, user.id)
    portfolio = await username_service.set_username(db, portfolio, payload.username)
    return PortfolioOut.model_validate(portfolio)


@router.patch("/status", response_model=PortfolioOut)
@limiter.limit(settings.RATE_LIMIT_DEFAULT_WRITE)
async def update_status(
    request: Request,
    payload: StatusUpdateIn,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PortfolioOut:
    portfolio = await portfolio_service.ensure_primary_portfolio(db, user.id)
    portfolio = await portfolio_service.update_status(db, portfolio, payload.status)
    return PortfolioOut.model_validate(portfolio)
