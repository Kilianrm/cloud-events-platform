import json
import pytest
from unittest.mock import patch

from ingestion.handler import handler
from ingestion.errors import EventAlreadyExists


# -----------------------------
# HELPERS
# -----------------------------

def sqs_event(body, message_id="msg-1"):
    return {
        "Records": [
            {
                "messageId": message_id,
                "body": json.dumps(body)
            }
        ]
    }


def valid_event():
    return {
        "event_id": "123",
        "event_type": "image_uploaded",
        "source": "api",
        "timestamp": "2026-01-01T10:00:00+00:00",
        "payload": {"image_id": "1"},
    }


# -----------------------------
# SUCCESS CASE
# -----------------------------

@patch("ingestion.handler.persist_event")
@patch("ingestion.handler.get_correlation_id", return_value="corr-1")
def test_ingestion_success(mock_corr, mock_persist):
    event = sqs_event(valid_event())

    handler(event, None)

    mock_persist.assert_called_once()


# -----------------------------
# DUPLICATE EVENT
# -----------------------------

@patch("ingestion.handler.persist_event", side_effect=EventAlreadyExists())
@patch("ingestion.handler.get_correlation_id", return_value="corr-1")
def test_ingestion_duplicate_event(mock_corr, mock_persist):
    event = sqs_event(valid_event())
    handler(event, None)

    mock_persist.assert_called_once()


# -----------------------------
# UNEXPECTED ERROR MARKS FAILURE
# -----------------------------

@patch("ingestion.handler.persist_event", side_effect=Exception("boom"))
@patch("ingestion.handler.get_correlation_id", return_value="corr-1")
def test_ingestion_unexpected_error_marks_failure(mock_corr, mock_persist):
    event = sqs_event(valid_event())

    result = handler(event, None)

    assert result == {
        "batchItemFailures": [
            {"itemIdentifier": event["Records"][0]["messageId"]}
        ]
    }


# -----------------------------
# BATCH PROCESSING (SQS MULTIPLE RECORDS)
# -----------------------------

@patch("ingestion.handler.persist_event")
@patch("ingestion.handler.get_correlation_id", return_value="corr-1")
def test_ingestion_batch_processing(mock_corr, mock_persist):
    event = {
        "Records": [
            {"body": json.dumps(valid_event())},
            {"body": json.dumps(valid_event())},
            {"body": json.dumps(valid_event())},
        ]
    }

    handler(event, None)

    assert mock_persist.call_count == 3