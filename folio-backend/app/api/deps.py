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
    return await profile_service.get_or_create_account(db, user)


async def require_admin(account: Profile = Depends(get_current_account)) -> Profile:
    if account.role != "admin":
        raise HTTPException(status_code=403, detail="Admins only.")
    return account
