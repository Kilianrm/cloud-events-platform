from datetime import datetime, timezone, timedelta
import json
import uuid

from validation.errors import ValidationError, ErrorCodes

REQUIRED_FIELDS = {
    "event_id",
    "event_type",
    "source",
    "timestamp",
    "payload",
}


def validate_event(event: dict) -> None:
    _validate_required_fields(event)
    _validate_event_id(event["event_id"])
    _validate_event_type(event["event_type"])
    _validate_source(event["source"])
    _validate_timestamp(event["timestamp"])
    _validate_payload(event["payload"])


def _validate_required_fields(event: dict) -> None:
    missing = REQUIRED_FIELDS - event.keys()
    if missing:
        raise ValidationError(
            ErrorCodes.MISSING_FIELDS,
            f"Missing required fields: {', '.join(missing)}"
        )


def _validate_event_id(event_id: str) -> None:
    if not isinstance(event_id, str) or not event_id.strip():
        raise ValidationError(ErrorCodes.INVALID_EVENT_ID)

    try:
        uuid.UUID(event_id)
    except ValueError:
        raise ValidationError(ErrorCodes.INVALID_EVENT_ID)


def _validate_event_type(event_type: str) -> None:
    if not isinstance(event_type, str) or not event_type.strip():
        raise ValidationError(ErrorCodes.INVALID_EVENT_ID)


def _validate_source(source: str) -> None:
    if not isinstance(source, str) or not source.strip():
        raise ValidationError(ErrorCodes.INVALID_SOURCE)


def _validate_timestamp(ts: str) -> None:
    try:
        event_time = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        raise ValidationError(ErrorCodes.INVALID_TIMESTAMP)

    now = datetime.now(timezone.utc)

    if event_time > now:
        raise ValidationError(ErrorCodes.INVALID_TIMESTAMP)

    if event_time < now - timedelta(days=30):
        raise ValidationError(ErrorCodes.INVALID_TIMESTAMP)


def _validate_payload(payload) -> None:
    if payload is None:
        raise ValidationError(ErrorCodes.INVALID_PAYLOAD)

    try:
        json.dumps(payload)
    except TypeError:
        raise ValidationError(ErrorCodes.INVALID_PAYLOAD)

    if len(json.dumps(payload)) > 256_000:
        raise ValidationError(ErrorCodes.INVALID_PAYLOAD)