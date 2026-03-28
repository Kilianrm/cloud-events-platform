import json
import uuid
from unittest.mock import patch
from shared.logging_utils import log, get_correlation_id

# --- log tests ---
@patch("builtins.print")
def test_log_basic(mock_print):
    log("Test message")
    # Get the JSON printed
    printed_json = mock_print.call_args[0][0]
    log_data = json.loads(printed_json)

    # Check basic fields
    assert log_data["message"] == "Test message"
    assert log_data["level"] == "info"
    assert log_data["correlation_id"] is None

@patch("builtins.print")
def test_log_with_extra_fields(mock_print):
    log("Another message", user="alice", ip="127.0.0.1")
    printed_json = mock_print.call_args[0][0]
    log_data = json.loads(printed_json)

    # Check extra fields merged
    assert log_data["user"] == "alice"
    assert log_data["ip"] == "127.0.0.1"

# --- get_correlation_id tests ---
def test_get_correlation_id_from_header():
    event = {"headers": {"X-Correlation-Id": "header-id-123"}}
    result = get_correlation_id(event)
    assert result == "header-id-123"

def test_get_correlation_id_from_request_context():
    event = {"requestContext": {"requestId": "req-id-456"}}
    result = get_correlation_id(event)
    assert result == "req-id-456"

def test_get_correlation_id_fallback_uuid():
    event = {}
    result = get_correlation_id(event)
    # Validate that it is a valid UUID
    uuid_obj = uuid.UUID(result)
    assert str(uuid_obj) == result