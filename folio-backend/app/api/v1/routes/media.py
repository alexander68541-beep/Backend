import hashlib
import time

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_account
from app.core.config import settings
from app.core.security import CurrentUser, get_current_user
from app.db.session import get_db
from app.models import Media, PlatformSettings, Profile

router = APIRouter(prefix="/media", tags=["media"])


class MediaConfigOut(BaseModel):
    enabled: bool
    accounts: int = 0


class SignOut(BaseModel):
    cloud_name: str
    api_key: str
    timestamp: int
    signature: str
    folder: str
    account: str
    index: int
    has_more: bool


class MediaRecordIn(BaseModel):
    account: str | None = None
    public_id: str | None = None
    url: str | None = None
    format: str | None = None
    width: int | None = None
    height: int | None = None
    bytes: int | None = None


def _accounts(s: PlatformSettings | None) -> list[dict]:
    out: list[dict] = []
    if s is not None and isinstance(s.cloudinary_accounts, list):
        for a in s.cloudinary_accounts:
            if isinstance(a, dict) and a.get("active", True) and a.get("cloud_name") and a.get("api_key") and a.get("api_secret"):
                out.append({
                    "name": a.get("name") or a["cloud_name"],
                    "cloud_name": a["cloud_name"], "api_key": a["api_key"],
                    "api_secret": a["api_secret"], "folder": a.get("folder") or "folio",
                })
    # legacy single account
    if s is not None and s.cloudinary_cloud_name and s.cloudinary_api_key and s.cloudinary_api_secret:
        out.append({"name": "default", "cloud_name": s.cloudinary_cloud_name, "api_key": s.cloudinary_api_key,
                    "api_secret": s.cloudinary_api_secret, "folder": s.cloudinary_folder or "folio"})
    # env fallback
    if settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY and settings.CLOUDINARY_API_SECRET:
        out.append({"name": "env", "cloud_name": settings.CLOUDINARY_CLOUD_NAME, "api_key": settings.CLOUDINARY_API_KEY,
                    "api_secret": settings.CLOUDINARY_API_SECRET, "folder": settings.CLOUDINARY_UPLOAD_FOLDER or "folio"})
    return out


@router.get("/config", response_model=MediaConfigOut)
async def media_config(db: AsyncSession = Depends(get_db)):
    accts = _accounts(await db.get(PlatformSettings, 1))
    return MediaConfigOut(enabled=len(accts) > 0, accounts=len(accts))


@router.post("/sign", response_model=SignOut)
async def sign_upload(
    index: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    accts = _accounts(await db.get(PlatformSettings, 1))
    if not accts:
        raise HTTPException(status_code=503, detail="Media uploads are not configured.")
    if index >= len(accts):
        raise HTTPException(status_code=404, detail="No more upload accounts.")
    a = accts[index]
    timestamp = int(time.time())
    folder = f"{a['folder']}/{user.id}"
    to_sign = f"folder={folder}&timestamp={timestamp}"
    signature = hashlib.sha1((to_sign + a["api_secret"]).encode()).hexdigest()
    return SignOut(
        cloud_name=a["cloud_name"], api_key=a["api_key"], timestamp=timestamp,
        signature=signature, folder=folder, account=a["name"], index=index,
        has_more=(index + 1) < len(accts),
    )


@router.post("/record")
async def record_media(payload: MediaRecordIn, account: Profile = Depends(get_current_account), db: AsyncSession = Depends(get_db)):
    from app.services import portfolio_service
    pf = await portfolio_service.ensure_primary_portfolio(db, str(account.id))
    db.add(Media(
        portfolio_id=pf.id, user_id=account.id, account=payload.account, public_id=payload.public_id,
        url=payload.url, format=payload.format, width=payload.width, height=payload.height, bytes=payload.bytes,
    ))
    await db.commit()
    return {"ok": True}
