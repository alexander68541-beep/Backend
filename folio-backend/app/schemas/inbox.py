import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ContactIn(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    email: str | None = Field(default=None, max_length=320)
    message: str = Field(min_length=1, max_length=4000)
    website: str | None = None  # honeypot — must stay empty


class ContactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str | None = None
    email: str | None = None
    message: str
    read: bool
    created_at: datetime


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    type: str
    title: str
    body: str | None = None
    read: bool
    created_at: datetime
