import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PaymentMethod(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    value: str = Field(min_length=1, max_length=300)


class FeatureOut(BaseModel):
    key: str
    label: str
    desc: str
    pro: bool
    has: bool


class BillingInfoOut(BaseModel):
    plan: str
    is_pro: bool
    pro_price: str | None = None
    currency: str | None = None
    payment_note: str | None = None
    payment_methods: list[PaymentMethod] = []
    features: list[FeatureOut] = []


class PaymentSubmitIn(BaseModel):
    method: str = Field(min_length=1, max_length=60)
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
    payment_note: str | None = None
    payment_methods: list[PaymentMethod] = []
    cloudinary_cloud_name: str | None = None
    cloudinary_api_key: str | None = None
    cloudinary_folder: str | None = None
    cloudinary_configured: bool = False


class SettingsUpdate(BaseModel):
    pro_price: str | None = None
    currency: str | None = None
    pro_features: list[str] | None = None
    payment_note: str | None = None
    payment_methods: list[PaymentMethod] | None = None
    cloudinary_cloud_name: str | None = None
    cloudinary_api_key: str | None = None
    cloudinary_api_secret: str | None = None
    cloudinary_folder: str | None = None
