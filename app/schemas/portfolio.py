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
    tagline: str | None = None
    pronouns: str | None = None
    about: str | None = None
    email: str | None = None
    phone: str | None = None
    website: str | None = None
    availability: str | None = None
    resume_url: str | None = None


class PortfolioProfileUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=120)
    title: str | None = Field(default=None, max_length=160)
    bio: str | None = Field(default=None, max_length=2000)
    location: str | None = Field(default=None, max_length=120)
    avatar_url: str | None = Field(default=None, max_length=2048)
    tagline: str | None = Field(default=None, max_length=200)
    pronouns: str | None = Field(default=None, max_length=40)
    about: str | None = Field(default=None, max_length=4000)
    email: str | None = Field(default=None, max_length=320)
    phone: str | None = Field(default=None, max_length=40)
    website: str | None = Field(default=None, max_length=2048)
    availability: str | None = Field(default=None, max_length=200)
    resume_url: str | None = Field(default=None, max_length=2048)


class PortfolioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str | None = None
    status: str
    template: str = "minimal"
    accent: str = "#7c6cff"
    seo_title: str | None = None
    seo_description: str | None = None
    seo_image: str | None = None
    is_primary: bool
    username_change_count: int
    username_changed_at: datetime | None = None
    profile: PortfolioProfileOut | None = None


class UsernameSetIn(BaseModel):
    username: str = Field(min_length=1, max_length=60)


class StatusUpdateIn(BaseModel):
    status: Literal["draft", "published", "unpublished"]


class TemplateUpdateIn(BaseModel):
    template: str = Field(min_length=1, max_length=40)


class AccentUpdateIn(BaseModel):
    accent: str = Field(min_length=4, max_length=9, pattern=r"^#[0-9a-fA-F]{6}$")


class SeoUpdateIn(BaseModel):
    seo_title: str | None = Field(default=None, max_length=200)
    seo_description: str | None = Field(default=None, max_length=400)
    seo_image: str | None = Field(default=None, max_length=2048)
