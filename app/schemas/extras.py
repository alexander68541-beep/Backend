import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

_BASES = {"minimal", "bold", "editorial", "studio"}


class CustomTemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    category: str
    base: str
    accent: str
    plan: str
    is_published: bool


class CustomTemplateIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    category: str = Field(default="Custom", max_length=60)
    base: str = "minimal"
    accent: str = Field(default="#7c6cff", pattern=r"^#[0-9a-fA-F]{6}$")
    plan: str = "free"
    is_published: bool = True


class CustomTemplateUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=80)
    category: str | None = Field(default=None, max_length=60)
    base: str | None = None
    accent: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    plan: str | None = None
    is_published: bool | None = None


class ApplyTemplateIn(BaseModel):
    template_id: uuid.UUID


class MessageIn(BaseModel):
    body: str = Field(min_length=1, max_length=4000)


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    sender: str
    body: str
    created_at: datetime


class ThreadOut(BaseModel):
    user_id: uuid.UUID
    email: str | None = None
    last_body: str
    last_at: datetime
    unread: int
