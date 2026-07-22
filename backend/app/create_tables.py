import argparse

from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError

from app.config import settings
from app.dynamodb import get_dynamodb_resource


def course_table_exists(table_name: str) -> bool:
    dynamodb = get_dynamodb_resource()
    client = dynamodb.meta.client

    try:
        client.describe_table(TableName=table_name)
        return True
    except client.exceptions.ResourceNotFoundException:
        return False


def create_course_table() -> dict:
    table_name = settings.dynamodb_courses_table

    if course_table_exists(table_name):
        return {
            "status": "exists",
            "table_name": table_name,
            "message": "Course table already exists.",
        }

    dynamodb = get_dynamodb_resource()

    table = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
            {
                "AttributeName": "course_id",
                "KeyType": "HASH",
            }
        ],
        AttributeDefinitions=[
            {
                "AttributeName": "course_id",
                "AttributeType": "S",
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    table.wait_until_exists()

    return {
        "status": "created",
        "table_name": table_name,
        "message": "Course table created successfully.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create required DynamoDB tables for CoursePilot."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show table setup information without creating tables.",
    )
    args = parser.parse_args()

    print("CoursePilot DynamoDB table setup")
    print(f"AWS region: {settings.aws_region}")
    print(f"Course table: {settings.dynamodb_courses_table}")

    if args.dry_run:
        print("Dry run complete. No table was created.")
        return

    try:
        result = create_course_table()
        print(result["message"])
        print(f"Status: {result['status']}")
        print(f"Table: {result['table_name']}")

    except NoCredentialsError:
        print("AWS credentials were not found.")
        print("Configure AWS credentials locally before creating the table.")

    except (BotoCoreError, ClientError) as error:
        print("DynamoDB table setup failed.")
        print(str(error))


if __name__ == "__main__":
    main()