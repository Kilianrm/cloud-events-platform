import json
import pytest
from unittest.mock import patch, MagicMock

from validation.handler import handler
from validation.errors import ValidationError


def build_event(body=None):
    event = {}
    if body is not None:
        event["body"] = json.dumps(body)
    return event


def valid_body():
    return {
        "event_id": "123e4567-e89b-12d3-a456-426614174000",
        "event_type": "image_uploaded",
        "source": "api",
        "timestamp": "2026-01-01T10:00:00+00:00",
        "payload": {"image_id": "123"},
    }


# -----------------------------
# FIXTURES
# -----------------------------

@pytest.fixture
def mock_queue_env():
    with patch.dict("os.environ", {"QUEUE_URL": "https://mock-queue-url"}):
        yield


# -----------------------------
# SUCCESS CASE
# -----------------------------

@patch("validation.handler.get_sqs")
@patch("validation.handler.validate_event")
def test_handler_valid_request_returns_202(mock_validate, mock_get_sqs, mock_queue_env):

    mock_sqs_client = MagicMock()
    mock_get_sqs.return_value = mock_sqs_client

    response = handler(build_event(valid_body()), None)

    assert response["statusCode"] == 202

    body = json.loads(response["body"])
    assert body["status"] == "accepted"
    assert body["event_id"] == valid_body()["event_id"]

    mock_validate.assert_called_once()
    mock_sqs_client.send_message.assert_called_once()


# -----------------------------
# MISSING BODY
# -----------------------------

def test_handler_missing_body_returns_400():
    response = handler({}, None)

    assert response["statusCode"] == 400

    body = json.loads(response["body"])
    assert body["error"] == "INVALID_REQUEST"


# -----------------------------
# VALIDATION ERROR
# -----------------------------

@patch("validation.handler.validate_event")
def test_handler_validation_error_returns_400(mock_validate):
    mock_validate.side_effect = ValidationError(
        "INVALID_TIMESTAMP",
        "timestamp invalid"
    )

    response = handler(build_event(valid_body()), None)

    assert response["statusCode"] == 400

    body = json.loads(response["body"])
    assert body["error"] == "INVALID_TIMESTAMP"
    assert body["message"] == "timestamp invalid"


# -----------------------------
# UNEXPECTED ERROR
# -----------------------------

@patch("validation.handler.validate_event")
def test_handler_unexpected_error_returns_500(mock_validate):
    mock_validate.side_effect = Exception("boom")

    response = handler(build_event(valid_body()), None)

    assert response["statusCode"] == 500

    body = json.loads(response["body"])
    assert body["error"] == "INTERNAL_ERROR"