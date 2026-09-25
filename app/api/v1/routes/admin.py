from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.db.session import get_db
from app.models import Portfolio, Profile

# Whole router requires an admin account.
router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/stats")
async def stats(db: AsyncSession = Depends(get_db)):
    users = (await db.execute(select(func.count()).select_from(Profile))).scalar_one()
    portfolios = (
        await db.execute(
            select(func.count()).select_from(Portfolio).where(Portfolio.deleted_at.is_(None))
        )
    ).scalar_one()
    published = (
        await db.execute(
            select(func.count())
            .select_from(Portfolio)
            .where(Portfolio.status == "published", Portfolio.deleted_at.is_(None))
        )
    ).scalar_one()
    return {"users": int(users), "portfolios": int(portfolios), "published": int(published)}


@router.get("/portfolios")
async def list_portfolios(db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Portfolio, Profile.email)
        .join(Profile, Profile.id == Portfolio.user_id)
        .where(Portfolio.deleted_at.is_(None))
        .order_by(Portfolio.created_at.desc())
        .limit(200)
    )
    rows = (await db.execute(stmt)).all()
    return [
        {
            "id": str(p.id),
            "username": p.username,
            "status": p.status,
            "template": p.template,
            "email": email,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p, email in rows
    ]
