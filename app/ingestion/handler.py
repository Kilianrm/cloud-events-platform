import json
from ingestion.validation import validate_event
from ingestion.persistence import persist_event
from ingestion.errors import ValidationError, EventAlreadyExists
from shared.response import response


def handler(event, context):
    try:
        body = json.loads(event["body"])
        validate_event(body)
        persist_event(body)

        return response(
            201,
            {
                "event_id": body["event_id"],
                "status": "accepted",
            },
        )

    except ValidationError as e:
        return response(400, {"error": "InvalidEvent", "message": e.message})

    except EventAlreadyExists:
        return response(
            200,
            {
                "event_id": body["event_id"],
                "status": "already_exists",
            },
        )

    except Exception:
        return response(
            500,
            {"error": "InternalError", "message": "An unexpected error occurred"},
        )
