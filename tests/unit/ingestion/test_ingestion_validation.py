import pytest
from ingestion.validation import validate_event
from ingestion.errors import ValidationError


def test_valid_event_passes():
    event = {
        "event_id": "evt-1",
        "event_type": "TEST",
        "source": "test",
        "timestamp": "2026-03-01T12:00:00Z",
        "payload": {},
    }

    validate_event(event)  # no exception


def test_missing_field_fails():
    event = {
        "event_id": "evt-1",
        "source": "test",
        "timestamp": "2026-03-01T12:00:00Z",
        "payload": {},
    }

    with pytest.raises(ValidationError):
        validate_event(event)
