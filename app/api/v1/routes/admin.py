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


from app.models import PlatformSettings, PaymentRequest
from app.schemas.billing import SettingsOut, SettingsUpdate, AdminPaymentOut


@router.get("/settings", response_model=SettingsOut)
async def get_settings(db: AsyncSession = Depends(get_db)):
    s = await db.get(PlatformSettings, 1)
    if s is None:
        s = PlatformSettings(id=1)
        db.add(s)
        await db.commit()
        await db.refresh(s)
    return SettingsOut.model_validate(s)


@router.patch("/settings", response_model=SettingsOut)
async def update_settings(payload: SettingsUpdate, db: AsyncSession = Depends(get_db)):
    s = await db.get(PlatformSettings, 1)
    if s is None:
        s = PlatformSettings(id=1)
        db.add(s)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(s, k, v)
    await db.commit()
    await db.refresh(s)
    return SettingsOut.model_validate(s)


@router.get("/payments", response_model=list[AdminPaymentOut])
async def list_payments(db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(
            select(PaymentRequest, Profile.email)
            .join(Profile, Profile.id == PaymentRequest.user_id)
            .order_by(PaymentRequest.created_at.desc())
            .limit(300)
        )
    ).all()
    out = []
    for pr, email in rows:
        item = AdminPaymentOut.model_validate(pr)
        item.email = email
        out.append(item)
    return out


@router.post("/payments/{payment_id}/approve")
async def approve_payment(payment_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    pr = await db.get(PaymentRequest, payment_id)
    if pr is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    pr.status = "approved"
    user = await db.get(Profile, pr.user_id)
    if user is not None:
        user.plan = "pro"
    await db.commit()
    return {"ok": True}


@router.post("/payments/{payment_id}/reject")
async def reject_payment(payment_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    pr = await db.get(PaymentRequest, payment_id)
    if pr is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    pr.status = "rejected"
    await db.commit()
    return {"ok": True}


from sqlalchemy import update as _sql_update

from app.models import CustomTemplate, Message
from app.schemas.extras import (
    CustomTemplateIn,
    CustomTemplateOut,
    CustomTemplateUpdate,
    MessageIn,
    MessageOut,
    ThreadOut,
)

_TEMPLATE_BASES = {"minimal", "bold", "editorial", "studio"}


# ---------- custom templates (admin builder) ----------
@router.get("/templates", response_model=list[CustomTemplateOut])
async def admin_list_templates(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(CustomTemplate).order_by(CustomTemplate.created_at.desc()))).scalars().all()
    return [CustomTemplateOut.model_validate(r) for r in rows]


@router.post("/templates", response_model=CustomTemplateOut, status_code=201)
async def admin_create_template(payload: CustomTemplateIn, db: AsyncSession = Depends(get_db)):
    if payload.plan not in ("free", "pro"):
        raise HTTPException(status_code=422, detail="Invalid plan")
    data = payload.model_dump()
    if not data.get("base"):
        data["base"] = data["key"]
    t = CustomTemplate(**data)
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return CustomTemplateOut.model_validate(t)


@router.patch("/templates/{template_id}", response_model=CustomTemplateOut)
async def admin_update_template(template_id: uuid.UUID, payload: CustomTemplateUpdate, db: AsyncSession = Depends(get_db)):
    t = await db.get(CustomTemplate, template_id)
    if t is None:
        raise HTTPException(status_code=404, detail="Not found")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(t, k, v)
    await db.commit()
    await db.refresh(t)
    return CustomTemplateOut.model_validate(t)


@router.delete("/templates/{template_id}")
async def admin_delete_template(template_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    t = await db.get(CustomTemplate, template_id)
    if t is not None:
        await db.delete(t)
        await db.commit()
    return {"ok": True}


# ---------- messaging (admin side) ----------
@router.get("/messages", response_model=list[ThreadOut])
async def admin_threads(db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(
            select(Message, Profile.email)
            .join(Profile, Profile.id == Message.user_id)
            .order_by(Message.created_at.desc())
            .limit(2000)
        )
    ).all()
    threads: dict = {}
    for m, email in rows:
        t = threads.get(m.user_id)
        if t is None:
            threads[m.user_id] = {"user_id": m.user_id, "email": email, "last_body": m.body, "last_at": m.created_at, "unread": 0}
            t = threads[m.user_id]
        if m.sender == "user" and not m.read:
            t["unread"] += 1
    return [ThreadOut(**t) for t in threads.values()]


@router.get("/messages/{user_id}", response_model=list[MessageOut])
async def admin_thread(user_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(select(Message).where(Message.user_id == user_id).order_by(Message.created_at.asc()))
    ).scalars().all()
    await db.execute(
        _sql_update(Message).where(Message.user_id == user_id, Message.sender == "user", Message.read == False).values(read=True)  # noqa: E712
    )
    await db.commit()
    return [MessageOut.model_validate(m) for m in rows]


@router.post("/messages/{user_id}", response_model=MessageOut, status_code=201)
async def admin_reply(user_id: uuid.UUID, payload: MessageIn, db: AsyncSession = Depends(get_db)):
    m = Message(user_id=user_id, sender="admin", body=payload.body, read=False)
    db.add(m)
    await db.commit()
    await db.refresh(m)
    return MessageOut.model_validate(m)
