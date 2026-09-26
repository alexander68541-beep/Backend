from __future__ import annotations

import json
import urllib.request

import anyio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import PlatformSettings


async def send_email(db: AsyncSession, to: str | None, subject: str, html: str) -> bool:
    if not to:
        return False
    s = await db.get(PlatformSettings, 1)
    api_key = (s.resend_api_key if s else None) or settings.RESEND_API_KEY
    frm = (s.email_from if s else None) or settings.EMAIL_FROM
    if not (api_key and frm):
        return False
    payload = json.dumps({"from": frm, "to": [to], "subject": subject, "html": html}).encode()

    def _do():
        req = urllib.request.Request(
            "https://api.resend.com/emails",
            data=payload,
            method="POST",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=15).read()

    try:
        await anyio.to_thread.run_sync(_do)
        return True
    except Exception:
        return False


async def notify(db: AsyncSession, user_id, ntype: str, title: str, body: str | None = None):
    from app.models import Notification
    db.add(Notification(user_id=user_id, type=ntype, title=title, body=body))
