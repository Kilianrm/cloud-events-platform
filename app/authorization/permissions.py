def get_effect_from_scope(payload: dict, method: str) -> str:
    """
    Returns 'Allow' or 'Deny' based on user's scope and HTTP method.
    Assumes method is either 'GET', 'POST', or None.
    """
    scope = payload.get("scope", "")
    
    if not method:
        return "Deny"
    
    if method == "GET" and "read" in scope:
        return "Allow"
    elif method == "POST" and "write" in scope:
        return "Allow"
    
    return "Deny"