import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

def generate_jwt(client_id, scope, secret_key, expire_seconds=3600):
    """
    Generates a JWT token with the given client_id, scope, and secret key.

    Args:
        client_id (str): The ID of the client.
        scope (str | list): The access scope(s) of the client.
        secret_key (str): The secret key used to sign the token.
        expire_seconds (int, optional): Token expiration time in seconds. Defaults to 3600 (1 hour).

    Returns:
        str: The signed JWT token.
    """
    import time
    payload = {
        "sub": client_id,
        "scope": scope,
        "iat": int(time.time()),               # Issued at
        "exp": int(time.time()) + expire_seconds  # Expiration
    }

    token = jwt.encode(payload, secret_key, algorithm="HS256")
    return token


def verify_jwt(jwt_token: str, secret: str) -> dict:
    """
    Verifies a JWT token and returns its payload.

    Args:
        token (str): JWT token to verify.
        secret (str): Secret key used to verify the token.

    Returns:
        dict: The decoded payload of the token.

    Raises:
        ValueError: If the token is expired or invalid.
    """
    try:
        payload = jwt.decode(
            jwt_token,
            secret,
            algorithms=["HS256"]
        )
        return payload
    except ExpiredSignatureError:
        raise ValueError("Token has expired")
    except InvalidTokenError:
        raise ValueError("Invalid token")