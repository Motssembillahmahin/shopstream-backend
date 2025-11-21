import os
import boto3
from datetime import datetime, timezone

TABLE = os.environ["TABLE_NAME"]
ddb = boto3.client("dynamodb")


def lambda_handler(event, context):
    for record in event.get("Records", []):
        try:
            if record["eventName"] not in ("INSERT", "MODIFY"):
                continue

            new_image = record["dynamodb"].get("NewImage")
            if not new_image:
                continue

            # Extract entity type safely
            entity = new_image.get("EntityType", {}).get("S")
            if entity != "UserEvent":
                continue

            event_type = new_image.get("EventType", {}).get("S")
            if event_type != "VIEW":
                continue

            product_id_field = new_image.get("ProductId", {}).get("S", "")
            if not product_id_field or "#" not in product_id_field:
                print(f"Invalid ProductId format: {product_id_field}")
                continue

            product_id = product_id_field.split("#", 1)[1]
            ts = int(new_image.get("TS", {}).get("N", 0))

            # Compute date
            date_str = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")

            # Update aggregate
            pk = f"PRODUCT#{product_id}"
            sk = f"AGG#{date_str}"

            ddb.update_item(
                TableName=TABLE,
                Key={"PK": {"S": pk}, "SK": {"S": sk}},
                UpdateExpression="ADD ViewCount :inc SET EntityType = :type, #d = :date",
                ExpressionAttributeNames={
                    "#d": "Date"  # 'Date' might be a reserved word
                },
                ExpressionAttributeValues={
                    ":inc": {"N": "1"},
                    ":type": {"S": "ProductAggregate"},
                    ":date": {"S": date_str},
                },
            )

        except Exception as e:
            print(f"Error processing record: {e}")
            print(f"Record: {record}")
            # Optionally: send to DLQ or error tracking
            continue

    return {"statusCode": 200, "body": "Processed"}
