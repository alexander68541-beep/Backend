from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession


async def log(db: AsyncSession, actor_email: str | None, action: str, target: str | None = None, meta: dict | None = None):
    from app.models import AuditLog
    db.add(AuditLog(actor_email=actor_email, action=action, target=target, meta=meta or {}))
