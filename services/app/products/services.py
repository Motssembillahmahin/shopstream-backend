import os
import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.client("dynamodb")
TABLE = os.environ.get("TABLE_NAME", "ShopStreamMain")


def create_order_transaction(order_id: str, user_id: str, items: list):
    transact_items = []
    # Put order item
    order_item = {
        "PK": {"S": f"ORDER#{order_id}"},
        "SK": {"S": "METADATA"},
        "EntityType": {"S": "Order"},
        "UserId": {"S": f"USER#{user_id}"},
        # add Items, TS, Status...
    }
    transact_items.append({"Put": {"TableName": TABLE, "Item": order_item}})

    # Update inventory for each product
    for it in items:
        key = {"PK": {"S": f"PRODUCT#{it['product_id']}"}, "SK": {"S": "METADATA"}}
        update = {
            "TableName": TABLE,
            "Key": key,
            "UpdateExpression": "SET Inventory = Inventory - :q",
            "ConditionExpression": "Inventory >= :q",
            "ExpressionAttributeValues": {":q": {"N": str(it["qty"])}},
        }
        transact_items.append({"Update": update})

    try:
        dynamodb.transact_write_items(TransactItems=transact_items)
        return True
    except ClientError:
        # handle ConditionalCheckFailed
        raise
