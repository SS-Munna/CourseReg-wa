from decimal import Decimal
from typing import Any, Optional

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


def normalize_text(value: Optional[str]) -> str:
    return value.strip().lower() if value else ""


def course_matches_filters(
    course: dict,
    search: Optional[str] = None,
    department: Optional[str] = None,
    semester: Optional[str] = None,
    is_mandatory: Optional[bool] = None,
    available_only: bool = False,
) -> bool:
    search_text = normalize_text(search)
    department_filter = normalize_text(department)
    semester_filter = normalize_text(semester)

    course_code = normalize_text(course.get("code"))
    course_title = normalize_text(course.get("title"))
    course_department = normalize_text(course.get("department"))
    course_semester = normalize_text(course.get("semester"))

    if search_text and search_text not in course_code and search_text not in course_title:
        return False

    if department_filter and department_filter != course_department:
        return False

    if semester_filter and semester_filter != course_semester:
        return False

    if is_mandatory is not None and course.get("is_mandatory") != is_mandatory:
        return False

    if available_only and int(course.get("available_seats", 0)) <= 0:
        return False

    return True


def filter_course_items(
    courses: list[dict],
    search: Optional[str] = None,
    department: Optional[str] = None,
    semester: Optional[str] = None,
    is_mandatory: Optional[bool] = None,
    available_only: bool = False,
) -> list[dict]:
    return [
        course
        for course in courses
        if course_matches_filters(
            course=course,
            search=search,
            department=department,
            semester=semester,
            is_mandatory=is_mandatory,
            available_only=available_only,
        )
    ]


def list_courses(
    search: Optional[str] = None,
    department: Optional[str] = None,
    semester: Optional[str] = None,
    is_mandatory: Optional[bool] = None,
    available_only: bool = False,
) -> list[CourseResponse]:
    table = get_courses_table()
    course_items: list[dict] = []

    try:
        response = table.scan()

        while True:
            items = response.get("Items", [])

            for item in items:
                normalized_item = convert_decimal_values(item)
                course_items.append(normalized_item)

            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                break

            response = table.scan(ExclusiveStartKey=last_key)

        filtered_items = filter_course_items(
            courses=course_items,
            search=search,
            department=department,
            semester=semester,
            is_mandatory=is_mandatory,
            available_only=available_only,
        )

        return [CourseResponse(**course) for course in filtered_items]

    except (BotoCoreError, ClientError) as error:
        raise CourseRepositoryError(str(error)) from error