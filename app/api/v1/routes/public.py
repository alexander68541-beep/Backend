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
)
from app.services import public_service
from pydantic import BaseModel

router = APIRouter(prefix="/public", tags=["public"])


class PublicPortfolioOut(BaseModel):
    username: str | None = None
    template: str = "minimal"
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


@router.get("/{username}", response_model=PublicPortfolioOut)
async def get_public_portfolio(username: str, db: AsyncSession = Depends(get_db)):
    data = await public_service.get_published(db, username)
    pf = data["portfolio"]
    return PublicPortfolioOut(
        username=pf.username,
        template=pf.template,
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
    )
