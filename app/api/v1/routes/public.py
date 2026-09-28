from fastapi import APIRouter, Body, Depends, Request
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
    settings: dict = {}
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
        settings=(pf.settings or {}),
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
    hide = has_feature("remove_branding", (s.plans if s else []), account.role, account.plan)
    return _serialize(data, hide_branding=hide)


@router.get("/usernames")
async def list_published_usernames(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select as _select
    rows = (
        await db.execute(
            _select(Portfolio.username)
            .where(
                Portfolio.status == "published",
                Portfolio.visibility == "public",
                Portfolio.deleted_at.is_(None),
                Portfolio.username.isnot(None),
            )
            .limit(5000)
        )
    ).all()
    return [r[0] for r in rows]


@router.post("/{username}/view")
async def track_view(username: str, request: Request, payload: dict | None = Body(default=None), db: AsyncSession = Depends(get_db)):
    import hashlib
    from datetime import date
    from urllib.parse import urlparse
    from sqlalchemy import select as _select, func as _func
    from sqlalchemy.dialects.postgresql import insert as _pg_insert
    from app.models import ViewDaily, ViewEvent
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
    pid = row[0]
    today = date.today()

    ua = (request.headers.get("user-agent") or "")
    device = "mobile" if ("Mobi" in ua or "iPhone" in ua or "Android" in ua) else "desktop"
    country = request.headers.get("cf-ipcountry") or None
    if country in ("XX", "T1", ""):
        country = None
    ip = request.headers.get("cf-connecting-ip") or (request.client.host if request.client else "")
    visitor_hash = hashlib.sha256(f"{ip}|{today}|folio-salt".encode()).hexdigest()[:32] if ip else None

    ref = None
    raw = (payload or {}).get("referrer") if isinstance(payload, dict) else None
    if raw:
        try:
            ref = urlparse(raw).hostname or None
        except Exception:
            ref = None

    db.add(ViewEvent(portfolio_id=pid, day=today, visitor_hash=visitor_hash, referrer=ref, device=device, country=country))
    stmt = _pg_insert(ViewDaily).values(portfolio_id=pid, day=today, count=1).on_conflict_do_update(
        index_elements=["portfolio_id", "day"], set_={"count": ViewDaily.count + 1},
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
    from app.services.email_service import notify, send_email, email_html

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
        body = (
            f"<p><b>From:</b> {payload.name or 'Someone'} ({payload.email or 'no email'})</p>"
            f"<p style='background:#1a1b28;border-radius:10px;padding:14px'>{payload.message}</p>"
        )
        html = await email_html(db, "New message on your portfolio", body)
        await send_email(db, owner.email, "New message on your portfolio", html)
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




async def build_snapshot(db: AsyncSession, portfolio) -> dict:
    """Serialize the current live data into a snapshot dict for publishing."""
    data = await public_service.get_owner_preview(db, portfolio)
    owner = await db.get(Profile, portfolio.user_id)
    s = await db.get(PlatformSettings, 1)
    pro_features = list(s.pro_features) if s and s.pro_features else []
    hide = bool(owner) and has_feature("remove_branding", (s.plans if s else []), owner.role, owner.plan)
    return _serialize(data, hide_branding=hide).model_dump(mode="json")

def _plan_limits_map(s) -> dict:
    from app.core.limits import entity_limits
    keys = ["free"] + [p.get("key") for p in (s.plans or []) if isinstance(p, dict) and p.get("key")]
    out = {}
    for k in keys:
        out[k] = entity_limits(k, s.plan_limits if s else None)
    return out


@router.get("/resolve-domain")
async def resolve_domain(host: str, db: AsyncSession = Depends(get_db)):
    from app.models import Domain
    from sqlalchemy import func as _func, select as _select
    row = (await db.execute(_select(Domain.username).where(_func.lower(Domain.domain) == host.strip().lower(), Domain.verified == True))).first()  # noqa: E712
    return {"username": row[0] if row and row[0] else None}


@router.get("/branding")
async def branding(db: AsyncSession = Depends(get_db)):
    s = await db.get(PlatformSettings, 1)
    if s is None:
        return {}
    return {
        "site_name": s.site_name, "logo_url": s.logo_url, "favicon_url": s.favicon_url,
        "google_site_verification": s.google_site_verification,
        "seo_keywords": s.seo_keywords, "seo_description": getattr(s, "seo_description", None),
        "footer_text": s.footer_text,
        "contact_email": s.contact_email, "contact_phone": s.contact_phone,
        "contact_whatsapp": s.contact_whatsapp, "contact_address": s.contact_address,
        "contact_note": s.contact_note,
        "currency": s.currency,
        "plans": [p for p in (s.plans or []) if isinstance(p, dict)],
        "limits": _plan_limits_map(s),
    }


@router.get("/explore")
async def explore(q: str | None = None, limit: int = 24, offset: int = 0, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import or_, select as _select
    from app.models import PortfolioProfile

    stmt = (
        _select(Portfolio, PortfolioProfile)
        .join(PortfolioProfile, PortfolioProfile.portfolio_id == Portfolio.id, isouter=True)
        .where(
            Portfolio.status == "published",
            Portfolio.visibility == "public",
            Portfolio.deleted_at.is_(None),
            Portfolio.username.isnot(None),
        )
    )
    if q and q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                PortfolioProfile.display_name.ilike(like),
                PortfolioProfile.title.ilike(like),
                PortfolioProfile.tagline.ilike(like),
                PortfolioProfile.location.ilike(like),
                Portfolio.username.ilike(like),
            )
        )
    stmt = stmt.order_by(Portfolio.published_at.desc().nullslast(), Portfolio.created_at.desc()).limit(min(limit, 48)).offset(max(offset, 0))
    rows = (await db.execute(stmt)).all()
    out = []
    for pf, prof in rows:
        out.append({
            "username": pf.username,
            "template": pf.template,
            "display_name": (prof.display_name if prof else None) or pf.username,
            "title": prof.title if prof else None,
            "tagline": prof.tagline if prof else None,
            "location": prof.location if prof else None,
            "avatar_url": prof.avatar_url if prof else None,
        })
    return out


@router.get("/{username}/social")
async def social_counts(username: str, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import func as _func, select as _select
    from app.models import PortfolioLike
    from app.utils.username import normalize_username
    row = (await db.execute(_select(Portfolio.id).where(_func.lower(Portfolio.username) == normalize_username(username), Portfolio.status == "published"))).first()
    if not row:
        return {"likes": 0}
    likes = (await db.execute(_select(_func.count()).select_from(PortfolioLike).where(PortfolioLike.portfolio_id == row[0]))).scalar_one()
    return {"likes": int(likes)}


async def _full_public_dict(db: AsyncSession, pf, data) -> dict:
    owner = await db.get(Profile, pf.user_id)
    s = await db.get(PlatformSettings, 1)
    hide = bool(owner) and has_feature("remove_branding", (s.plans if s else []), owner.role, owner.plan)
    if pf.published_data:
        d = dict(pf.published_data)
        d["hide_branding"] = hide  # live branding
        return d
    return _serialize(data, hide_branding=hide).model_dump(mode="json")


@router.get("/{username}")
async def get_public_portfolio(username: str, db: AsyncSession = Depends(get_db)):
    data = await public_service.get_published(db, username)
    pf = data["portfolio"]
    if pf.access_password:
        prof = data.get("profile")
        return {"protected": True, "username": pf.username,
                "display_name": (getattr(prof, "display_name", None) or pf.username)}
    return await _full_public_dict(db, pf, data)


@router.post("/{username}/unlock")
async def unlock_portfolio(username: str, payload: dict, db: AsyncSession = Depends(get_db)):
    from fastapi import HTTPException as _HTTPException
    data = await public_service.get_published(db, username)
    pf = data["portfolio"]
    if pf.access_password:
        pw = (payload or {}).get("password", "") if isinstance(payload, dict) else ""
        if pw != pf.access_password:
            raise _HTTPException(status_code=401, detail="Incorrect password")
    return await _full_public_dict(db, pf, data)
