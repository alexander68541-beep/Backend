# Catalogue of gate-able features. Each PLAN (in platform_settings.plans) lists which
# feature keys it includes. A user gets exactly the features of their own plan.
FEATURE_CATALOG = [
    {"key": "premium_templates", "label": "Premium templates", "desc": "Studio and other premium designs"},
    {"key": "custom_accent", "label": "Custom accent colour", "desc": "Any colour, not just the presets"},
    {"key": "remove_branding", "label": "Remove Folio branding", "desc": "Hide the ‘Made with Folio’ footer"},
    {"key": "custom_domain", "label": "Custom domain", "desc": "Connect your own domain"},
    {"key": "analytics", "label": "Analytics", "desc": "Visitor and view stats"},
]

FEATURE_KEYS = {f["key"] for f in FEATURE_CATALOG}


def is_pro_account(role: str, plan: str) -> bool:
    """True for any paid account (used for coarse 'is this a paying user' checks)."""
    return role == "admin" or plan in ("pro", "max")


def features_for_plan(plan: str, plans: list[dict] | None) -> set[str]:
    """The set of feature keys included in the given plan, from the admin plans catalogue."""
    for p in (plans or []):
        if isinstance(p, dict) and p.get("key") == plan:
            return {f for f in (p.get("features") or []) if isinstance(f, str)}
    return set()


def has_feature(key: str, plans: list[dict] | None, role: str, plan: str) -> bool:
    """A user has a feature only if their own plan includes it (admins get everything)."""
    if role == "admin":
        return True
    return key in features_for_plan(plan, plans)
