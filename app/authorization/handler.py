from shared.secrets_service import get_jwt_secret
from shared.jwt_utils import verify_jwt
from authorization.permissions import get_effect_from_scope
from authorization.policy_builder import build_policy


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
        # Extract the Authorization header from the event
        auth_header = event.get("authorizationToken", "")
        
        # Check if header starts with 'Bearer ', otherwise reject
        if not auth_header.startswith("Bearer "):
            raise ValueError("Invalid authorization header format")
        
        # Extract the JWT token from the header safely
        token = auth_header.split(" ", 1)[1]
        
        # Get the secret for verifying the JWT
        secret = get_jwt_secret()
        
        # Verify the JWT and decode the payload
        payload = verify_jwt(token, secret)
        
        # Extract the principal ID (user identifier)
        principal_id = payload.get("sub", "unknown")
        
        # Determine the effect ("Allow" or "Deny") based on JWT scopes
        effect = get_effect_from_scope(payload)
    
    except Exception as e:
        # Log the error for debugging purposes
        print(f"Authorization failed: {e}")
        # Deny access if any error occurs
        return build_policy("unknown", "Deny", event.get("methodArn", "*"))
    
    # Build and return the IAM policy allowing or denying access
    return build_policy(principal_id, effect, event.get("methodArn", "*"))