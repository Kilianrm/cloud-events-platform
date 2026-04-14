import json
import os
import boto3

from validation.validators import validate_event
from validation.errors import ValidationError
from shared.response import response
from shared.logging_utils import log
from shared.parse_utils import get_correlation_id


def get_sqs():
    return boto3.client("sqs")

def handler(event, context):
    correlation_id = get_correlation_id(event)

    log(
        "Validation request received",
        level="info",
        correlation_id=correlation_id,
    )

    sqs = get_sqs()

    try:
        if not event.get("body"):
            return response(
                400,
                {
                    "error": "INVALID_REQUEST",
                    "message": "Request body is required"
                },
            )
        body = json.loads(event["body"])
        

        validate_event(body)

        event_id = body["event_id"]

        QUEUE_URL = os.environ["QUEUE_URL"]
        sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps({
                "correlation_id": correlation_id,
                "event": body
            })
        )

        log(
            "Event queued successfully",
            level="info",
            correlation_id=correlation_id,
            event_id=event_id,
            status="accepted",
        )

        return response(
            202,
            {
                "event_id": event_id,
                "status": "accepted"
            },
        )

    except ValidationError as e:
        log(
            "Validation failed",
            level="warning",
            correlation_id=correlation_id,
            error_code=e.code,
            error_message=e.message,
        )

        return response(
            400,
            {
                "error": e.code,
                "message": e.message
            },
        )

    except Exception as e:
        log(
            "Internal error",
            level="error",
            correlation_id=correlation_id,
            error=repr(e),
        )

        return response(
            500,
            {
                "error": "INTERNAL_ERROR",
                "message": "Unexpected error"
            },
        )