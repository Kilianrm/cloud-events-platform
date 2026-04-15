import json
import os
import boto3
from moto import mock_aws

from ingestion.handler import handler as ingestion_handler


# -----------------------------
# HELPERS
# -----------------------------
def valid_event():
    return {
        "event": {
            "event_id": "evt-1",
            "event_type": "TEST",
            "source": "integration-test",
            "timestamp": "2026-03-01T12:00:00Z",
            "payload": {"x": 1}
        }
    }


def sqs_record(message_id, body=None):
    record = {"messageId": message_id}
    if body is not None:
        record["body"] = json.dumps(body) if isinstance(body, dict) else body
    return record


# -----------------------------
# TEST 1: HAPPY PATH
# -----------------------------
@mock_aws
def test_ingestion_processes_event_and_persists():

    os.environ["TABLE_NAME"] = "events"

    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    table = dynamodb.create_table(
        TableName="events",
        KeySchema=[
            {"AttributeName": "event_id", "KeyType": "HASH"}
        ],
        AttributeDefinitions=[
            {"AttributeName": "event_id", "AttributeType": "S"}
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    event = {
        "Records": [
            sqs_record("msg-1", valid_event())
        ]
    }

    response = ingestion_handler(event, None)

    # ✔ no failures
    assert response == {"batchItemFailures": []}

    # ✔ persisted
    item = table.get_item(Key={"event_id": "evt-1"})
    assert "Item" in item
    assert item["Item"]["event_id"] == "evt-1"


# -----------------------------
# TEST 2: INVALID JSON
# -----------------------------
@mock_aws
def test_ingestion_invalid_json_is_failed():

    os.environ["TABLE_NAME"] = "events"

    boto3.resource("dynamodb", region_name="us-east-1").create_table(
        TableName="events",
        KeySchema=[{"AttributeName": "event_id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "event_id", "AttributeType": "S"}
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    event = {
        "Records": [
            sqs_record("msg-1", "{invalid-json")
        ]
    }

    response = ingestion_handler(event, None)

    assert response == {
        "batchItemFailures": [
            {"itemIdentifier": "msg-1"}
        ]
    }


# -----------------------------
# TEST 3: MISSING BODY
# -----------------------------
@mock_aws
def test_ingestion_missing_body_is_failed():

    os.environ["TABLE_NAME"] = "events"

    boto3.resource("dynamodb", region_name="us-east-1").create_table(
        TableName="events",
        KeySchema=[{"AttributeName": "event_id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "event_id", "AttributeType": "S"}
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    event = {
        "Records": [
            {"messageId": "msg-1"}  # no body
        ]
    }

    response = ingestion_handler(event, None)

    assert response == {
        "batchItemFailures": [
            {"itemIdentifier": "msg-1"}
        ]
    }


# -----------------------------
# TEST 4: PARTIAL FAILURE BATCH
# -----------------------------
@mock_aws
def test_ingestion_partial_failure_batch():

    os.environ["TABLE_NAME"] = "events"

    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

    table = dynamodb.create_table(
        TableName="events",
        KeySchema=[
            {"AttributeName": "event_id", "KeyType": "HASH"}
        ],
        AttributeDefinitions=[
            {"AttributeName": "event_id", "AttributeType": "S"}
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    event = {
        "Records": [
            sqs_record("ok-1", valid_event()),
            sqs_record("bad-1", "{invalid-json"),
            sqs_record("ok-2", valid_event()),
        ]
    }

    response = ingestion_handler(event, None)

    # ✔ only failed message returned
    assert response == {
        "batchItemFailures": [
            {"itemIdentifier": "bad-1"}
        ]
    }

    # ✔ successful ones persisted
    item = table.get_item(Key={"event_id": "evt-1"})
    assert "Item" in item