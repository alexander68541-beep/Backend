import hashlib
import time

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.config import settings
from app.core.security import CurrentUser, get_current_user

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


def _cloudinary_ready() -> bool:
    return bool(
        settings.CLOUDINARY_CLOUD_NAME
        and settings.CLOUDINARY_API_KEY
        and settings.CLOUDINARY_API_SECRET
    )


@router.get("/config", response_model=MediaConfigOut)
async def media_config():
    return MediaConfigOut(
        enabled=_cloudinary_ready(),
        cloud_name=settings.CLOUDINARY_CLOUD_NAME or None,
    )


@router.post("/sign", response_model=SignOut)
async def sign_upload(user: CurrentUser = Depends(get_current_user)):
    """Return signed params for a direct browser->Cloudinary upload. The API secret
    never leaves the server. Files are scoped to a per-user folder."""
    from fastapi import HTTPException

    if not _cloudinary_ready():
        raise HTTPException(status_code=503, detail="Media uploads are not configured.")

    timestamp = int(time.time())
    folder = f"{settings.CLOUDINARY_UPLOAD_FOLDER}/{user.id}"
    # Cloudinary signature: sha1 of sorted "key=value" of the params being signed + api_secret
    to_sign = f"folder={folder}&timestamp={timestamp}"
    signature = hashlib.sha1((to_sign + settings.CLOUDINARY_API_SECRET).encode()).hexdigest()

    return SignOut(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        timestamp=timestamp,
        signature=signature,
        folder=folder,
    )
