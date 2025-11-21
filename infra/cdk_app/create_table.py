import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.client("dynamodb", region_name="ap-southeast-1")


# helper function
def create_table():
    try:
        response = dynamodb.create_table(
            TableName="ShopStreamMain",
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
                {"AttributeName": "GSI1PK", "AttributeType": "S"},
                {"AttributeName": "GSI1SK", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "GSI1-EventsByDay",
                    "KeySchema": [
                        {"AttributeName": "GSI1PK", "KeyType": "HASH"},
                        {"AttributeName": "GSI1SK", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            BillingMode="PAY_PER_REQUEST",
            StreamSpecification={
                "StreamEnabled": True,
                "StreamViewType": "NEW_AND_OLD_IMAGES",
            },
        )

        print(f"✓ Table created: {response['TableDescription']['TableName']}")
        print("  Waiting for table to become active...")

        waiter = dynamodb.get_waiter("table_exists")
        waiter.wait(TableName="ShopStreamMain")

        print("✓ Table is now ACTIVE!")

    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print("✓ Table already exists!")
        else:
            print(f"✗ Error: {e}")
            raise


if __name__ == "__main__":
    create_table()
