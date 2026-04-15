import pytest
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError

from ingestion.persistence import persist_event
from ingestion.errors import EventAlreadyExists


# -----------------------------
# HELPERS
# -----------------------------

def base_event():
    return {
        "event": {
            "event_id": "evt-1",
            "event_type": "TEST",
            "source": "integration-test",
            "timestamp": "2026-03-01T12:00:00Z",
            "payload": {"x": 1}
        }
    }


# -----------------------------
# SUCCESS CASE
# -----------------------------

@patch("ingestion.persistence.boto3.resource")
@patch.dict("os.environ", {"TABLE_NAME": "events", "AWS_REGION": "us-east-1"})
def test_persist_event_success(mock_boto_resource):
    mock_table = MagicMock()
    mock_dynamodb = MagicMock()

    mock_dynamodb.Table.return_value = mock_table
    mock_boto_resource.return_value = mock_dynamodb

    event = base_event()

    persist_event(event)

    mock_table.put_item.assert_called_once()

    args, kwargs = mock_table.put_item.call_args

    assert kwargs["Item"]["event"]["event_id"] == "evt-1"
    assert "ingestion_time" in kwargs["Item"]
    assert kwargs["ConditionExpression"] == "attribute_not_exists(event_id)"


# -----------------------------
# DUPLICATE EVENT (ConditionalCheckFailedException)
# -----------------------------

@patch("ingestion.persistence.boto3.resource")
@patch.dict("os.environ", {"TABLE_NAME": "events", "AWS_REGION": "us-east-1"})
def test_persist_event_duplicate_raises_custom_error(mock_boto_resource):
    mock_table = MagicMock()
    mock_dynamodb = MagicMock()

    mock_dynamodb.Table.return_value = mock_table
    mock_boto_resource.return_value = mock_dynamodb

    error_response = {
        "Error": {
            "Code": "ConditionalCheckFailedException",
            "Message": "duplicate"
        }
    }

    mock_table.put_item.side_effect = ClientError(error_response, "PutItem")

    event = base_event()

    with pytest.raises(EventAlreadyExists):
        persist_event(event)


# -----------------------------
# OTHER AWS ERROR (RE-RAISED)
# -----------------------------

@patch("ingestion.persistence.boto3.resource")
@patch.dict("os.environ", {"TABLE_NAME": "events", "AWS_REGION": "us-east-1"})
def test_persist_event_unexpected_client_error(mock_boto_resource):
    mock_table = MagicMock()
    mock_dynamodb = MagicMock()

    mock_dynamodb.Table.return_value = mock_table
    mock_boto_resource.return_value = mock_dynamodb

    error_response = {
        "Error": {
            "Code": "ProvisionedThroughputExceededException",
            "Message": "throttled"
        }
    }

    mock_table.put_item.side_effect = ClientError(error_response, "PutItem")

    event = base_event()

    with pytest.raises(ClientError):
        persist_event(event)