from ingestion.errors import ValidationError
from datetime import datetime, timezone
import json


REQUIRED_FIELDS = {
    "event_id",
    "event_type",
    "source",
    "timestamp",
    "payload",
}


def validate_event(event: dict) -> None:
    missing = REQUIRED_FIELDS - event.keys()
    if missing:
        raise ValidationError(f"Missing required fields: {', '.join(missing)}")

    _validate_timestamp(event["timestamp"])
    _validate_payload(event["payload"])


def _validate_timestamp(ts: str) -> None:
    try:
        event_time = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        raise ValidationError("Invalid timestamp format")

    now = datetime.now(timezone.utc)
    if event_time > now.replace(year=now.year + 1):
        raise ValidationError("Timestamp too far in the future")


def _validate_payload(payload) -> None:
    try:
        json.dumps(payload)
    except TypeError:
        raise ValidationError("Payload must be JSON serializable")
