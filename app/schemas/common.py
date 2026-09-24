from pydantic import BaseModel


class MessageOut(BaseModel):
    detail: str
    code: str = "ok"


class AvailabilityOut(BaseModel):
    username: str
    available: bool
    reason: str | None = None  # machine code when not available
    message: str | None = None  # user-safe message
    suggestions: list[str] = []
