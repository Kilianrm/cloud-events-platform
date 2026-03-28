def get_effect_from_scope(payload: dict) -> str:
    scope = payload.get("scope", "")

    if "events:read" in scope:
        return "Allow"

    return "Deny"