import boto3
import pytest
from moto import mock_aws
from ingestion.persistence import persist_event
from ingestion.errors import EventAlreadyExists
import os



@mock_aws
def test_persist_event_creates_item():
    os.environ["TABLE_NAME"] = "events"
    os.environ["AWS_REGION"] = "us-east-1"

    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    dynamodb.create_table(
        TableName="events",
        KeySchema=[{"AttributeName": "event_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "event_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    event = {
        "event_id": "evt-1",
        "event_type": "TEST",
        "source": "test",
        "timestamp": "2026-03-01T12:00:00Z",
        "payload": {},
    }

    persist_event(event)

    table = dynamodb.Table("events")
    item = table.get_item(Key={"event_id": "evt-1"})["Item"]

    assert item["event_id"] == "evt-1"


@mock_aws
def test_persist_event_idempotent():
    os.environ["TABLE_NAME"] = "events"
    os.environ["AWS_REGION"] = "us-east-1"
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    dynamodb.create_table(
        TableName="events",
        KeySchema=[{"AttributeName": "event_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "event_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    event = {
        "event_id": "evt-1",
        "event_type": "TEST",
        "source": "test",
        "timestamp": "2026-03-01T12:00:00Z",
        "payload": {},
    }

    persist_event(event)

    with pytest.raises(EventAlreadyExists):
        persist_event(event)
