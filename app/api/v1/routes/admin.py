from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.services import audit
from app.core.config import settings
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
    portfolio_id: uuid.UUID, payload: AdminStatusIn, actor: Profile = Depends(require_admin), db: AsyncSession = Depends(get_db)
):
    if payload.status not in _VALID_STATUS:
        raise HTTPException(status_code=422, detail="Invalid status")
    pf = await db.get(Portfolio, portfolio_id)
    if pf is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    pf.status = payload.status
    await audit.log(db, actor.email, "portfolio.status", str(portfolio_id), {"status": payload.status})
    await db.commit()
    return {"ok": True, "status": pf.status}


@router.delete("/portfolios/{portfolio_id}", status_code=200)
async def delete_portfolio(portfolio_id: uuid.UUID, actor: Profile = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    pf = await db.get(Portfolio, portfolio_id)
    if pf is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    pf.deleted_at = datetime.now(timezone.utc)
    await audit.log(db, actor.email, "portfolio.delete", str(portfolio_id))
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
    user_id: uuid.UUID, payload: AdminRoleIn, actor: Profile = Depends(require_admin), db: AsyncSession = Depends(get_db)
):
    if payload.role not in _VALID_ROLES:
        raise HTTPException(status_code=422, detail="Invalid role")
    u = await db.get(Profile, user_id)
    if u is None:
        raise HTTPException(status_code=404, detail="User not found")
    u.role = payload.role
    await audit.log(db, actor.email, "user.role", str(user_id), {"role": payload.role})
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
from app.schemas.billing import SettingsOut, SettingsUpdate, AdminPaymentOut, PaymentMethod


def _settings_dict(s) -> dict:
    """Return settings as a plain JSON-safe dict (no response-model validation, so no
    stored value can ever 422). Surfaces legacy single-field config as editable accounts."""
    def _s(v):
        return v if (v is None or isinstance(v, str)) else str(v)

    methods = []
    for m in (s.payment_methods or []):
        if isinstance(m, dict) and m.get("name") is not None and m.get("value") is not None:
            methods.append({"name": str(m["name"]), "value": str(m["value"])})

    ea = [a for a in (s.email_accounts or []) if isinstance(a, dict)]
    if s.email_from and s.resend_api_key and not any(a.get("from") == s.email_from for a in ea):
        ea.append({"name": "default", "from": s.email_from, "api_key": s.resend_api_key, "active": True})
    ca = [a for a in (s.cloudinary_accounts or []) if isinstance(a, dict)]
    if s.cloudinary_cloud_name and s.cloudinary_api_key and s.cloudinary_api_secret and not any(a.get("cloud_name") == s.cloudinary_cloud_name for a in ca):
        ca.append({"name": "default", "cloud_name": s.cloudinary_cloud_name, "api_key": s.cloudinary_api_key,
                   "api_secret": s.cloudinary_api_secret, "folder": s.cloudinary_folder or "folio", "active": True})

    return {
        "pro_price": _s(s.pro_price), "currency": _s(s.currency),
        "pro_features": [str(x) for x in (s.pro_features or [])],
        "payment_note": _s(s.payment_note),
        "payment_methods": methods,
        "cloudinary_cloud_name": _s(s.cloudinary_cloud_name),
        "cloudinary_api_key": _s(s.cloudinary_api_key),
        "cloudinary_folder": _s(s.cloudinary_folder),
        "cloudinary_configured": bool(s.cloudinary_cloud_name and s.cloudinary_api_key and s.cloudinary_api_secret),
        "email_from": _s(s.email_from),
        "email_configured": bool(s.resend_api_key and s.email_from),
        "flags": dict(s.flags or {}),
        "email_enabled": bool(s.email_enabled),
        "email_accounts": ea,
        "cloudinary_accounts": ca,
        "plan_limits": dict(s.plan_limits or {}),
        "plans": [p for p in (s.plans or []) if isinstance(p, dict)],
        "site_name": _s(s.site_name), "logo_url": _s(s.logo_url), "favicon_url": _s(s.favicon_url),
        "google_site_verification": _s(s.google_site_verification), "seo_keywords": _s(s.seo_keywords),
        "seo_description": _s(getattr(s, "seo_description", None)), "footer_text": _s(s.footer_text),
        "contact_email": _s(s.contact_email), "contact_phone": _s(s.contact_phone),
        "contact_whatsapp": _s(s.contact_whatsapp), "contact_address": _s(s.contact_address),
        "contact_note": _s(s.contact_note),
    }


@router.get("/settings")
async def get_settings(db: AsyncSession = Depends(get_db)):
    import logging
    try:
        s = await db.get(PlatformSettings, 1)
        if s is None:
            s = PlatformSettings(id=1)
            db.add(s)
            await db.commit()
            await db.refresh(s)
        return _settings_dict(s)
    except Exception as e:  # noqa: BLE001
        logging.getLogger("folio").exception("get_settings failed: %s", e)
        return {
            "pro_price": None, "currency": None, "pro_features": [], "payment_note": None,
            "payment_methods": [], "cloudinary_cloud_name": None, "cloudinary_api_key": None,
            "cloudinary_folder": None, "cloudinary_configured": False, "email_from": None,
            "email_configured": False, "flags": {}, "email_enabled": True, "email_accounts": [],
            "cloudinary_accounts": [], "plan_limits": {}, "plans": [], "site_name": None, "logo_url": None, "favicon_url": None, "google_site_verification": None, "seo_keywords": None, "seo_description": None, "footer_text": None, "contact_email": None, "contact_phone": None, "contact_whatsapp": None, "contact_address": None, "contact_note": None, "_error": str(e)[:200],
        }


@router.patch("/settings")
async def update_settings(payload: SettingsUpdate, db: AsyncSession = Depends(get_db)):
    s = await db.get(PlatformSettings, 1)
    if s is None:
        s = PlatformSettings(id=1)
        db.add(s)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(s, k, v)
    await db.commit()
    await db.refresh(s)
    return _settings_dict(s)


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
async def approve_payment(payment_id: uuid.UUID, actor: Profile = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    pr = await db.get(PaymentRequest, payment_id)
    if pr is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    pr.status = "approved"
    user = await db.get(Profile, pr.user_id)
    if user is not None:
        user.plan = pr.plan or "pro"
        from datetime import datetime, timezone, timedelta
        if pr.period == "monthly":
            user.plan_expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        elif pr.period == "yearly":
            user.plan_expires_at = datetime.now(timezone.utc) + timedelta(days=365)
        else:
            user.plan_expires_at = None  # lifetime = no expiry
        await audit.log(db, actor.email, "payment.approve", str(payment_id), {"user": user.email, "plan": pr.plan, "period": pr.period})
        from app.services.email_service import notify, send_email, email_html
        await notify(db, user.id, "billing", "Payment approved", "You're now on Pro — enjoy all premium features!")
        await db.commit()
        if user.email:
            _plan = (pr.plan or "pro").capitalize()
            _body = f"<p>Your payment has been approved. Your account is now <b>{_plan}</b> — enjoy your unlocked features!</p>"
            _html = await email_html(db, "Payment approved 🎉", _body, cta_text="Open dashboard", cta_url=(settings.APP_URL.rstrip('/') + '/dashboard' if settings.APP_URL else None))
            await send_email(db, user.email, "Your payment was approved", _html)
    else:
        await db.commit()
    return {"ok": True}


@router.post("/payments/{payment_id}/reject")
async def reject_payment(payment_id: uuid.UUID, actor: Profile = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    pr = await db.get(PaymentRequest, payment_id)
    if pr is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    pr.status = "rejected"
    await audit.log(db, actor.email, "payment.reject", str(payment_id))
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
async def admin_delete_template(template_id: uuid.UUID, actor: Profile = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    t = await db.get(CustomTemplate, template_id)
    if t is not None:
        await audit.log(db, actor.email, "template.delete", str(template_id), {"name": t.name})
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


from app.models import AuditLog, Report


@router.get("/audit")
async def list_audit(limit: int = 50, offset: int = 0, db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(min(limit, 100)).offset(offset))
    ).scalars().all()
    return [
        {"id": str(r.id), "actor_email": r.actor_email, "action": r.action, "target": r.target,
         "meta": r.meta, "created_at": r.created_at.isoformat() if r.created_at else None}
        for r in rows
    ]


@router.get("/reports")
async def list_reports(status: str | None = None, limit: int = 50, offset: int = 0, db: AsyncSession = Depends(get_db)):
    q = select(Report).order_by(Report.created_at.desc())
    if status:
        q = q.where(Report.status == status)
    rows = (await db.execute(q.limit(min(limit, 100)).offset(offset))).scalars().all()
    return [
        {"id": str(r.id), "portfolio_id": str(r.portfolio_id) if r.portfolio_id else None, "username": r.username,
         "reason": r.reason, "detail": r.detail, "status": r.status,
         "created_at": r.created_at.isoformat() if r.created_at else None}
        for r in rows
    ]


@router.post("/reports/{report_id}/resolve")
async def resolve_report(report_id: uuid.UUID, action: str, actor: Profile = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    r = await db.get(Report, report_id)
    if r is None:
        raise HTTPException(status_code=404, detail="Report not found")
    if action == "suspend" and r.portfolio_id:
        pf = await db.get(Portfolio, r.portfolio_id)
        if pf is not None:
            pf.status = "suspended"
        r.status = "actioned"
        await audit.log(db, actor.email, "report.suspend", str(report_id), {"portfolio": str(r.portfolio_id)})
    else:
        r.status = "dismissed"
        await audit.log(db, actor.email, "report.dismiss", str(report_id))
    await db.commit()
    return {"ok": True}


@router.post("/test-email")
async def test_email(actor: Profile = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    """Attempt a real send to the admin's own email and return the exact result/error."""
    import anyio

    from app.core.config import settings as _settings
    from app.models import PlatformSettings

    s = await db.get(PlatformSettings, 1)
    api_key = (s.resend_api_key if s else None) or _settings.RESEND_API_KEY
    frm = (s.email_from if s else None) or _settings.EMAIL_FROM

    if not api_key:
        return {"ok": False, "error": "No Resend API key set (Admin → Email)."}
    if not frm:
        return {"ok": False, "error": "No 'From' address set (Admin → Email)."}
    if not actor.email:
        return {"ok": False, "error": "Your admin account has no email address."}

    import urllib.error
    from app.services.email_service import http_send

    def _do():
        try:
            http_send(api_key, frm, actor.email, "Folio — test email",
                      "<p>✅ Test email from Folio. If you got this, email works.</p>")
            return True, "sent"
        except urllib.error.HTTPError as e:
            try:
                body = e.read().decode()[:400]
            except Exception:
                body = ""
            return False, f"HTTP {e.code}: {body}"
        except Exception as e:  # noqa: BLE001
            return False, f"{type(e).__name__}: {str(e)[:400]}"

    ok, detail = await anyio.to_thread.run_sync(_do)
    return {"ok": ok, "detail": detail, "to": actor.email, "from": frm}


from pydantic import BaseModel as _BaseModel


class TemplateMigrateIn(_BaseModel):
    from_key: str
    to_key: str


@router.post("/templates/migrate")
async def migrate_templates(payload: TemplateMigrateIn, actor: Profile = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    from sqlalchemy import update as _update
    res = await db.execute(
        _update(Portfolio).where(Portfolio.template == payload.from_key).values(template=payload.to_key)
    )
    await audit.log(db, actor.email, "template.migrate", None, {"from": payload.from_key, "to": payload.to_key})
    await db.commit()
    return {"ok": True, "migrated": res.rowcount}
