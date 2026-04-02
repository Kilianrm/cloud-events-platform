
import uuid
def extract_method_and_path(event: dict):
    """
    Extract HTTP method and path from a Lambda event (HTTP API v2 style).
    Returns:
        method (str or None), path (str or None)
    """
    # Try 
    route_key = event.get("routeKey") 
    if route_key and " " in route_key:
        method, path = route_key.split(" ", 1)
        return method, path

    # Try
    http_info = event.get("requestContext", {}).get("http", {})
    method = http_info.get("method")
    path = http_info.get("path")
    if method or path:
        return method, path 

    #Try
    method = event.get("httpMethod")
    path = event.get("path")
    if method or path:
        return method, path 
    
    #Try
    raw_path = event.get("rawPath")
    if raw_path:
        return None, raw_path 

    # 4️⃣ Could not find anything
    return None, None

def get_correlation_id(event):
    """
    Professional, robust way to get a correlation ID.
    - Uses client-sent header if present
    - Uses API Gateway requestId if present
    - Generates a UUID as last resort
    """
    headers = event.get("headers") or {}
    correlation_id = headers.get("X-Correlation-Id")

    # Safe access to API Gateway requestId
    if not correlation_id:
        correlation_id = event.get("requestContext", {}).get("requestId")

    # Fallback: generate a random UUID if nothing else exists
    if not correlation_id:
        correlation_id = str(uuid.uuid4())

    return correlation_id