import os

import boto3

from read.errors import EventNotFound

# Created once per Lambda container, at import time. Lambda runs module-level code
# during init, which gets more CPU than the request itself; importing boto3 inside
# the request made reads on a 128 MB function exceed the 5s timeout.
_table = boto3.resource(
    "dynamodb",
    region_name=os.environ.get("AWS_REGION", "us-east-1"),
).Table(os.environ.get("TABLE_NAME", "events"))


def get_table():
    return _table


def get_event(event_id: str, table=None) -> dict:
    table = table or get_table()

    response = table.get_item(
        Key={"event_id": event_id},
        ConsistentRead=True,
    )

    if "Item" not in response:
        raise EventNotFound(event_id)

    return response["Item"]
