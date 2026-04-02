import json
from ingestion.validation import validate_event
from ingestion.persistence import persist_event
from ingestion.errors import ValidationError, EventAlreadyExists
from shared.response import response
from shared.logging_utils import log
from shared.parse_utils import get_correlation_id

def handler(event, context):
    correlation_id = get_correlation_id(event)
    event_id = None

    log(
        "Ingestion request received",
        level="info",
        correlation_id=correlation_id,
        status="received",
        path=event.get("path"),
        method=event.get("httpMethod"),
    )

    try:
        if not event.get("body"):
            log(
                "Request rejected: missing body",
                level="error",
                correlation_id=correlation_id,
                status="rejected"
            )
            return response(
                400,
                {"error": "InvalidRequest", "message": "Request body is required"},
            )

        body = json.loads(event["body"])
        event_id = body.get("event_id")

        log(
            "Processing event",
            level = "info",
            correlation_id=correlation_id,
            event_id=event_id,
            status="processing",
        )

        validate_event(body)
        persist_event(body)

        log(
            "Request accepted",
            level="info",
            correlation_id=correlation_id,
            event_id=event_id,
            status="accepted"
        )

        return response(
            201,
            {"event_id": event_id, "status": "accepted"},
        )

    except ValidationError as e:
        log(
            "Request rejected: validation failed",
            level="error",
            correlation_id=correlation_id,
            event_id=event_id,
            status= "rejected",
        )
        return response(
            400,
            {"error": "InvalidEvent", "message": e.message},
        )

    except EventAlreadyExists:
        log(
            "Request accepted: already exists",
            level="error",
            correlation_id=correlation_id,
            event_id=event_id,
            status= "rejected",
        )
        return response(
            200,
            {"event_id": event_id, "status": "already_exists"},
        )

    except Exception as e:
        log(
            "Internal error",
            level="error",
            correlation_id=correlation_id,
            event_id=event_id,
            status= "rejected",
            error=repr(e)
        )
        return response(
            500,
            {"error": "InternalError", "message": "An unexpected error occurred"},
        )
