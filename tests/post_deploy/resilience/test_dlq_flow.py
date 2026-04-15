import boto3
import json
import time
import uuid
import pytest
import os
from dotenv import load_dotenv

load_dotenv()

QUEUE_URL = os.getenv("QUEUE_URL")
DLQ_URL = os.getenv("DLQ_URL")

if not QUEUE_URL:
    raise RuntimeError("API_BASE_URL is not set.")

if not DLQ_URL:
    raise RuntimeError("TABLE_NAME is not set.")    

def test_message_goes_to_dlq_after_3_failures():
    sqs = boto3.client("sqs")

    event_id = f"dlq-test-{uuid.uuid4()}"

    # 1. Enviar evento con test hook
    sqs.send_message(
        QueueUrl=QUEUE_URL,
        MessageBody=json.dumps({
            "event": {
                "event_id": event_id,
                "type": "duplicate-test"
            },
            "metadata": {
                "test": {
                    "force_fail": True
                }
            }
        })
    )

    # 2. Polling en DLQ
    timeout = 120
    start = time.time()

    while time.time() - start < timeout:

        response = sqs.receive_message(
            QueueUrl=DLQ_URL,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=10
        )

        for msg in response.get("Messages", []):
            body = json.loads(msg["Body"])

            event = body.get("event", {})

            if event.get("event_id") == event_id:
                return  # éxito

    pytest.fail(f"Event {event_id} was not found in DLQ within {timeout}s")