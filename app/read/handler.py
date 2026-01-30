from read.persistence import get_event
from read.errors import EventNotFound
from shared.response import response
from shared.serialization import to_json_safe


def handler(event, context):
    print("Read lambda invoked")

    try:
        path_params = event.get("pathParameters")
        if not path_params or "event_id" not in path_params:
            print("Missing path parameter: event_id")
            return response(
                400,
                {
                    "error": "InvalidRequest",
                    "message": "event_id path parameter is required",
                },
            )

        event_id = path_params["event_id"]
        print(f"Fetching event_id={event_id}")

        item = get_event(event_id)

        print(f"Event found event_id={event_id}")

        return response(
            200,
            to_json_safe(item),
        )

    except EventNotFound:
        print(f"Event not found event_id={event_id}")
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
            {
                "error": "InternalError",
                "message": "An unexpected error occurred",
            },
        )
