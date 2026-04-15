import json
import os
import boto3
from moto import mock_aws

from ingestion.handler import handler as ingestion_handler


def sqs_record(message_id, body):
    return {
        "messageId": message_id,
        "body": json.dumps(body)
    }


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


@mock_aws
def test_ingestion_is_idempotent():
    """
    🧠 IDEMPOTENCY TEST (SQS + DynamoDB)

    PURPOSE:
    This test validates that the ingestion system is idempotent under SQS at-least-once delivery semantics.

    In AWS SQS, the same message can be delivered more than once.
    Therefore, the system MUST guarantee that duplicate events do NOT create duplicate records.

    SCENARIO:
    - Two SQS messages are received
    - Both contain the same event_id (duplicate event)
    - ingestion_handler processes both messages

    EXPECTED BEHAVIOR:
    - Only one event is persisted in DynamoDB
    - The second duplicate event is ignored via idempotency logic (e.g., conditional write or EventAlreadyExists)
    - The Lambda does not report batch failures for valid processing flow
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
            sqs_record("msg-1", valid_event()),
            sqs_record("msg-2", valid_event()),  # DUPLICATE
        ]
    }

    # -----------------------------
    # ACT
    # -----------------------------
    response = ingestion_handler(event, None)

    # -----------------------------
    # ASSERT RESPONSE
    # -----------------------------
    assert response["batchItemFailures"] == []

    # -----------------------------
    # ASSERT STATE (CRITICAL PART)
    # -----------------------------
    items = table.scan()["Items"]

    assert len(items) == 1
    assert items[0]["event_id"] == "evt-1"