import json
import logging
import uuid

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def log(message,level="info",correlation_id=None,event_id=None,status=None,path=None,method=None,error=None,**kwargs):
    """
    Structured log in JSON format.
    Ensures uniform fields for observability.
    """
    log_entry = {
        "message": message,
        "level": level,
        "correlation_id": correlation_id,
        "event_id": event_id,
        "status": status,
        "path": path,
        "method": method,
        "error": error,
    }

    # Merge extra fields if needed
    log_entry.update(kwargs)

    print(json.dumps(log_entry))

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