import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PortfolioProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    display_name: str | None = None
    title: str | None = None
    bio: str | None = None
    location: str | None = None
    avatar_url: str | None = None


class PortfolioProfileUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=120)
    title: str | None = Field(default=None, max_length=160)
    bio: str | None = Field(default=None, max_length=2000)
    location: str | None = Field(default=None, max_length=120)
    avatar_url: str | None = Field(default=None, max_length=2048)


class PortfolioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str | None = None
    status: str
    is_primary: bool
    username_change_count: int
    username_changed_at: datetime | None = None
    profile: PortfolioProfileOut | None = None


class UsernameSetIn(BaseModel):
    username: str = Field(min_length=1, max_length=60)


class StatusUpdateIn(BaseModel):
    status: Literal["draft", "published", "unpublished"]
