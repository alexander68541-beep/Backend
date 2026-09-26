from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.portfolio import (
    PortfolioProfileOut,
    PortfolioOut,
)
from app.schemas.portfolio_data import (
    AchievementOut,
    CertificationOut,
    EducationOut,
    ExperienceOut,
    ProjectOut,
    PublicationOut,
    ServiceOut,
    SkillOut,
    SocialLinkOut,
    TestimonialOut,
    GalleryOut,
    VideoOut,
)
from app.core.security import CurrentUser, get_current_user
from app.api.deps import get_current_account
from app.core.features import has_feature
from app.core.config import settings
from app.core.rate_limit import limiter
from app.schemas.inbox import ContactIn
from app.models import ContactSubmission, PlatformSettings, Portfolio, Profile
from app.services import portfolio_service, public_service
from pydantic import BaseModel

router = APIRouter(prefix="/public", tags=["public"])


class PublicPortfolioOut(BaseModel):
    username: str | None = None
    template: str = "minimal"
    accent: str = "#7c6cff"
    hide_branding: bool = False
    seo_title: str | None = None
    seo_description: str | None = None
    seo_image: str | None = None
    profile: PortfolioProfileOut | None = None
    projects: list[ProjectOut] = []
    skills: list[SkillOut] = []
    experience: list[ExperienceOut] = []
    education: list[EducationOut] = []
    links: list[SocialLinkOut] = []
    services: list[ServiceOut] = []
    certifications: list[CertificationOut] = []
    achievements: list[AchievementOut] = []
    testimonials: list[TestimonialOut] = []
    publications: list[PublicationOut] = []
    gallery: list[GalleryOut] = []
    videos: list[VideoOut] = []


def _serialize(data, hide_branding: bool = False) -> "PublicPortfolioOut":
    pf = data["portfolio"]
    return PublicPortfolioOut(
        username=pf.username,
        template=pf.template,
        accent=pf.accent,
        hide_branding=hide_branding,
        seo_title=pf.seo_title,
        seo_description=pf.seo_description,
        seo_image=pf.seo_image,
        profile=PortfolioProfileOut.model_validate(data["profile"]) if data["profile"] else None,
        projects=[ProjectOut.model_validate(x) for x in data["projects"]],
        skills=[SkillOut.model_validate(x) for x in data["skills"]],
        experience=[ExperienceOut.model_validate(x) for x in data["experience"]],
        education=[EducationOut.model_validate(x) for x in data["education"]],
        links=[SocialLinkOut.model_validate(x) for x in data["links"]],
        services=[ServiceOut.model_validate(x) for x in data["services"]],
        certifications=[CertificationOut.model_validate(x) for x in data["certifications"]],
        achievements=[AchievementOut.model_validate(x) for x in data["achievements"]],
        testimonials=[TestimonialOut.model_validate(x) for x in data["testimonials"]],
        publications=[PublicationOut.model_validate(x) for x in data["publications"]],
        gallery=[GalleryOut.model_validate(x) for x in data["gallery"]],
        videos=[VideoOut.model_validate(x) for x in data["videos"]],
    )


@router.get("/preview", response_model=PublicPortfolioOut)
async def preview_portfolio(
    account = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    portfolio = await portfolio_service.ensure_primary_portfolio(db, str(account.id))
    data = await public_service.get_owner_preview(db, portfolio)
    s = await db.get(PlatformSettings, 1)
    pro_features = list(s.pro_features) if s and s.pro_features else []
    hide = has_feature("remove_branding", pro_features, account.role, account.plan) and ("remove_branding" in pro_features)
    return _serialize(data, hide_branding=hide)


@router.get("/usernames")
async def list_published_usernames(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select as _select
    rows = (
        await db.execute(
            _select(Portfolio.username)
            .where(
                Portfolio.status == "published",
                Portfolio.deleted_at.is_(None),
                Portfolio.username.isnot(None),
            )
            .limit(5000)
        )
    ).all()
    return [r[0] for r in rows]


@router.post("/{username}/view")
async def track_view(username: str, db: AsyncSession = Depends(get_db)):
    from datetime import date
    from sqlalchemy import select as _select, func as _func
    from sqlalchemy.dialects.postgresql import insert as _pg_insert
    from app.models import ViewDaily
    from app.utils.username import normalize_username

    row = (
        await db.execute(
            _select(Portfolio.id).where(
                _func.lower(Portfolio.username) == normalize_username(username),
                Portfolio.status == "published",
                Portfolio.deleted_at.is_(None),
            )
        )
    ).first()
    if row is None:
        return {"ok": False}
    stmt = _pg_insert(ViewDaily).values(portfolio_id=row[0], day=date.today(), count=1)
    stmt = stmt.on_conflict_do_update(
        index_elements=["portfolio_id", "day"],
        set_={"count": ViewDaily.count + 1},
    )
    await db.execute(stmt)
    await db.commit()
    return {"ok": True}


@router.post("/{username}/contact")
@limiter.limit("6/minute")
async def contact(request: Request, username: str, payload: ContactIn, db: AsyncSession = Depends(get_db)):
    # honeypot: if a bot filled the hidden field, silently accept without storing
    if payload.website:
        return {"ok": True}
    _s = await db.get(PlatformSettings, 1)
    if _s and isinstance(_s.flags, dict) and _s.flags.get("enable_contact") is False:
        return {"ok": False, "disabled": True}
    from sqlalchemy import func as _func, select as _select
    from app.utils.username import normalize_username
    from app.services.email_service import notify, send_email

    row = (
        await db.execute(
            _select(Portfolio).where(
                _func.lower(Portfolio.username) == normalize_username(username),
                Portfolio.status == "published",
                Portfolio.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if row is None:
        return {"ok": False}

    ip = request.client.host if request.client else None
    db.add(ContactSubmission(portfolio_id=row.id, name=payload.name, email=payload.email, message=payload.message, ip=ip))
    await notify(db, row.user_id, "contact", "New contact message",
                 f"{payload.name or 'Someone'} sent you a message.")
    await db.commit()

    owner = await db.get(Profile, row.user_id)
    if owner and owner.email:
        html = (
            "<p>You received a new message on your Folio portfolio.</p>"
            f"<p><b>From:</b> {payload.name or ''} ({payload.email or ''})</p>"
            f"<p>{payload.message}</p>"
        )
        await send_email(db, owner.email, "New message on your Folio portfolio", html)
    return {"ok": True}


@router.get("/flags")
async def public_flags(db: AsyncSession = Depends(get_db)):
    s = await db.get(PlatformSettings, 1)
    return (s.flags if s and isinstance(s.flags, dict) else {})


@router.post("/{username}/report")
@limiter.limit("4/minute")
async def report_portfolio(request: Request, username: str, payload: dict, db: AsyncSession = Depends(get_db)):
    from app.models import Report
    from app.utils.username import normalize_username
    from sqlalchemy import func as _func, select as _select

    reason = str(payload.get("reason") or "").strip()[:120]
    detail = str(payload.get("detail") or "").strip()[:2000] or None
    if not reason:
        return {"ok": False}
    name = normalize_username(username)
    row = (await db.execute(_select(Portfolio.id).where(_func.lower(Portfolio.username) == name))).first()
    db.add(Report(portfolio_id=(row[0] if row else None), username=name, reason=reason, detail=detail))
    await db.commit()
    return {"ok": True}


@router.get("/{username}", response_model=PublicPortfolioOut)
async def get_public_portfolio(username: str, db: AsyncSession = Depends(get_db)):
    data = await public_service.get_published(db, username)
    pf = data["portfolio"]
    owner = await db.get(Profile, pf.user_id)
    s = await db.get(PlatformSettings, 1)
    pro_features = list(s.pro_features) if s and s.pro_features else []
    hide = bool(owner) and has_feature("remove_branding", pro_features, owner.role, owner.plan) and ("remove_branding" in pro_features)
    return _serialize(data, hide_branding=hide)
