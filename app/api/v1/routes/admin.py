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


import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from pydantic import BaseModel, Field

from app.models import ReservedUsername

_VALID_STATUS = {"draft", "published", "unpublished", "suspended", "archived"}
_VALID_ROLES = {"user", "admin", "moderator", "support", "content_manager", "finance"}


class AdminStatusIn(BaseModel):
    status: str


class AdminRoleIn(BaseModel):
    role: str


class ReservedIn(BaseModel):
    name: str = Field(min_length=1, max_length=60)


@router.patch("/portfolios/{portfolio_id}/status")
async def set_portfolio_status(
    portfolio_id: uuid.UUID, payload: AdminStatusIn, db: AsyncSession = Depends(get_db)
):
    if payload.status not in _VALID_STATUS:
        raise HTTPException(status_code=422, detail="Invalid status")
    pf = await db.get(Portfolio, portfolio_id)
    if pf is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    pf.status = payload.status
    await db.commit()
    return {"ok": True, "status": pf.status}


@router.delete("/portfolios/{portfolio_id}", status_code=200)
async def delete_portfolio(portfolio_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    pf = await db.get(Portfolio, portfolio_id)
    if pf is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    pf.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return {"ok": True}


@router.get("/users")
async def list_users(db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(select(Profile).order_by(Profile.created_at.desc()).limit(300))
    ).scalars().all()
    return [{"id": str(u.id), "email": u.email, "role": u.role} for u in rows]


@router.patch("/users/{user_id}/role")
async def set_user_role(
    user_id: uuid.UUID, payload: AdminRoleIn, db: AsyncSession = Depends(get_db)
):
    if payload.role not in _VALID_ROLES:
        raise HTTPException(status_code=422, detail="Invalid role")
    u = await db.get(Profile, user_id)
    if u is None:
        raise HTTPException(status_code=404, detail="User not found")
    u.role = payload.role
    await db.commit()
    return {"ok": True, "role": u.role}


@router.get("/reserved")
async def list_reserved(db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(select(ReservedUsername).order_by(ReservedUsername.name).limit(1000))
    ).scalars().all()
    return [{"name": r.name, "note": r.note} for r in rows]


@router.post("/reserved", status_code=201)
async def add_reserved(payload: ReservedIn, db: AsyncSession = Depends(get_db)):
    name = payload.name.strip().lower()
    if await db.get(ReservedUsername, name) is None:
        db.add(ReservedUsername(name=name, note="admin"))
        await db.commit()
    return {"ok": True, "name": name}


@router.delete("/reserved/{name}")
async def remove_reserved(name: str, db: AsyncSession = Depends(get_db)):
    r = await db.get(ReservedUsername, name.strip().lower())
    if r is not None:
        await db.delete(r)
        await db.commit()
    return {"ok": True}
