import json

from ingestion.persistence import persist_event
from ingestion.errors import EventAlreadyExists
from shared.logging_utils import log
from shared.parse_utils import get_correlation_id


def handler(event, context):
    correlation_id = get_correlation_id(event)

    records = event.get("Records", [])

    log(
        "Ingestion batch received",
        level="info",
        correlation_id=correlation_id,
        records=len(records),
    )

    for record in records:
        event_id = None

        try:
            body = json.loads(record["body"])
            event_id = body.get("event_id")

            log(
                "Processing event",
                level="info",
                correlation_id=correlation_id,
                event_id=event_id,
            )

            # ingestion = NO validation
            persist_event(body)

            log(
                "Event persisted",
                level="info",
                correlation_id=correlation_id,
                event_id=event_id,
                status="accepted",
            )

        except EventAlreadyExists:
            log(
                "Duplicate event",
                level="warning",
                correlation_id=correlation_id,
                event_id=event_id,
            )

            # no raise → SQS continuará con otros mensajes

        except Exception as e:
            log(
                "Unexpected ingestion error",
                level="error",
                correlation_id=correlation_id,
                event_id=event_id,
                error=repr(e),
            )

            # importante: re-raise para retry + DLQ
            raise