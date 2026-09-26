from __future__ import annotations

import json
import urllib.error
import urllib.request

import anyio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import PlatformSettings

# A real browser UA — Resend's API is behind Cloudflare, whose "browser integrity
# check" (error 1010) blocks the default Python-urllib User-Agent.
_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"


def http_send(api_key: str, frm: str, to: str, subject: str, html: str) -> None:
    payload = json.dumps({"from": frm, "to": [to], "subject": subject, "html": html}).encode()
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": _UA,
        },
    )
    urllib.request.urlopen(req, timeout=15).read()


async def resolve_creds(db: AsyncSession) -> tuple[str | None, str | None]:
    s = await db.get(PlatformSettings, 1)
    api_key = (s.resend_api_key if s else None) or settings.RESEND_API_KEY
    frm = (s.email_from if s else None) or settings.EMAIL_FROM
    return api_key, frm


async def send_email(db: AsyncSession, to: str | None, subject: str, html: str) -> bool:
    if not to:
        return False
    api_key, frm = await resolve_creds(db)
    if not (api_key and frm):
        return False
    try:
        await anyio.to_thread.run_sync(http_send, api_key, frm, to, subject, html)
        return True
    except Exception:
        return False


async def notify(db: AsyncSession, user_id, ntype: str, title: str, body: str | None = None):
    from app.models import Notification
    db.add(Notification(user_id=user_id, type=ntype, title=title, body=body))
