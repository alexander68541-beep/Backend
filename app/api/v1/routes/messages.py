from fastapi import APIRouter, Depends
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_account
from app.db.session import get_db
from app.models import Message, Profile
from app.schemas.extras import MessageIn, MessageOut

router = APIRouter(prefix="/messages", tags=["messages"])


@router.get("", response_model=list[MessageOut])
async def my_thread(account: Profile = Depends(get_current_account), db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(
            select(Message).where(Message.user_id == account.id).order_by(Message.created_at.asc())
        )
    ).scalars().all()
    # mark admin messages as read
    await db.execute(
        update(Message).where(Message.user_id == account.id, Message.sender == "admin", Message.read == False).values(read=True)  # noqa: E712
    )
    await db.commit()
    return [MessageOut.model_validate(m) for m in rows]


@router.post("", response_model=MessageOut, status_code=201)
async def send_message(payload: MessageIn, account: Profile = Depends(get_current_account), db: AsyncSession = Depends(get_db)):
    m = Message(user_id=account.id, sender="user", body=payload.body, read=False)
    db.add(m)
    await db.commit()
    await db.refresh(m)
    return MessageOut.model_validate(m)
