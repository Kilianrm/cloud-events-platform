import os
from read.errors import EventNotFound


def get_table():
    import boto3

    region = os.environ.get("AWS_REGION", "us-east-1")
    table_name = os.environ.get("TABLE_NAME", "events")

    dynamodb = boto3.resource("dynamodb", region_name=region)
    return dynamodb.Table(table_name)


def get_event(event_id: str, table=None) -> dict:
    table = table or get_table()

    response = table.get_item(
        Key={"event_id": event_id},
        ConsistentRead=True,
    )

    if "Item" not in response:
        raise EventNotFound(event_id)

    return response["Item"]