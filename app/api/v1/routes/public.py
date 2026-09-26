from fastapi import APIRouter, Depends
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
from app.models import PlatformSettings, Profile
from app.services import portfolio_service, public_service
from pydantic import BaseModel

router = APIRouter(prefix="/public", tags=["public"])


class PublicPortfolioOut(BaseModel):
    username: str | None = None
    template: str = "minimal"
    accent: str = "#7c6cff"
    hide_branding: bool = False
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


@router.get("/{username}", response_model=PublicPortfolioOut)
async def get_public_portfolio(username: str, db: AsyncSession = Depends(get_db)):
    data = await public_service.get_published(db, username)
    pf = data["portfolio"]
    owner = await db.get(Profile, pf.user_id)
    s = await db.get(PlatformSettings, 1)
    pro_features = list(s.pro_features) if s and s.pro_features else []
    hide = bool(owner) and has_feature("remove_branding", pro_features, owner.role, owner.plan) and ("remove_branding" in pro_features)
    return _serialize(data, hide_branding=hide)
