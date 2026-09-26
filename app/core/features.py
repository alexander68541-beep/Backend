# Catalogue of gate-able features. Admin marks which keys are "pro" (stored in
# platform_settings.pro_features). A capability is available to a user if its key is
# NOT marked pro, or the user is pro/admin.
FEATURE_CATALOG = [
    {"key": "premium_templates", "label": "Premium templates", "desc": "Studio and other premium designs"},
    {"key": "custom_accent", "label": "Custom accent colour", "desc": "Any colour, not just the presets"},
    {"key": "remove_branding", "label": "Remove Folio branding", "desc": "Hide the ‘Made with Folio’ footer"},
    {"key": "custom_domain", "label": "Custom domain", "desc": "Connect your own domain (coming soon)"},
    {"key": "analytics", "label": "Analytics", "desc": "Visitor and view stats (coming soon)"},
]

FEATURE_KEYS = {f["key"] for f in FEATURE_CATALOG}


def is_pro_account(role: str, plan: str) -> bool:
    return role == "admin" or plan == "pro"


def has_feature(key: str, pro_features: list[str], role: str, plan: str) -> bool:
    if key not in (pro_features or []):
        return True  # not gated -> free for everyone
    return is_pro_account(role, plan)
