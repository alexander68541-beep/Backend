"""Centralised plan entitlements. Free plan has caps; pro/admin are unlimited.
Admins can override via platform_settings.plan_limits (JSON: {plan: {entity: n}})."""

DEFAULT_LIMITS: dict[str, dict[str, int]] = {
    "free": {
        "projects": 6, "gallery": 12, "skills": 30, "experience": 10, "education": 8,
        "services": 8, "certifications": 15, "achievements": 15, "testimonials": 10,
        "publications": 15, "videos": 6, "links": 12,
    },
    "pro": {},  # empty = unlimited
}


def effective_plan(role: str, plan: str) -> str:
    return "pro" if (role == "admin" or plan == "pro") else "free"


def entity_limits(plan: str, overrides: dict | None) -> dict[str, int]:
    base = dict(DEFAULT_LIMITS.get(plan, {}))
    if overrides and isinstance(overrides, dict) and isinstance(overrides.get(plan), dict):
        base.update({k: int(v) for k, v in overrides[plan].items()})
    return base


def limit_for(entity: str, plan: str, overrides: dict | None) -> int | None:
    return entity_limits(plan, overrides).get(entity)  # None = unlimited
