from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.rate_limit import limiter
from app.core.security import CurrentUser, get_current_user
from app.api.deps import get_current_account
from app.core.features import has_feature, is_pro_account
from app.models import CustomTemplate, PlatformSettings, Profile
from app.schemas.extras import ApplyTemplateIn
from app.db.session import get_db
from app.schemas.portfolio import (
    PortfolioOut,
    PortfolioProfileUpdate,
    StatusUpdateIn,
    AccentUpdateIn,
    TemplateUpdateIn,
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


@router.patch("/template", response_model=PortfolioOut)
async def update_template(
    payload: TemplateUpdateIn,
    account: Profile = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
) -> PortfolioOut:
    if payload.template in portfolio_service.PRO_TEMPLATES:
        s = await db.get(PlatformSettings, 1)
        pro_features = list(s.pro_features) if s and s.pro_features else []
        if not has_feature("premium_templates", pro_features, account.role, account.plan):
            from app.core.errors import AppError
            raise AppError("This is a premium template. Upgrade to Pro to use it.", code="template_locked", status_code=403)
    portfolio = await portfolio_service.ensure_primary_portfolio(db, str(account.id))
    portfolio = await portfolio_service.update_template(db, portfolio, payload.template)
    return PortfolioOut.model_validate(portfolio)


@router.patch("/accent", response_model=PortfolioOut)
async def update_accent(
    payload: AccentUpdateIn,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PortfolioOut:
    portfolio = await portfolio_service.ensure_primary_portfolio(db, user.id)
    portfolio = await portfolio_service.update_accent(db, portfolio, payload.accent)
    return PortfolioOut.model_validate(portfolio)


@router.post("/apply-template", response_model=PortfolioOut)
async def apply_custom_template(
    payload: ApplyTemplateIn,
    account: Profile = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
) -> PortfolioOut:
    tpl = await db.get(CustomTemplate, payload.template_id)
    if tpl is None or not tpl.is_published:
        from app.core.errors import AppError
        raise AppError("Template not found", code="not_found", status_code=404)
    if tpl.plan == "pro" and not is_pro_account(account.role, account.plan):
        from app.core.errors import AppError
        raise AppError("This template is Pro. Upgrade to use it.", code="template_locked", status_code=403)
    portfolio = await portfolio_service.ensure_primary_portfolio(db, str(account.id))
    portfolio.template = tpl.base
    portfolio.accent = tpl.accent
    await db.commit()
    await db.refresh(portfolio)
    return PortfolioOut.model_validate(portfolio)
