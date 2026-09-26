from fastapi import APIRouter, Depends
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_account
from app.db.session import get_db
from app.models import ContactSubmission, Notification, Profile
from app.schemas.inbox import ContactOut, NotificationOut
from app.services import portfolio_service

router = APIRouter(tags=["inbox"])


@router.get("/notifications", response_model=list[NotificationOut])
async def list_notifications(account: Profile = Depends(get_current_account), db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(
            select(Notification).where(Notification.user_id == account.id).order_by(Notification.created_at.desc()).limit(50)
        )
    ).scalars().all()
    return [NotificationOut.model_validate(n) for n in rows]


@router.get("/notifications/unread-count")
async def unread_count(account: Profile = Depends(get_current_account), db: AsyncSession = Depends(get_db)):
    c = (
        await db.execute(
            select(func.count()).select_from(Notification).where(Notification.user_id == account.id, Notification.read == False)  # noqa: E712
        )
    ).scalar_one()
    return {"count": int(c)}


@router.post("/notifications/read")
async def mark_read(account: Profile = Depends(get_current_account), db: AsyncSession = Depends(get_db)):
    await db.execute(
        update(Notification).where(Notification.user_id == account.id, Notification.read == False).values(read=True)  # noqa: E712
    )
    await db.commit()
    return {"ok": True}


@router.get("/contact", response_model=list[ContactOut])
async def list_contact(account: Profile = Depends(get_current_account), db: AsyncSession = Depends(get_db)):
    portfolio = await portfolio_service.ensure_primary_portfolio(db, str(account.id))
    rows = (
        await db.execute(
            select(ContactSubmission).where(ContactSubmission.portfolio_id == portfolio.id).order_by(ContactSubmission.created_at.desc()).limit(200)
        )
    ).scalars().all()
    await db.execute(
        update(ContactSubmission).where(ContactSubmission.portfolio_id == portfolio.id, ContactSubmission.read == False).values(read=True)  # noqa: E712
    )
    await db.commit()
    return [ContactOut.model_validate(c) for c in rows]
