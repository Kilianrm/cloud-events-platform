import pytest
from datetime import datetime, timezone, timedelta
import uuid

from validation.validators import validate_event
from validation.errors import ValidationError, ErrorCodes


# -----------------------------
# Helpers
# -----------------------------

def base_event():
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": "image_uploaded",
        "source": "api",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": {"image_id": "123"},
    }


# -----------------------------
# SUCCESS CASE
# -----------------------------

def test_valid_event_passes():
    event = base_event()
    validate_event(event)  # no exception


# -----------------------------
# REQUIRED FIELDS
# -----------------------------

def test_missing_field_fails():
    event = base_event()
    del event["source"]

    with pytest.raises(ValidationError) as exc:
        validate_event(event)

    assert exc.value.code == ErrorCodes.MISSING_FIELDS


# -----------------------------
# EVENT ID VALIDATION
# -----------------------------

def test_invalid_event_id_fails():
    event = base_event()
    event["event_id"] = "not-a-uuid"

    with pytest.raises(ValidationError) as exc:
        validate_event(event)

    assert exc.value.code == ErrorCodes.INVALID_EVENT_ID


# -----------------------------
# SOURCE VALIDATION
# -----------------------------

def test_empty_source_fails():
    event = base_event()
    event["source"] = "   "

    with pytest.raises(ValidationError) as exc:
        validate_event(event)

    assert exc.value.code == ErrorCodes.INVALID_SOURCE


# -----------------------------
# TIMESTAMP VALIDATION
# -----------------------------

def test_future_timestamp_fails():
    event = base_event()
    future = datetime.now(timezone.utc) + timedelta(days=1)
    event["timestamp"] = future.isoformat()

    with pytest.raises(ValidationError) as exc:
        validate_event(event)

    assert exc.value.code == ErrorCodes.INVALID_TIMESTAMP


def test_invalid_timestamp_format_fails():
    event = base_event()
    event["timestamp"] = "invalid-date"

    with pytest.raises(ValidationError) as exc:
        validate_event(event)

    assert exc.value.code == ErrorCodes.INVALID_TIMESTAMP


def test_too_old_timestamp_fails():
    event = base_event()
    old = datetime.now(timezone.utc) - timedelta(days=365)
    event["timestamp"] = old.isoformat()

    with pytest.raises(ValidationError) as exc:
        validate_event(event)

    assert exc.value.code == ErrorCodes.INVALID_TIMESTAMP


# -----------------------------
# PAYLOAD VALIDATION
# -----------------------------

def test_null_payload_fails():
    event = base_event()
    event["payload"] = None

    with pytest.raises(ValidationError) as exc:
        validate_event(event)

    assert exc.value.code == ErrorCodes.INVALID_PAYLOAD


def test_non_serializable_payload_fails():
    event = base_event()
    event["payload"] = set([1, 2, 3])  # not JSON serializable

    with pytest.raises(ValidationError) as exc:
        validate_event(event)

    assert exc.value.code == ErrorCodes.INVALID_PAYLOAD


def test_payload_too_large_fails():
    event = base_event()
    event["payload"] = {"data": "x" * 300_000}

    with pytest.raises(ValidationError) as exc:
        validate_event(event)

    assert exc.value.code == ErrorCodes.INVALID_PAYLOAD