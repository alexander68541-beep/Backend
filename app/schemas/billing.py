import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BillingInfoOut(BaseModel):
    plan: str
    pro_price: str | None = None
    currency: str | None = None
    pro_features: list[str] = []
    bep20_address: str | None = None
    nagad_number: str | None = None
    bkash_number: str | None = None
    payment_note: str | None = None


class PaymentSubmitIn(BaseModel):
    method: str = Field(min_length=1, max_length=20)
    amount: str | None = Field(default=None, max_length=40)
    tx_id: str | None = Field(default=None, max_length=200)
    screenshot_url: str | None = Field(default=None, max_length=2048)


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    method: str
    amount: str | None = None
    tx_id: str | None = None
    screenshot_url: str | None = None
    status: str
    created_at: datetime


class AdminPaymentOut(PaymentOut):
    user_id: uuid.UUID
    email: str | None = None


class SettingsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    pro_price: str | None = None
    currency: str | None = None
    pro_features: list[str] = []
    bep20_address: str | None = None
    nagad_number: str | None = None
    bkash_number: str | None = None
    payment_note: str | None = None


class SettingsUpdate(BaseModel):
    pro_price: str | None = None
    currency: str | None = None
    pro_features: list[str] | None = None
    bep20_address: str | None = None
    nagad_number: str | None = None
    bkash_number: str | None = None
    payment_note: str | None = None
