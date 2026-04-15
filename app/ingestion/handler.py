import json

from ingestion.persistence import persist_event
from ingestion.errors import EventAlreadyExists
from shared.logging_utils import log
from shared.parse_utils import get_correlation_id


def handler(event, context):
    correlation_id = get_correlation_id(event)

    print(event)
    records = event.get("Records", [])

    log(
        "Ingestion batch received",
        level="info",
        correlation_id=correlation_id,
        records=len(records),
    )

    batch_item_failures = []

    for record in records:
        message_id = record.get("messageId")
        event_id = None

        try:
            # -----------------------------
            # SAFE BODY ACCESS
            # -----------------------------
            body_raw = record.get("body")
            if not body_raw:
                raise Exception("Missing SQS body")

            # -----------------------------
            # PARSE JSON
            # -----------------------------
            body = json.loads(body_raw)
            event_data = body.get("event", {})
            event_id = event_data.get("event_id")

            log(
                "Processing event",
                level="info",
                correlation_id=correlation_id,
                event_id=event_id,
            )

            # -----------------------------
            # TEST HOOK (infra-level only)
            # -----------------------------
            metadata = body.get("metadata", {})
            if metadata.get("test", {}).get("force_fail"):
                raise RuntimeError("Injected failure for DLQ test")
            

            # -----------------------------
            # PERSISTENCE
            # -----------------------------
            persist_event(event_data)

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
            # NOT failure → do NOT retry

        except Exception as e:
            log(
                "Unexpected ingestion error",
                level="error",
                correlation_id=correlation_id,
                event_id=event_id,
                error=repr(e),
            )

            # mark ONLY this message as failed
            if message_id:
                batch_item_failures.append({
                    "itemIdentifier": message_id
                })

    # -----------------------------
    # AWS SQS RESPONSE FORMAT
    # -----------------------------
    return {
        "batchItemFailures": batch_item_failures
    }