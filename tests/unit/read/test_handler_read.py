import json
from unittest.mock import patch

from read.handler import handler
from read.errors import EventNotFound


# -----------------------------
# HELPERS
# -----------------------------

def build_event(event_id=None):
    event = {}

    if event_id:
        event["pathParameters"] = {"event_id": event_id}

    return event


# -----------------------------
# SUCCESS CASE
# -----------------------------

@patch("read.handler.get_event")
@patch("read.handler.get_correlation_id", return_value="corr-1")
def test_handler_success(mock_corr, mock_get_event):

    mock_get_event.return_value = {
        "event_id": "evt-1",
        "payload": {"x": 1},
    }

    response = handler(build_event("evt-1"), None)

    assert response["statusCode"] == 200

    body = json.loads(response["body"])
    assert body["event_id"] == "evt-1"
    assert body["payload"]["x"] == 1

    mock_get_event.assert_called_once_with("evt-1")


# -----------------------------
# MISSING PATH PARAM
# -----------------------------

def test_handler_missing_event_id():

    response = handler({}, None)

    assert response["statusCode"] == 400

    body = json.loads(response["body"])
    assert body["error"] == "InvalidRequest"
    assert "event_id" in body["message"]


# -----------------------------
# NOT FOUND
# -----------------------------

@patch("read.handler.get_event", side_effect=EventNotFound())
@patch("read.handler.get_correlation_id", return_value="corr-1")
def test_handler_not_found(mock_corr, mock_get_event):

    response = handler(build_event("missing-id"), None)

    assert response["statusCode"] == 404

    body = json.loads(response["body"])
    assert body["error"] == "EventNotFound"


# -----------------------------
# UNEXPECTED ERROR
# -----------------------------

@patch("read.handler.get_event", side_effect=Exception("boom"))
@patch("read.handler.get_correlation_id", return_value="corr-1")
def test_handler_unexpected_error(mock_corr, mock_get_event):

    response = handler(build_event("evt-1"), None)

    assert response["statusCode"] == 500

    body = json.loads(response["body"])
    assert body["error"] == "InternalError"