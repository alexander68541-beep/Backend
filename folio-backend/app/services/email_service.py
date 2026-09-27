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


def _accounts_from_settings(s) -> tuple[bool, list[tuple[str, str]]]:
    """Return (enabled, [(from, api_key), ...]) — multiple accounts tried in order."""
    if s is not None and s.email_enabled is False:
        return False, []
    out: list[tuple[str, str]] = []
    if s is not None and isinstance(s.email_accounts, list):
        for a in s.email_accounts:
            if isinstance(a, dict) and a.get("active", True) and a.get("api_key") and a.get("from"):
                out.append((a["from"], a["api_key"]))
    # legacy single fields + env, as final fallbacks
    key = (s.resend_api_key if s else None) or settings.RESEND_API_KEY
    frm = (s.email_from if s else None) or settings.EMAIL_FROM
    if key and frm and (frm, key) not in out:
        out.append((frm, key))
    return True, out


async def send_email(db: AsyncSession, to: str | None, subject: str, html: str) -> bool:
    if not to:
        return False
    s = await db.get(PlatformSettings, 1)
    enabled, accounts = _accounts_from_settings(s)
    if not enabled or not accounts:
        return False
    for frm, api_key in accounts:
        try:
            await anyio.to_thread.run_sync(http_send, api_key, frm, to, subject, html)
            return True
        except Exception:
            continue  # fall back to the next account
    return False


async def notify(db: AsyncSession, user_id, ntype: str, title: str, body: str | None = None):
    from app.models import Notification
    db.add(Notification(user_id=user_id, type=ntype, title=title, body=body))
