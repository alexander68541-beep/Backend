import uuid
from datetime import datetime

from sqlalchemy import Integer, String, Text, text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PlatformSettings(Base):
    __tablename__ = "platform_settings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, server_default=text("1"))
    pro_price: Mapped[str | None] = mapped_column(Text)
    currency: Mapped[str | None] = mapped_column(Text)
    pro_features: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default=text("'{}'"))
    bep20_address: Mapped[str | None] = mapped_column(Text)
    nagad_number: Mapped[str | None] = mapped_column(Text)
    bkash_number: Mapped[str | None] = mapped_column(Text)
    payment_note: Mapped[str | None] = mapped_column(Text)
    payment_methods: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=text("'[]'"))
    cloudinary_cloud_name: Mapped[str | None] = mapped_column(Text)
    cloudinary_api_key: Mapped[str | None] = mapped_column(Text)
    cloudinary_api_secret: Mapped[str | None] = mapped_column(Text)
    cloudinary_folder: Mapped[str | None] = mapped_column(Text)
    resend_api_key: Mapped[str | None] = mapped_column(Text)
    email_from: Mapped[str | None] = mapped_column(Text)
    flags: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)


class PaymentRequest(Base):
    __tablename__ = "payment_requests"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), index=True)
    method: Mapped[str] = mapped_column(Text, nullable=False)
    amount: Mapped[str | None] = mapped_column(Text)
    tx_id: Mapped[str | None] = mapped_column(Text)
    screenshot_url: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default=text("'pending'"))
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
