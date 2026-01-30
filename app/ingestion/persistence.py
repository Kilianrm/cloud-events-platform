import boto3
import os
from ingestion.errors import EventAlreadyExists
from botocore.exceptions import ClientError
from datetime import datetime, timezone


def persist_event(event: dict) -> None:
    table_name = os.environ.get("TABLE_NAME", "events")
    region = os.environ.get("AWS_REGION", "us-east-1")

    dynamodb = boto3.resource("dynamodb", region_name=region)
    table = dynamodb.Table(table_name)

    item = {
        **event,
        "ingestion_time": datetime.now(timezone.utc).isoformat(),
    }

    try:
        table.put_item(
            Item=item,
            ConditionExpression="attribute_not_exists(event_id)",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise EventAlreadyExists()
        raise



