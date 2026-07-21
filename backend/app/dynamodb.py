import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config import settings


class DynamoDBConfigurationError(RuntimeError):
    """Raised when DynamoDB configuration is missing or invalid."""


def get_dynamodb_resource():
    if not settings.aws_region:
        raise DynamoDBConfigurationError("AWS_REGION is not configured.")

    return boto3.resource("dynamodb", region_name=settings.aws_region)


def get_courses_table():
    if not settings.dynamodb_courses_table:
        raise DynamoDBConfigurationError(
            "DYNAMODB_COURSES_TABLE is not configured."
        )

    dynamodb = get_dynamodb_resource()
    return dynamodb.Table(settings.dynamodb_courses_table)


def get_database_status() -> dict:
    try:
        get_courses_table()

        return {
            "status": "configured",
            "database": "AWS DynamoDB",
            "region": settings.aws_region,
            "courses_table": settings.dynamodb_courses_table,
        }

    except DynamoDBConfigurationError as error:
        return {
            "status": "configuration_error",
            "database": "AWS DynamoDB",
            "message": str(error),
        }

    except (BotoCoreError, ClientError) as error:
        return {
            "status": "connection_error",
            "database": "AWS DynamoDB",
            "message": str(error),
        }