import uuid

from pydantic import BaseModel, ConfigDict, EmailStr


class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr | None = None
    full_name: str | None = None
    role: str
    plan: str = "free"
