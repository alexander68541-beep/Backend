from __future__ import annotations

import json
import urllib.error
import urllib.request

import anyio

from app.core.config import settings


class VercelError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.message = message
        self.status = status


def configured() -> bool:
    return bool(settings.VERCEL_TOKEN and settings.VERCEL_PROJECT_ID)


def _api(method: str, path: str, body: dict | None = None) -> dict:
    if not configured():
        raise VercelError("Custom domains are not configured on this server.", 503)
    url = f"https://api.vercel.com{path}"
    if settings.VERCEL_TEAM_ID:
        url += ("&" if "?" in url else "?") + f"teamId={settings.VERCEL_TEAM_ID}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={"Authorization": f"Bearer {settings.VERCEL_TOKEN}", "Content-Type": "application/json"},
    )
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        raw = resp.read().decode() or "{}"
        return json.loads(raw)
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read().decode())
            msg = err.get("error", {}).get("message") or f"Vercel error {e.code}"
        except Exception:
            msg = f"Vercel error {e.code}"
        raise VercelError(msg, e.code if e.code in (400, 402, 403, 409) else 502)
    except Exception as e:  # noqa: BLE001
        raise VercelError(f"Could not reach Vercel: {e}", 502)


async def add_domain(domain: str) -> dict:
    return await anyio.to_thread.run_sync(lambda: _api("POST", f"/v10/projects/{settings.VERCEL_PROJECT_ID}/domains", {"name": domain}))


async def get_domain(domain: str) -> dict:
    return await anyio.to_thread.run_sync(lambda: _api("GET", f"/v9/projects/{settings.VERCEL_PROJECT_ID}/domains/{domain}"))


async def get_config(domain: str) -> dict:
    return await anyio.to_thread.run_sync(lambda: _api("GET", f"/v6/domains/{domain}/config"))


async def remove_domain(domain: str) -> None:
    try:
        await anyio.to_thread.run_sync(lambda: _api("DELETE", f"/v9/projects/{settings.VERCEL_PROJECT_ID}/domains/{domain}"))
    except VercelError:
        pass


def dns_instructions(domain: str) -> list[dict]:
    """Standard DNS records to point a domain at Vercel."""
    parts = domain.split(".")
    if len(parts) <= 2:  # apex e.g. example.com
        return [{"type": "A", "name": "@", "value": "76.76.21.21"}]
    sub = ".".join(parts[:-2])  # subdomain label(s)
    return [{"type": "CNAME", "name": sub, "value": "cname.vercel-dns.com"}]
