from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage

import anyio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import PlatformSettings


def smtp_send(api_key: str, frm: str, to: str, subject: str, html: str) -> None:
    """Send via Resend SMTP (smtp.resend.com:465). Username is literally 'resend',
    password is the Resend API key. SMTP avoids the Cloudflare bot check on the HTTP API."""
    msg = EmailMessage()
    msg["From"] = frm
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content("Please view this email in an HTML-capable client.")
    msg.add_alternative(html, subtype="html")
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.resend.com", 465, context=ctx, timeout=20) as server:
        server.login("resend", api_key)
        server.send_message(msg)


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
        await anyio.to_thread.run_sync(smtp_send, api_key, frm, to, subject, html)
        return True
    except Exception:
        return False


async def notify(db: AsyncSession, user_id, ntype: str, title: str, body: str | None = None):
    from app.models import Notification
    db.add(Notification(user_id=user_id, type=ntype, title=title, body=body))
