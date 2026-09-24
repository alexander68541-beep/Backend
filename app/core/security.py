"""Authentication: verify the Supabase-issued JWT and expose the current user.

The backend NEVER trusts a user_id sent in a body/query/header. Identity is taken
only from the verified access token. The DB connection uses the pooler role (which
bypasses RLS), so ownership MUST be enforced in the service layer using this identity.
"""
from __future__ import annotations

from dataclasses import dataclass

import jwt
from fastapi import Depends, Header, HTTPException, status

from app.core.config import settings


@dataclass(frozen=True)
class CurrentUser:
    id: str
    email: str | None
    role: str  # supabase auth role claim ("authenticated"); app role lives in profiles


class AuthError(HTTPException):
    def __init__(self, detail: str = "Not authenticated") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


def _extract_bearer(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise AuthError()
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise AuthError()
    return token


def decode_supabase_jwt(token: str) -> dict:
    if not settings.SUPABASE_JWT_SECRET:
        # Misconfiguration is a server problem, not the client's.
        raise HTTPException(status_code=500, detail="Server auth is not configured")
    try:
        return jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
            options={"require": ["sub", "exp"]},
        )
    except jwt.ExpiredSignatureError:
        raise AuthError("Session expired")
    except jwt.InvalidTokenError:
        raise AuthError("Invalid token")


async def get_current_user(
    authorization: str | None = Header(default=None),
) -> CurrentUser:
    payload = decode_supabase_jwt(_extract_bearer(authorization))
    sub = payload.get("sub")
    if not sub:
        raise AuthError()
    return CurrentUser(
        id=str(sub),
        email=payload.get("email"),
        role=str(payload.get("role", "authenticated")),
    )


CurrentUserDep = Depends(get_current_user)
