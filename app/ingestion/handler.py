import json
from ingestion.validation import validate_event
from ingestion.persistence import persist_event
from ingestion.errors import ValidationError, EventAlreadyExists
from shared.response import response


def handler(event, context):
    print("Ingestion lambda invoked")

    try:
        if not event.get("body"):
            print("Invalid request: missing body")
            return response(
                400,
                {"error": "InvalidRequest", "message": "Request body is required"},
            )

        body = json.loads(event["body"])
        event_id = body.get("event_id")

        print(f"Ingesting event_id={event_id}")

        validate_event(body)
        persist_event(body)

        print(f"Event accepted event_id={event_id}")

        return response(
            201,
            {"event_id": event_id, "status": "accepted"},
        )

    except ValidationError as e:
        print(f"Validation failed event_id={event_id} error={e.message}")
        return response(
            400,
            {"error": "InvalidEvent", "message": e.message},
        )

    except EventAlreadyExists:
        print(f"Duplicate event event_id={event_id}")
        return response(
            200,
            {"event_id": event_id, "status": "already_exists"},
        )

    except Exception as e:
        print(f"Unexpected error event_id={event_id} error={repr(e)}")
        return response(
            500,
            {"error": "InternalError", "message": "An unexpected error occurred"},
        )
