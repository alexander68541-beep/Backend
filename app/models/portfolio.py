import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import CITEXT, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime

from app.models.base import Base, TimestampMixin


class Portfolio(Base, TimestampMixin):
    """A portfolio entity owned by a user. Public handle (username) lives here so a
    user can eventually own more than one addressable portfolio."""

    __tablename__ = "portfolios"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    username: Mapped[str | None] = mapped_column(CITEXT, unique=True, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'draft'")
    )
    is_primary: Mapped[bool] = mapped_column(nullable=False, server_default=text("true"))
    template: Mapped[str] = mapped_column(String(40), nullable=False, server_default=text("'minimal'"))

    username_changed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    username_change_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    profile: Mapped["PortfolioProfile"] = relationship(
        back_populates="portfolio", uselist=False, lazy="selectin"
    )


class PortfolioProfile(Base):
    """The universal 'profile' section (presentation data for a portfolio)."""

    __tablename__ = "portfolio_profiles"

    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("portfolios.id", ondelete="CASCADE"),
        primary_key=True,
    )
    display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    title: Mapped[str | None] = mapped_column(String(160), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(120), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )

    portfolio: Mapped["Portfolio"] = relationship(back_populates="profile")


class UsernameHistory(Base):
    __tablename__ = "username_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), index=True
    )
    old_username: Mapped[str | None] = mapped_column(CITEXT, nullable=True)
    new_username: Mapped[str | None] = mapped_column(CITEXT, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )


class ReservedUsername(Base):
    __tablename__ = "reserved_usernames"

    name: Mapped[str] = mapped_column(CITEXT, primary_key=True)
    note: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
