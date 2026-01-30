from read.persistence import get_event
from read.errors import EventNotFound
from shared.response import response
from shared.serialization import to_json_safe


def handler(event, context):
    try:
        event_id = event["pathParameters"]["event_id"]

        item = get_event(event_id)

        return response(200, to_json_safe(item),)

    except EventNotFound:
        return response(
            404,
            {
                "error": "EventNotFound",
                "message": "Event with the given identifier does not exist",
            },
        )

    except Exception as e:
        print("READ ERROR:", repr(e))
        return response(
            500,
            {"error": "InternalError", "message": "An unexpected error occurred"},
        )
