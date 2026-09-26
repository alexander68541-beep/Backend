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
    SeoUpdateIn,
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
    from sqlalchemy import select as _select
    from app.core.errors import AppError

    key = payload.template
    row = (
        await db.execute(
            _select(CustomTemplate).where(CustomTemplate.key == key, CustomTemplate.is_published == True).limit(1)  # noqa: E712
        )
    ).scalar_one_or_none()

    # Must be a known built-in or an active listed template.
    if row is None and key not in portfolio_service.ALLOWED_TEMPLATES:
        raise AppError("Template not found or inactive.", code="not_found", status_code=404)

    pro_needed = (row is not None and row.plan == "pro") or (key in portfolio_service.PRO_TEMPLATES)
    if pro_needed and not is_pro_account(account.role, account.plan):
        raise AppError("This is a Pro template. Upgrade to use it.", code="template_locked", status_code=403)

    portfolio = await portfolio_service.ensure_primary_portfolio(db, str(account.id))
    portfolio = await portfolio_service.update_template(db, portfolio, key)
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


@router.patch("/seo", response_model=PortfolioOut)
async def update_seo(
    payload: SeoUpdateIn,
    account: Profile = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
) -> PortfolioOut:
    portfolio = await portfolio_service.ensure_primary_portfolio(db, str(account.id))
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(portfolio, field, (value or None))
    await db.commit()
    await db.refresh(portfolio)
    return PortfolioOut.model_validate(portfolio)


@router.get("/analytics")
async def get_analytics(
    account: Profile = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    from datetime import date, timedelta
    from sqlalchemy import select as _select, func as _func
    from app.models import ViewDaily

    portfolio = await portfolio_service.ensure_primary_portfolio(db, str(account.id))
    today = date.today()
    start = today - timedelta(days=29)

    rows = (
        await db.execute(
            _select(ViewDaily.day, ViewDaily.count).where(
                ViewDaily.portfolio_id == portfolio.id, ViewDaily.day >= start
            )
        )
    ).all()
    by_day = {r[0]: r[1] for r in rows}
    series = []
    for i in range(30):
        d = start + timedelta(days=i)
        series.append({"day": d.isoformat(), "count": int(by_day.get(d, 0))})

    total = (
        await db.execute(
            _select(_func.coalesce(_func.sum(ViewDaily.count), 0)).where(ViewDaily.portfolio_id == portfolio.id)
        )
    ).scalar_one()
    last7 = sum(s["count"] for s in series[-7:])
    return {"series": series, "total": int(total), "today": int(by_day.get(today, 0)), "last7": int(last7)}
