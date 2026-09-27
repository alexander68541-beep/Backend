from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_account
from app.db.session import get_db
from app.models import PortfolioLike, PortfolioSave, Portfolio, PortfolioProfile, Profile
from app.utils.username import normalize_username

router = APIRouter(prefix="/social", tags=["social"])


async def _published_pid(db: AsyncSession, username: str):
    row = (
        await db.execute(
            select(Portfolio.id).where(
                func.lower(Portfolio.username) == normalize_username(username),
                Portfolio.status == "published",
                Portfolio.deleted_at.is_(None),
            )
        )
    ).first()
    return row[0] if row else None


@router.get("/saved")
async def list_saved(account: Profile = Depends(get_current_account), db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(
            select(Portfolio, PortfolioProfile)
            .join(PortfolioSave, PortfolioSave.portfolio_id == Portfolio.id)
            .join(PortfolioProfile, PortfolioProfile.portfolio_id == Portfolio.id, isouter=True)
            .where(PortfolioSave.user_id == account.id, Portfolio.deleted_at.is_(None))
            .order_by(PortfolioSave.created_at.desc())
        )
    ).all()
    return [
        {
            "username": pf.username, "template": pf.template,
            "display_name": (prof.display_name if prof else None) or pf.username,
            "title": prof.title if prof else None, "tagline": prof.tagline if prof else None,
            "location": prof.location if prof else None, "avatar_url": prof.avatar_url if prof else None,
        }
        for pf, prof in rows
    ]


@router.get("/{username}/status")
async def status(username: str, account: Profile = Depends(get_current_account), db: AsyncSession = Depends(get_db)):
    pid = await _published_pid(db, username)
    if not pid:
        return {"liked": False, "saved": False, "likes": 0}
    liked = (await db.get(PortfolioLike, {"user_id": account.id, "portfolio_id": pid})) is not None
    saved = (await db.get(PortfolioSave, {"user_id": account.id, "portfolio_id": pid})) is not None
    likes = (await db.execute(select(func.count()).select_from(PortfolioLike).where(PortfolioLike.portfolio_id == pid))).scalar_one()
    return {"liked": liked, "saved": saved, "likes": int(likes)}


@router.post("/{username}/like")
async def toggle_like(username: str, account: Profile = Depends(get_current_account), db: AsyncSession = Depends(get_db)):
    pid = await _published_pid(db, username)
    if not pid:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    existing = await db.get(PortfolioLike, {"user_id": account.id, "portfolio_id": pid})
    if existing:
        await db.delete(existing)
        liked = False
    else:
        db.add(PortfolioLike(user_id=account.id, portfolio_id=pid))
        liked = True
    await db.commit()
    likes = (await db.execute(select(func.count()).select_from(PortfolioLike).where(PortfolioLike.portfolio_id == pid))).scalar_one()
    return {"liked": liked, "likes": int(likes)}


@router.post("/{username}/save")
async def toggle_save(username: str, account: Profile = Depends(get_current_account), db: AsyncSession = Depends(get_db)):
    pid = await _published_pid(db, username)
    if not pid:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    existing = await db.get(PortfolioSave, {"user_id": account.id, "portfolio_id": pid})
    if existing:
        await db.delete(existing)
        saved = False
    else:
        db.add(PortfolioSave(user_id=account.id, portfolio_id=pid))
        saved = True
    await db.commit()
    return {"saved": saved}
