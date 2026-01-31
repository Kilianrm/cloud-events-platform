import boto3
import pytest
from moto import mock_aws
from read.persistence import get_event
from read.errors import EventNotFound
import os


@mock_aws
def test_get_event_not_found():
    os.environ["TABLE_NAME"] = "events"
    os.environ["AWS_REGION"] = "us-east-1"
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    dynamodb.create_table(
        TableName="events",
        KeySchema=[{"AttributeName": "event_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "event_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    with pytest.raises(EventNotFound):
        get_event("missing-id")


@mock_aws
def test_get_event_success():
    os.environ["TABLE_NAME"] = "events"
    os.environ["AWS_REGION"] = "us-east-1"
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    table = dynamodb.create_table(
        TableName="events",
        KeySchema=[{"AttributeName": "event_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "event_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    table.put_item(
        Item={
            "event_id": "evt-1",
            "event_type": "TEST",
            "source": "unit-test",
            "timestamp": "2026-03-01T12:00:00Z",
            "payload": {"x": 1},
            "ingestion_time": "2026-03-01T12:01:00Z",
        }
    )

    event = get_event("evt-1")

    assert event["event_id"] == "evt-1"
    assert event["payload"]["x"] == 1

