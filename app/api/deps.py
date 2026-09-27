from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, get_current_user
from app.db.session import get_db
from app.models import Profile
from app.services import profile_service


async def get_current_account(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Profile:
    account = await profile_service.get_or_create_account(db, user)
    await _enforce_plan_expiry(db, account)
    return account


async def require_admin(account: Profile = Depends(get_current_account)) -> Profile:
    if account.role != "admin":
        raise HTTPException(status_code=403, detail="Admins only.")
    return account


async def _enforce_plan_expiry(db, account) -> None:
    """Auto-downgrade to free when a timed subscription has expired."""
    exp = getattr(account, "plan_expires_at", None)
    if exp is None or (getattr(account, "plan", "free") or "free") == "free":
        return
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    exp_aware = exp if exp.tzinfo else exp.replace(tzinfo=timezone.utc)
    if exp_aware <= now:
        account.plan = "free"
        account.plan_expires_at = None
        await db.commit()
