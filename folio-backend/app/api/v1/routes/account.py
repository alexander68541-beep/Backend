import urllib.request

import anyio
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import CurrentUser, get_current_user
from app.db.session import get_db
from app.schemas.profile import AccountOut
from app.services import profile_service

router = APIRouter(prefix="/me", tags=["account"])


class AccountUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=120)


@router.get("", response_model=AccountOut)
async def get_me(user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> AccountOut:
    account = await profile_service.get_or_create_account(db, user)
    return AccountOut.model_validate(account)


@router.patch("", response_model=AccountOut)
async def update_me(payload: AccountUpdate, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> AccountOut:
    account = await profile_service.get_or_create_account(db, user)
    if payload.full_name is not None:
        account.full_name = payload.full_name or None
    await db.commit()
    await db.refresh(account)
    return AccountOut.model_validate(account)


@router.delete("")
async def delete_me(user: CurrentUser = Depends(get_current_user)):
    """Delete the auth user via Supabase Admin API. Cascades to profile + all data."""
    if not (settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY):
        raise HTTPException(status_code=500, detail="Account deletion is not configured.")
    url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/admin/users/{user.id}"

    def _do():
        req = urllib.request.Request(
            url,
            method="DELETE",
            headers={
                "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            },
        )
        urllib.request.urlopen(req, timeout=15).read()

    try:
        await anyio.to_thread.run_sync(_do)
    except Exception:
        raise HTTPException(status_code=502, detail="Could not delete account. Try again.")
    return {"ok": True}
