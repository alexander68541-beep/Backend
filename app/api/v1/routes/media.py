import hashlib
import time

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import CurrentUser, get_current_user
from app.db.session import get_db
from app.models import PlatformSettings

router = APIRouter(prefix="/media", tags=["media"])


class MediaConfigOut(BaseModel):
    enabled: bool
    cloud_name: str | None = None


class SignOut(BaseModel):
    cloud_name: str
    api_key: str
    timestamp: int
    signature: str
    folder: str


async def _creds(db: AsyncSession):
    s = await db.get(PlatformSettings, 1)
    cloud = (s.cloudinary_cloud_name if s else None) or settings.CLOUDINARY_CLOUD_NAME
    key = (s.cloudinary_api_key if s else None) or settings.CLOUDINARY_API_KEY
    secret = (s.cloudinary_api_secret if s else None) or settings.CLOUDINARY_API_SECRET
    folder = (s.cloudinary_folder if s else None) or settings.CLOUDINARY_UPLOAD_FOLDER or "folio"
    return cloud, key, secret, folder


@router.get("/config", response_model=MediaConfigOut)
async def media_config(db: AsyncSession = Depends(get_db)):
    cloud, key, secret, _ = await _creds(db)
    return MediaConfigOut(enabled=bool(cloud and key and secret), cloud_name=cloud or None)


@router.post("/sign", response_model=SignOut)
async def sign_upload(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cloud, key, secret, base_folder = await _creds(db)
    if not (cloud and key and secret):
        raise HTTPException(status_code=503, detail="Media uploads are not configured.")
    timestamp = int(time.time())
    folder = f"{base_folder}/{user.id}"
    to_sign = f"folder={folder}&timestamp={timestamp}"
    signature = hashlib.sha1((to_sign + secret).encode()).hexdigest()
    return SignOut(cloud_name=cloud, api_key=key, timestamp=timestamp, signature=signature, folder=folder)
