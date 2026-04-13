import pytest
from unittest.mock import MagicMock

from read.persistence import get_event
from read.errors import EventNotFound


# -----------------------------
# SUCCESS CASE
# -----------------------------

def test_get_event_success():

    mock_table = MagicMock()

    mock_table.get_item.return_value = {
        "Item": {
            "event_id": "evt-1",
            "event_type": "TEST",
            "source": "unit-test",
            "timestamp": "2026-03-01T12:00:00Z",
            "payload": {"x": 1},
            "ingestion_time": "2026-03-01T12:01:00Z",
        }
    }

    result = get_event("evt-1", table=mock_table)

    assert result["event_id"] == "evt-1"
    assert result["payload"]["x"] == 1

    mock_table.get_item.assert_called_once_with(
        Key={"event_id": "evt-1"},
        ConsistentRead=True,
    )


# -----------------------------
# NOT FOUND CASE
# -----------------------------

def test_get_event_not_found():

    mock_table = MagicMock()
    mock_table.get_item.return_value = {}  # no "Item"

    with pytest.raises(EventNotFound):
        get_event("missing-id", table=mock_table)

    mock_table.get_item.assert_called_once_with(
        Key={"event_id": "missing-id"},
        ConsistentRead=True,
    )