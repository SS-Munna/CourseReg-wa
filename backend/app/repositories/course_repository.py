from decimal import Decimal
from typing import Any

from botocore.exceptions import BotoCoreError, ClientError

from app.dynamodb import get_courses_table
from app.schemas.course import CourseResponse


class CourseRepositoryError(RuntimeError):
    """Raised when course data cannot be retrieved from DynamoDB."""


def convert_decimal_values(value: Any) -> Any:
    if isinstance(value, list):
        return [convert_decimal_values(item) for item in value]

    if isinstance(value, dict):
        return {key: convert_decimal_values(item) for key, item in value.items()}

    if isinstance(value, Decimal):
        if value % 1 == 0:
            return int(value)
        return float(value)

    return value


def list_courses() -> list[CourseResponse]:
    table = get_courses_table()
    courses: list[CourseResponse] = []

    try:
        response = table.scan()

        while True:
            items = response.get("Items", [])

            for item in items:
                normalized_item = convert_decimal_values(item)
                courses.append(CourseResponse(**normalized_item))

            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                break

            response = table.scan(ExclusiveStartKey=last_key)

        return courses

    except (BotoCoreError, ClientError) as error:
        raise CourseRepositoryError(str(error)) from error