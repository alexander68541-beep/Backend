"""Server-side username validation. This is authoritative; the frontend mirror is only UX."""
from __future__ import annotations

import re

from app.core.config import settings

# lowercase letters / digits, single hyphens allowed, no leading/trailing/consecutive hyphen
_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# A small built-in profanity/abuse seed. The full list is configurable in DB later (Phase 7).
_PROFANITY = {
    "fuck", "shit", "bitch", "asshole", "cunt", "nigger", "faggot", "rape", "porn", "nazi",
}


def normalize_username(raw: str) -> str:
    return (raw or "").strip().lower()


def validate_username_format(raw: str) -> tuple[bool, str | None]:
    """Return (ok, error_code). error_code is a stable machine string when not ok."""
    name = normalize_username(raw)
    if not name:
        return False, "required"
    if len(name) < settings.USERNAME_MIN_LENGTH:
        return False, "too_short"
    if len(name) > settings.USERNAME_MAX_LENGTH:
        return False, "too_long"
    if not _PATTERN.match(name):
        return False, "invalid_characters"
    if _contains_profanity(name):
        return False, "not_allowed"
    return True, None


def _contains_profanity(name: str) -> bool:
    flat = name.replace("-", "")
    return any(bad in flat for bad in _PROFANITY)


def error_message(code: str) -> str:
    return {
        "required": "Username is required.",
        "too_short": f"Username must be at least {settings.USERNAME_MIN_LENGTH} characters.",
        "too_long": f"Username must be at most {settings.USERNAME_MAX_LENGTH} characters.",
        "invalid_characters": "Use lowercase letters, numbers and single hyphens only.",
        "not_allowed": "This username is not allowed.",
        "reserved": "This username is reserved.",
        "taken": "This username is already taken.",
    }.get(code, "Invalid username.")


def suggestion_candidates(desired: str) -> list[str]:
    """Generate candidate usernames for the availability check to filter."""
    base = normalize_username(desired)
    base = re.sub(r"[^a-z0-9-]", "", base).strip("-") or "portfolio"
    suffixes = ["", "-portfolio", "-studio", "-design", "-hq", "-co", "-official"]
    numbers = ["", "1", "01", "2", "07", "22"]
    out: list[str] = []
    seen: set[str] = set()
    for suf in suffixes:
        for num in numbers:
            cand = f"{base}{suf}{num}"
            ok, _ = validate_username_format(cand)
            if ok and cand not in seen:
                seen.add(cand)
                out.append(cand)
    return out
