import json
import os
import boto3
from moto import mock_aws
from unittest.mock import patch

from ingestion.handler import handler as ingestion_handler


def valid_event():
    return {
        "event_id": "evt-retry-1",
        "event_type": "TEST",
        "source": "test",
        "timestamp": "2026-01-01T10:00:00Z",
        "payload": {"x": 1},
    }


def sqs_record(message_id, body):
    return {
        "messageId": message_id,
        "body": json.dumps(body)
    }


@mock_aws
def test_ingestion_retry_behavior_is_handled_correctly():
    """
    🧠 RETRY SIMULATION TEST (SQS + Lambda failure recovery)

    PURPOSE:
    This test validates how the system behaves under SQS retry conditions.

    In AWS SQS:
    - If a Lambda fails (exception, timeout, or unhandled error),
      the message is NOT deleted from the queue.
    - Instead, SQS retries delivering the same message.

    WHAT WE SIMULATE:
    We simulate a transient failure in the persistence layer (DynamoDB write failure)
    during the first attempt, and then a successful retry.

    EXPECTED BEHAVIOR:
    1. First execution:
       - persist_event fails
       - message is marked as failed via batchItemFailures
       - SQS will retry the message

    2. Second execution:
       - persist_event succeeds
       - event is stored in DynamoDB
       - no duplicates are created

    3. Final state:
       - exactly one record in DynamoDB
       - system recovered correctly from transient failure
    """

    # -----------------------------
    # ARRANGE AWS
    # -----------------------------
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

    # -----------------------------
    # ACT 1 — SIMULATE FAILURE
    # -----------------------------
    with patch(
        "ingestion.handler.persist_event",
        side_effect=Exception("Transient DB error")
    ):
        response = ingestion_handler(event, None)

    # Lambda should mark message as failed (triggering SQS retry)
    assert response["batchItemFailures"] == [
        {"itemIdentifier": "msg-1"}
    ]

    # -----------------------------
    # ACT 2 — RETRY SUCCESS
    # -----------------------------
    response = ingestion_handler(event, None)

    # Now processing should succeed
    assert response["batchItemFailures"] == []

    # -----------------------------
    # ASSERT FINAL STATE
    # -----------------------------
    items = table.scan()["Items"]

    assert len(items) == 1
    assert items[0]["event_id"] == "evt-retry-1"