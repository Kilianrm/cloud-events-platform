import boto3
import os
from read.errors import EventNotFound


def get_event(event_id: str) -> dict:
    table_name = os.environ.get("TABLE_NAME", "events")
    region = os.environ.get("AWS_REGION", "us-east-1")

    dynamodb = boto3.resource("dynamodb", region_name=region)
    table = dynamodb.Table(table_name)

    response = table.get_item(
        Key={"event_id": event_id},
        ConsistentRead=True,
    )

    if "Item" not in response:
        raise EventNotFound(event_id)

    return response["Item"]
