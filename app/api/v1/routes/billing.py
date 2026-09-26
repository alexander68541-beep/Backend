from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_account
from app.db.session import get_db
from app.models import PaymentRequest, PlatformSettings, Profile
from app.core.features import FEATURE_CATALOG, has_feature, is_pro_account
from app.schemas.billing import BillingInfoOut, FeatureOut, PaymentMethod, PaymentOut, PaymentSubmitIn

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/info", response_model=BillingInfoOut)
async def billing_info(
    account: Profile = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    s = await db.get(PlatformSettings, 1)
    pro_features = list(s.pro_features) if s and s.pro_features else []
    methods = [PaymentMethod(**m) for m in (s.payment_methods or [])] if s else []
    features = [
        FeatureOut(
            key=f["key"], label=f["label"], desc=f["desc"],
            pro=(f["key"] in pro_features),
            has=has_feature(f["key"], pro_features, account.role, account.plan),
        )
        for f in FEATURE_CATALOG
    ]
    return BillingInfoOut(
        plan=account.plan,
        is_pro=is_pro_account(account.role, account.plan),
        pro_price=(s.pro_price if s else None),
        currency=(s.currency if s else None),
        payment_note=(s.payment_note if s else None),
        payment_methods=methods,
        features=features,
    )


@router.post("/submit", response_model=PaymentOut, status_code=201)
async def submit_payment(
    payload: PaymentSubmitIn,
    account: Profile = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    pr = PaymentRequest(
        user_id=account.id,
        method=payload.method,
        amount=payload.amount,
        tx_id=payload.tx_id,
        screenshot_url=payload.screenshot_url,
    )
    db.add(pr)
    await db.commit()
    await db.refresh(pr)
    return PaymentOut.model_validate(pr)


@router.get("/my", response_model=list[PaymentOut])
async def my_payments(
    account: Profile = Depends(get_current_account),
    db: AsyncSession = Depends(get_db),
):
    rows = (
        await db.execute(
            select(PaymentRequest)
            .where(PaymentRequest.user_id == account.id)
            .order_by(PaymentRequest.created_at.desc())
        )
    ).scalars().all()
    return [PaymentOut.model_validate(r) for r in rows]
