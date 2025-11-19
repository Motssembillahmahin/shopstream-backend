import os
import boto3

TABLE = os.environ["TABLE_NAME"]
ddb = boto3.client("dynamodb")


def lambda_handler(event, context):
    # event contains multiple records
    for record in event.get("Records", []):
        if record["eventName"] not in ("INSERT", "MODIFY"):
            continue
        new = record["dynamodb"].get("NewImage")
        if not new:
            continue
        entity = new.get("EntityType", {}).get("S")
        if entity == "UserEvent":
            event_type = new.get("EventType", {}).get("S")
            product_id = new.get("ProductId", {}).get("S").split("#", 1)[1]
            ts = int(new.get("TS", {}).get("N"))
            # compute date (UTC)
            from datetime import datetime, timezone

            date_str = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
            pk = f"PRODUCT#{product_id}"
            sk = f"AGG#{date_str}"
            if event_type == "VIEW":
                # atomic counter on aggregate item
                ddb.update_item(
                    TableName=TABLE,
                    Key={"PK": {"S": pk}, "SK": {"S": sk}},
                    UpdateExpression="ADD Views :inc",
                    ExpressionAttributeValues={":inc": {"N": "1"}},
                    ReturnValues="NONE",
                )
