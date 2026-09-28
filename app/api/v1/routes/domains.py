import re
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_account
from app.db.session import get_db
from app.models import Domain, Profile
from app.services import portfolio_service, vercel_service

router = APIRouter(prefix="/portfolio/domains", tags=["domains"])

_DOMAIN_RE = re.compile(r"^(?=.{1,253}$)([a-z0-9](-?[a-z0-9])*\.)+[a-z]{2,}$")


class DomainIn(BaseModel):
    domain: str


def _norm(d: str) -> str:
    d = (d or "").strip().lower()
    d = d.replace("https://", "").replace("http://", "").rstrip("/").split("/")[0]
    if d.startswith("www.") and d.count(".") == 2:
        pass  # keep www subdomains as-is
    return d


def _out(d: Domain) -> dict:
    return {
        "id": str(d.id), "domain": d.domain, "verified": d.verified,
        "verification": d.verification or [],
        "dns": vercel_service.dns_instructions(d.domain),
        "url": f"https://{d.domain}",
    }


@router.get("")
async def list_domains(account: Profile = Depends(get_current_account), db: AsyncSession = Depends(get_db)):
    pf = await portfolio_service.ensure_primary_portfolio(db, str(account.id))
    rows = (await db.execute(select(Domain).where(Domain.portfolio_id == pf.id).order_by(Domain.created_at.desc()))).scalars().all()
    return {"configured": vercel_service.configured(), "domains": [_out(d) for d in rows]}


@router.post("")
async def add_domain(payload: DomainIn, account: Profile = Depends(get_current_account), db: AsyncSession = Depends(get_db)):
    if not vercel_service.configured():
        raise HTTPException(status_code=503, detail="Custom domains aren’t enabled on this server yet.")
    domain = _norm(payload.domain)
    if not _DOMAIN_RE.match(domain):
        raise HTTPException(status_code=422, detail="Enter a valid domain, e.g. yourname.com")
    pf = await portfolio_service.ensure_primary_portfolio(db, str(account.id))
    existing = (await db.execute(select(Domain).where(func.lower(Domain.domain) == domain))).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail="That domain is already connected.")
    try:
        result = await vercel_service.add_domain(domain)
    except vercel_service.VercelError as e:
        raise HTTPException(status_code=e.status, detail=e.message)
    d = Domain(
        portfolio_id=pf.id, user_id=account.id, username=pf.username, domain=domain,
        verified=bool(result.get("verified")), verification=result.get("verification") or [],
    )
    db.add(d)
    await db.commit()
    await db.refresh(d)
    return _out(d)


@router.post("/{domain_id}/refresh")
async def refresh_domain(domain_id: uuid.UUID, account: Profile = Depends(get_current_account), db: AsyncSession = Depends(get_db)):
    d = (await db.execute(select(Domain).where(Domain.id == domain_id, Domain.user_id == account.id))).scalar_one_or_none()
    if d is None:
        raise HTTPException(status_code=404, detail="Domain not found")
    try:
        info = await vercel_service.get_domain(d.domain)
        cfg = await vercel_service.get_config(d.domain)
        d.verified = bool(info.get("verified")) and not bool(cfg.get("misconfigured", True))
        d.verification = info.get("verification") or []
        # keep username fresh
        pf = await portfolio_service.ensure_primary_portfolio(db, str(account.id))
        d.username = pf.username
        await db.commit()
        await db.refresh(d)
    except vercel_service.VercelError as e:
        raise HTTPException(status_code=e.status, detail=e.message)
    return _out(d)


@router.delete("/{domain_id}")
async def delete_domain(domain_id: uuid.UUID, account: Profile = Depends(get_current_account), db: AsyncSession = Depends(get_db)):
    d = (await db.execute(select(Domain).where(Domain.id == domain_id, Domain.user_id == account.id))).scalar_one_or_none()
    if d is None:
        raise HTTPException(status_code=404, detail="Domain not found")
    await vercel_service.remove_domain(d.domain)
    await db.delete(d)
    await db.commit()
    return {"ok": True}
