from read.persistence import get_event
from read.errors import EventNotFound
from shared.response import response
from shared.serialization import to_json_safe
from shared.logging_utils import log
from shared.parse_utils import get_correlation_id


def handler(event, context):
    correlation_id = get_correlation_id(event)
    event_id = None

    log("Read request received",
        level="info",
        correlation_id=correlation_id,
        status="received",
        path=event.get("path"),
        method=event.get("httpMethod"))
    try:
        path_params = event.get("pathParameters")
        if not path_params or "event_id" not in path_params:
            log(
                "Request rejected: missing path parameter: event_id",
                level="error",
                correlation_id=correlation_id,
                status="rejected"
            )
            return response(
                400,
                {
                    "error": "InvalidRequest",
                    "message": "event_id path parameter is required",
                },
            )

        event_id = path_params["event_id"]
        log(
            "Fetching event",
            level = "info",
            correlation_id=correlation_id,
            event_id=event_id,
            status="fetching",
        )
        item = get_event(event_id)
        log(
            "Event found",
            level="info",
            correlation_id=correlation_id,
            event_id=event_id,
            status="accepted"
        )

        return response(
            200,
            to_json_safe(item),
        )

    except EventNotFound:
        log(
            "Event not found",
            level="error",
            correlation_id=correlation_id,
            event_id=event_id,
            status="rejected"
        )
        
        return response(
            404,
            {
                "error": "EventNotFound",
                "message": "Event with the given identifier does not exist",
            },
        )

    except Exception as e:
        log(
            "Unexpected error during read",
            level="error",
            correlation_id=correlation_id,
            event_id=event_id,
            status= "rejected",
            error=repr(e)
        )
        return response(
            500,
            {
                "error": "InternalError",
                "message": "An unexpected error occurred",
            },
        )
