from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models import (
    Achievement,
    Certification,
    Education,
    Experience,
    Portfolio,
    PortfolioProfile,
    Project,
    Publication,
    Service,
    Skill,
    SocialLink,
    Testimonial,
)
from app.utils.username import normalize_username


async def get_published(db: AsyncSession, username: str) -> dict:
    name = normalize_username(username)
    stmt = select(Portfolio).where(
        func.lower(Portfolio.username) == name,
        Portfolio.status == "published",
        Portfolio.deleted_at.is_(None),
    )
    portfolio = (await db.execute(stmt)).scalar_one_or_none()
    if portfolio is None:
        raise AppError("Portfolio not found", code="not_found", status_code=404)

    profile = await db.get(PortfolioProfile, portfolio.id)

    async def _items(model):
        rows = await db.execute(
            select(model)
            .where(model.portfolio_id == portfolio.id)
            .order_by(model.position.asc(), model.created_at.asc())
        )
        return list(rows.scalars().all())

    return {
        "portfolio": portfolio,
        "profile": profile,
        "projects": await _items(Project),
        "skills": await _items(Skill),
        "experience": await _items(Experience),
        "education": await _items(Education),
        "links": await _items(SocialLink),
        "services": await _items(Service),
        "certifications": await _items(Certification),
        "achievements": await _items(Achievement),
        "testimonials": await _items(Testimonial),
        "publications": await _items(Publication),
    }
