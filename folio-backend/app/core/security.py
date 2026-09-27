"""Authentication: verify the Supabase-issued JWT and expose the current user.

Supports BOTH signing schemes a Supabase project can use:
  - HS256 with the legacy shared JWT secret (SUPABASE_JWT_SECRET), and
  - Asymmetric ES256/RS256/EdDSA verified against the project's JWKS
    ({SUPABASE_URL}/auth/v1/.well-known/jwks.json) — used by the new API-key system.

Identity is taken ONLY from the verified token; the backend never trusts a user_id
sent in a body/query/header. The DB connection uses the pooler role (bypasses RLS),
so ownership is enforced in the service layer using this identity.
"""
from __future__ import annotations

from dataclasses import dataclass

import anyio
import jwt
from fastapi import Depends, Header, HTTPException, status
from jwt import PyJWKClient

from app.core.config import settings

_ASYMMETRIC = {"RS256", "RS384", "RS512", "ES256", "ES384", "ES512", "EdDSA"}
_AUDIENCE = "authenticated"
_jwk_client: PyJWKClient | None = None


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


def _jwks_url() -> str:
    return f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"


def _get_jwk_client() -> PyJWKClient:
    global _jwk_client
    if _jwk_client is None:
        _jwk_client = PyJWKClient(_jwks_url(), cache_keys=True)
    return _jwk_client


def _decode_hs256(token: str) -> dict:
    if not settings.SUPABASE_JWT_SECRET:
        raise HTTPException(500, "Server auth is not configured (SUPABASE_JWT_SECRET missing).")
    return jwt.decode(
        token,
        settings.SUPABASE_JWT_SECRET,
        algorithms=["HS256"],
        audience=_AUDIENCE,
        options={"require": ["sub", "exp"]},
    )


def _decode_asymmetric(token: str) -> dict:
    if not settings.SUPABASE_URL:
        raise HTTPException(500, "Server auth is not configured (SUPABASE_URL missing).")
    signing_key = _get_jwk_client().get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=list(_ASYMMETRIC),
        audience=_AUDIENCE,
        options={"require": ["sub", "exp"]},
    )


async def decode_supabase_jwt(token: str) -> dict:
    try:
        header = jwt.get_unverified_header(token)
    except jwt.InvalidTokenError:
        raise AuthError("Invalid token")

    alg = header.get("alg", "")
    try:
        if alg == "HS256":
            return _decode_hs256(token)
        if alg in _ASYMMETRIC:
            # JWKS fetch is blocking (urllib) — run it off the event loop.
            return await anyio.to_thread.run_sync(_decode_asymmetric, token)
        raise AuthError("Unsupported token algorithm")
    except jwt.ExpiredSignatureError:
        raise AuthError("Session expired")
    except jwt.InvalidTokenError:
        raise AuthError("Invalid token")
    except HTTPException:
        raise
    except Exception:
        # JWKS unreachable, key mismatch, etc. — never leak internals.
        raise AuthError("Could not verify token")


async def get_current_user(
    authorization: str | None = Header(default=None),
) -> CurrentUser:
    payload = await decode_supabase_jwt(_extract_bearer(authorization))
    sub = payload.get("sub")
    if not sub:
        raise AuthError()
    return CurrentUser(
        id=str(sub),
        email=payload.get("email"),
        role=str(payload.get("role", "authenticated")),
    )


CurrentUserDep = Depends(get_current_user)
