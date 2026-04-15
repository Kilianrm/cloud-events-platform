import json
import os
import boto3
import pytest
from datetime import datetime, timezone, timedelta
from moto import mock_aws
from validation.handler import handler as validation_handler


# -----------------------------
# FIXTURE: VALID EVENT
# -----------------------------

def valid_event():
    return {
        "event_id": "123e4567-e89b-12d3-a456-426614174000",
        "event_type": "image_uploaded",
        "source": "api",
        "timestamp": (
            datetime.now(timezone.utc) - timedelta(minutes=1)
        ).isoformat(),
        "payload": {"image_id": "123"},
    }


def build_lambda_event(body: dict):
    return {"body": json.dumps(body)}


# -----------------------------
# INTEGRATION TESTS
# -----------------------------

@mock_aws
def test_validation_accepts_valid_event_and_returns_202_and_sends_to_sqs():
    # -----------------------------
    # ARRANGE: AWS MOCK (SQS)
    # -----------------------------
    sqs = boto3.client("sqs", region_name="us-east-1")

    queue = sqs.create_queue(QueueName="validation-queue")
    queue_url = queue["QueueUrl"]

    os.environ["QUEUE_URL"] = queue_url

    # -----------------------------
    # ACT: call real lambda
    # -----------------------------
    event = build_lambda_event(valid_event())

    response = validation_handler(event, None)

    # -----------------------------
    # ASSERT: lambda response
    # -----------------------------
    assert response["statusCode"] == 202

    body = json.loads(response["body"])
    assert body["status"] == "accepted"
    assert body["event_id"] == valid_event()["event_id"]

    # -----------------------------
    # ASSERT: message in SQS
    # -----------------------------
    messages = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=1,
    )

    assert "Messages" in messages

    message_body = json.loads(messages["Messages"][0]["Body"])
    event = message_body["event"]

    assert event["event_id"] == valid_event()["event_id"]
    assert event["event_type"] == valid_event()["event_type"]
    assert event["source"] == valid_event()["source"]


# -----------------------------
# INVALID EVENT CASE
# -----------------------------

@mock_aws
def test_validation_rejects_invalid_event():
    sqs = boto3.client("sqs", region_name="us-east-1")

    queue = sqs.create_queue(QueueName="validation-queue")
    queue_url = queue["QueueUrl"]

    os.environ["QUEUE_URL"] = queue_url

    # missing event_type (invalid)
    invalid_event = {
        "event_id": "123e4567-e89b-12d3-a456-426614174000",
        "source": "api",
        "timestamp": "2026-01-01T10:00:00+00:00",
        "payload": {"image_id": "123"},
    }

    event = build_lambda_event(invalid_event)

    response = validation_handler(event, None)

    # -----------------------------
    # ASSERT: rejected
    # -----------------------------
    assert response["statusCode"] == 400

    body = json.loads(response["body"])
    assert "error" in body

    # -----------------------------
    # ASSERT: NO message sent to SQS
    # -----------------------------
    messages = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=1,
    )

    assert "Messages" not in messages