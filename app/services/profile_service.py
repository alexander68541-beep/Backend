from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser
from app.models import Profile


async def get_or_create_account(db: AsyncSession, user: CurrentUser) -> Profile:
    """The DB trigger normally creates the profile on signup. This is a safety net
    so the API still works if a row is missing for any reason."""
    uid = uuid.UUID(user.id)
    profile = await db.get(Profile, uid)
    if profile is None:
        profile = Profile(id=uid, email=user.email)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
    return profile


async def get_account(db: AsyncSession, user_id: str) -> Profile | None:
    return await db.get(Profile, uuid.UUID(user_id))
