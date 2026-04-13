from unittest.mock import patch
from authorization.handler import handler


# --- Sample event ---
event_valid = {
    "authorizationToken": "Bearer valid_token",
    "methodArn": "arn:aws:execute-api:region:account:id"
}


# --- Test: valid token ---
@patch("authorization.handler.get_jwt_secret")
@patch("authorization.handler.verify_jwt")
@patch("authorization.handler.get_effect_from_scope")
@patch("authorization.handler.build_policy")
def test_handler_valid_token(
    mock_build_policy,
    mock_get_effect,
    mock_verify_jwt,
    mock_get_secret
):
    mock_get_secret.return_value = "secret"
    mock_verify_jwt.return_value = {"sub": "user123", "scope": "read"}
    mock_get_effect.return_value = "Allow"
    mock_build_policy.return_value = {"result": "ok"}

    result = handler(event_valid, None)

    assert result == {"result": "ok"}


# --- Test: invalid header format ---
@patch("authorization.handler.build_policy")
def test_handler_invalid_header_format(mock_build_policy):
    event = {
        "authorizationToken": "invalid_token",
        "methodArn": "arn"
    }

    mock_build_policy.return_value = {"deny": True}

    result = handler(event, None)

    assert result["deny"] is True


# --- Test: empty header ---
@patch("authorization.handler.build_policy")
def test_handler_empty_header(mock_build_policy):
    event = {
        "methodArn": "arn"
    }

    mock_build_policy.return_value = {"deny": True}

    result = handler(event, None)

    assert result["deny"] is True


# --- Test: invalid JWT ---
@patch("authorization.handler.get_jwt_secret")
@patch("authorization.handler.verify_jwt")
@patch("authorization.handler.build_policy")
def test_handler_invalid_jwt(
    mock_build_policy,
    mock_verify_jwt,
    mock_get_secret
):
    mock_get_secret.return_value = "secret"
    mock_verify_jwt.side_effect = Exception("Invalid token")
    mock_build_policy.return_value = {"deny": True}

    result = handler(event_valid, None)

    assert result["deny"] is True


# --- Test: missing sub ---
@patch("authorization.handler.get_jwt_secret")
@patch("authorization.handler.verify_jwt")
@patch("authorization.handler.get_effect_from_scope")
@patch("authorization.handler.build_policy")
def test_handler_missing_sub(
    mock_build_policy,
    mock_get_effect,
    mock_verify_jwt,
    mock_get_secret
):
    mock_get_secret.return_value = "secret"
    mock_verify_jwt.return_value = {"scope": "read"}  # no "sub"
    mock_get_effect.return_value = "Allow"
    mock_build_policy.return_value = {"principal": "unknown"}

    result = handler(event_valid, None)

    assert result["principal"] == "unknown"


# --- Test: deny scope ---
@patch("authorization.handler.get_jwt_secret")
@patch("authorization.handler.verify_jwt")
@patch("authorization.handler.get_effect_from_scope")
@patch("authorization.handler.build_policy")
def test_handler_deny_scope(
    mock_build_policy,
    mock_get_effect,
    mock_verify_jwt,
    mock_get_secret
):
    mock_get_secret.return_value = "secret"
    mock_verify_jwt.return_value = {"sub": "user123"}
    mock_get_effect.return_value = "Deny"
    mock_build_policy.return_value = {"effect": "Deny"}

    result = handler(event_valid, None)

    assert result["effect"] == "Deny"


# --- Test: secret failure ---
@patch("authorization.handler.get_jwt_secret")
@patch("authorization.handler.build_policy")
def test_handler_secret_failure(
    mock_build_policy,
    mock_get_secret
):
    mock_get_secret.side_effect = Exception("Secrets error")
    mock_build_policy.return_value = {"deny": True}

    result = handler(event_valid, None)

    assert result["deny"] is True


# --- Test: missing methodArn ---
@patch("authorization.handler.get_jwt_secret")
@patch("authorization.handler.verify_jwt")
@patch("authorization.handler.get_effect_from_scope")
@patch("authorization.handler.build_policy")
def test_handler_missing_method_arn(
    mock_build_policy,
    mock_get_effect,
    mock_verify_jwt,
    mock_get_secret
):
    event = {
        "authorizationToken": "Bearer valid_token"
    }

    mock_get_secret.return_value = "secret"
    mock_verify_jwt.return_value = {"sub": "user123"}
    mock_get_effect.return_value = "Allow"
    mock_build_policy.return_value = {"arn": "*"}

    result = handler(event, None)

    assert result["arn"] == "*"


# --- Test: weird bearer format ---
@patch("authorization.handler.get_jwt_secret")
@patch("authorization.handler.verify_jwt")
@patch("authorization.handler.get_effect_from_scope")
@patch("authorization.handler.build_policy")
def test_handler_weird_bearer_format(
    mock_build_policy,
    mock_get_effect,
    mock_verify_jwt,
    mock_get_secret
):
    event = {
        "authorizationToken": "Bearer    token",
        "methodArn": "arn"
    }

    mock_get_secret.return_value = "secret"
    mock_verify_jwt.return_value = {"sub": "user123"}
    mock_get_effect.return_value = "Allow"
    mock_build_policy.return_value = {"ok": True}

    result = handler(event, None)

    assert result["ok"] is True