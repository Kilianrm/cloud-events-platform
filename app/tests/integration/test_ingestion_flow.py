import boto3
import json
from moto import mock_aws
from ingestion.handler import handler as ingest
from read.handler import handler as read

@mock_aws
def test_ingest_then_read():
    import os
    os.environ["TABLE_NAME"] = "events"
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")


    dynamodb.create_table(
        TableName="events",
        KeySchema=[{"AttributeName": "event_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "event_id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    event_body = {
        "event_id": "evt-1",
        "event_type": "TEST",
        "source": "integration-test",
        "timestamp": "2026-03-01T12:00:00Z",
        "payload": {"x": 1},
    }

    ingest(
        {"body": json.dumps(event_body)},
        None,
    )

    response = read(
        {"pathParameters": {"event_id": "evt-1"}},
        None,
    )

    assert response["statusCode"] == 200
    data = json.loads(response["body"])
    assert data["event_id"] == "evt-1"
    assert "ingestion_time" in data
