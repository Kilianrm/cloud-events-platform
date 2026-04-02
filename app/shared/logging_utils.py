import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def log(message,level="info",correlation_id=None,status=None,path=None,method=None,**kwargs):
    """
    Structured log in JSON format.
    Ensures uniform fields for observability.
    """
    log_entry = {
        "message": message,
        "level": level,
        "correlation_id": correlation_id,
        "status": status,
        "path": path,
        "method": method,
    }

    # Merge extra fields if needed
    log_entry.update(kwargs)

    print(json.dumps(log_entry))