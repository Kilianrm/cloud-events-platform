from shared.secrets_service import get_jwt_secret
from shared.jwt_utils import verify_jwt
from authorization.permissions import get_effect_from_scope
from authorization.policy_builder import build_policy
from shared.logging_utils import log
from shared.parse_utils import extract_method_and_path, get_correlation_id

import os

def handler(event: dict, context: any) -> dict:
    """
    AWS Lambda Authorizer handler for JWT-based authentication and authorization.
    
    Args:
        event (dict): Event payload from API Gateway, contains 'authorizationToken' and 'methodArn'.
        context (object): Lambda context object (not used here).
    
    Returns:
        dict: Policy document allowing or denying access to the API Gateway method.
    """
    try:


        correlation_id = get_correlation_id(event)
        method, path = extract_method_and_path(event)
        log(
            "Authorization request received",
            level="info",
            correlation_id=correlation_id,
            status="received",
            method = method,
            path=path,
        )
        
        jwt_secret_name = os.getenv("JWT_SECRET_NAME", "auth/jwt_secret")
        # Extract the Authorization header from the event
        auth_header = event.get("headers", {}).get("authorization", "")

        print("HOLA",auth_header)
        if not auth_header.startswith("Bearer "):
            token_preview = auth_header[:10] + "..." if auth_header else "None"
            log(
                "Invalid authorization header format",
                level="error",
                correlation_id=correlation_id,
                status="rejected",
                method = method,
                path=path,
                token_preview=token_preview
            )
            raise ValueError("Invalid authorization header format")
        

        # Extact token
        token = auth_header.split(" ", 1)[1]

        log(
            "Get auth_header",
            level="info",
            correlation_id=correlation_id,
            status="received",
            method = method,
            path=path,
            token_preview=token[:10] + "..."
        )
        
        # Extract the JWT token from the header safely
        token = auth_header.split(" ", 1)[1]
        
        # Get the secret for verifying the JWT
        secret = get_jwt_secret(jwt_secret_name)
        
        # Verify the JWT and decode the payload
        payload = verify_jwt(token, secret)
        
        # Extract the principal ID (user identifier)
        principal_id = payload.get("sub", "unknown")

        log(
            "JWT verified successfully",
            level="info",
            correlation_id=correlation_id,
            status="verified",
            method = method,
            path=path,
            principal_id=payload.get("sub", "unknown"),
            scopes=payload.get("scope", []),
            token_preview=token[:10] + "..."
        )
        
        # Determine the effect ("Allow" or "Deny") based on JWT scopes
        effect = get_effect_from_scope(payload,method)

        log(
            "Authorization decision",
            level="info",
            correlation_id=correlation_id,
            status="authorized" if effect == "Allow" else "denied",
            method = method,
            path=path,
            principal_id=principal_id,
            effect=effect,
        )

        # Build and return the IAM policy allowing or denying access
        return build_policy(principal_id, effect, event.get("methodArn", "*"))

    
    except Exception as e:
        # Log the error for debugging purposes
        import traceback

        log(
            "Authorization failed",
            level="error",
            correlation_id=correlation_id,
            status="failed",
            method = method,
            path=path,
            token_preview=token[:10] + "..." if 'token' in locals() else "N/A",
            error=str(e),
            traceback=traceback.format_exc()
        )
        
        # Deny access if any error occurs
        return build_policy("unknown", "Deny", event.get("methodArn", "*"))
    
