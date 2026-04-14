import uuid
import time
import requests
import boto3
from datetime import datetime, timezone, timedelta


dynamodb = boto3.resource("dynamodb")


def wait_for_event(table, event_id: str, timeout: int = 15):
    start = time.time()

    while time.time() - start < timeout:
        response = table.get_item(Key={"event_id": event_id})

        if "Item" in response:
            return response["Item"]

        time.sleep(1)

    return None


def test_event_reaches_dynamodb(get_jwt_token, api_base_url, table_name):
    """
    E2E test:
    API → authentication -> authorization -> validation → SQS → ingestion → DynamoDB
    """


    token = get_jwt_token("client1", "super-secret-pass1")

    event_id = str(uuid.uuid4())

    payload = {
        "event_id": event_id,
        "event_type": "SMOKE",
        "source": "smoke-test",
        "timestamp": (
            datetime.now(timezone.utc) - timedelta(minutes=1)
        ).isoformat(),
        "payload": {"x": 1}
    }

    # 1. send event
    resp = requests.post(
        f"{api_base_url}/events",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert resp.status_code == 202

    # 2. wait async
    table = dynamodb.Table(table_name)
    item = wait_for_event(table, event_id)

    # 3. assert final state
    assert item is not None
    assert item["event_id"] == event_id