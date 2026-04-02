import json
from shared.secrets_service import get_client_data, get_jwt_secret
from shared.jwt_utils import generate_jwt
from authentication.authenticate_client import validate_client
from shared.logging_utils import log
from shared.parse_utils import extract_method_and_path, get_correlation_id

import os


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

    #Get secret name:
    correlation_id = None

    try:
        correlation_id = get_correlation_id(event)
        method, path = extract_method_and_path(event)

        log(
            "Authentication request received",
            level="info",
            correlation_id=correlation_id,
            status="received",
            method=method,
            path=path
        )

        jwt_secret_name = os.getenv("JWT_SECRET_NAME", "auth/jwt_secret")
        client_secret_prefix = os.getenv("CLIENT_SECRET_PREFIX","auth/client/")

        # Parse the request body
        body = json.loads(event.get("body", "{}"))
        client_id = body.get("client_id")
        client_secret = body.get("client_secret")

        log(
            "Authentication payload parsed",
            level="info",
            correlation_id=correlation_id,
            method=method,
            path=path,
            client_id=client_id,
            secret_present=bool(client_secret)
        )


        # Validate if body is empty:
        if not client_id or not client_secret:
            log(
                "Missing client credentials",
                level="warning",
                correlation_id=correlation_id,
                status="rejected",
                method=method,
                path=path,
                client_id=client_id
            )

            return {
                "statusCode": 401,
                "body": json.dumps({"error": "invalid_client"})
            }
        
        # Retrieve client data from Secrets Manager
        client_data = get_client_data(client_id)
        if not client_data:
            log(
                "Client not found",
                level="warning",
                correlation_id=correlation_id,
                status="rejected",
                method=method,
                path=path,
                client_id=client_id
            )
            return {
                "statusCode": 401,
                "body": json.dumps({"error": "invalid_client"})
            }

        # Validate client credentials
        if not validate_client(client_id, client_secret, client_data):
            log(
                "Client authentication failed",
                level="warning",
                correlation_id=correlation_id,
                status="rejected",
                method=method,
                path=path,
                client_id=client_id
            )

            return {
                "statusCode": 401,
                "body": json.dumps({"error": "invalid_client"})
            }

        log(
            "Client authenticated successfully",
            level="info",
            correlation_id=correlation_id,
            status="validated",
            method=method,
            path=path,
            client_id=client_id
        )

        # Generate JWT token
        token = generate_jwt(client_id, client_data.get("scope"), get_jwt_secret(SecretId=jwt_secret_name))

        log(
            "JWT generated successfully",
            level="info",
            correlation_id=correlation_id,
            status="success",
            method=method,
            path=path,
            client_id=client_id,
            scopes=client_data.get("scope", [])
        )

        # Return success response with token
        return {
            "statusCode": 200,
            "body": json.dumps({
                "access_token": token,
                "token_type": "Bearer"
            })
        }
    except Exception as e:
        import traceback

        log(
            "Authentication process failed",
            level="error",
            correlation_id=correlation_id,
            status="failed",
            method=method,
            path=path,
            error=str(e),
            traceback=traceback.format_exc()
        )

        return {
            "statusCode": 500,
            "body": json.dumps({"error": "internal_server_error"})
        }
    