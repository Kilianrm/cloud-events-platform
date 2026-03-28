import json
from shared.secrets_service import get_client_data, get_jwt_secret
from shared.jwt_utils import generate_jwt
from authentication.authenticate_client import validate_client


def handler(event: dict, context) -> dict:
    """
    Lambda handler for client authentication.

    This handler performs the following steps:
        1. Extracts client_id and client_secret from the request body.
        2. Retrieves client data from AWS Secrets Manager.
        3. Validates the credentials.
        4. Generates a JWT if credentials are correct.
        5. Returns a JSON response with the token or a 401 error if validation fails.

    Args:
        event (dict): Event received by Lambda (HTTP request from API Gateway).
        context: Lambda execution context.

    Returns:
        dict: Dictionary with statusCode and body (JSON) containing the token or an error.
    """
    # Parse the request body
    body = json.loads(event.get("body", "{}"))
    client_id = body.get("client_id")
    client_secret = body.get("client_secret")

    # Retrieve client data from Secrets Manager
    client_data = get_client_data(client_id)
    if not client_data:
        return {
            "statusCode": 401,
            "body": json.dumps({"error": "invalid_client"})
        }

    # Validate client credentials
    if not validate_client(client_id, client_secret, client_data):
        return {
            "statusCode": 401,
            "body": json.dumps({"error": "invalid_client"})
        }

    # Generate JWT token
    token = generate_jwt(client_id, client_data.get("scope"), get_jwt_secret())

    # Return success response with token
    return {
        "statusCode": 200,
        "body": json.dumps({
            "access_token": token,
            "token_type": "Bearer"
        })
    }