from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.rate_limit import limiter
from app.core.security import get_current_user
from app.db.session import get_db
from app.schemas.common import AvailabilityOut
from app.services import username_service

router = APIRouter(prefix="/username", tags=["username"])


@router.get("/check", response_model=AvailabilityOut)
@limiter.limit(settings.RATE_LIMIT_USERNAME_CHECK)
async def check_username(
    request: Request,
    username: str = Query(min_length=1, max_length=60),
    _=Depends(get_current_user),  # auth required to avoid enumeration by anonymous bots
    db: AsyncSession = Depends(get_db),
) -> AvailabilityOut:
    result = await username_service.check_availability(db, username)
    return AvailabilityOut(**result)
