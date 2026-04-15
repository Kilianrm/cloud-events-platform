# test_jwt.py
import pytest
import time
import jwt
import secrets
from shared.jwt_utils import generate_jwt, verify_jwt

# Generate a secure ~256-bit secret for all tests
SECURE_SECRET = secrets.token_urlsafe(32)


def test_generate_jwt_structure_secure_secret():
    """
    Test that generate_jwt returns a string JWT with correct payload fields.
    """
    client_id = "myclient"
    scope = "events:read"

    token = generate_jwt(client_id, scope, SECURE_SECRET)

    assert isinstance(token, str)

    payload = jwt.decode(token, SECURE_SECRET, algorithms=["HS256"])
    assert payload["sub"] == client_id
    assert payload["scope"] == scope

    now = int(time.time())
    assert payload["iat"] <= now
    assert payload["exp"] > now
    assert payload["exp"] - payload["iat"] == 3600  # default expiration


def test_generate_jwt_custom_expiration():
    """
    Test generate_jwt with a custom expiration time.
    """
    token = generate_jwt("client1", "read", SECURE_SECRET, expire_seconds=120)
    payload = jwt.decode(token, SECURE_SECRET, algorithms=["HS256"])
    assert payload["exp"] - payload["iat"] == 120


def test_verify_jwt_valid():
    """
    Test verify_jwt successfully decodes a valid token.
    """
    token = generate_jwt("client1", "read", SECURE_SECRET)
    payload = verify_jwt(token, SECURE_SECRET)
    assert payload["sub"] == "client1"
    assert payload["scope"] == "read"


def test_verify_jwt_expired():
    """
    Test that verify_jwt raises ValueError for expired tokens.
    """
    token = generate_jwt("client1", "read", SECURE_SECRET, expire_seconds=-1)
    time.sleep(1)  # Ensure token is expired
    with pytest.raises(ValueError, match="Token has expired"):
        verify_jwt(token, SECURE_SECRET)


def test_verify_jwt_invalid():
    """
    Test that verify_jwt raises ValueError for malformed/invalid tokens.
    """
    fake_token = "this.is.not.a.jwt"
    with pytest.raises(ValueError, match="Invalid token"):
        verify_jwt(fake_token, SECURE_SECRET)


def test_generate_jwt_multiple_scopes():
    """
    Test that generate_jwt correctly handles scope as a list.
    """
    token = generate_jwt("client1", ["read", "write"], SECURE_SECRET)
    payload = jwt.decode(token, SECURE_SECRET, algorithms=["HS256"])
    assert payload["scope"] == ["read", "write"]