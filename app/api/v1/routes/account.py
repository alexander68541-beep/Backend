from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, get_current_user
from app.db.session import get_db
from app.schemas.profile import AccountOut
from app.services import profile_service

router = APIRouter(prefix="/me", tags=["account"])


@router.get("", response_model=AccountOut)
async def get_me(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AccountOut:
    account = await profile_service.get_or_create_account(db, user)
    return AccountOut.model_validate(account)
