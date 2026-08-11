from dataclasses import dataclass

from fastapi import Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.api.errors import error_response_content


@dataclass(frozen=True)
class ConstraintResponse:
    status_code: int
    code: str
    message: str


CONSTRAINT_RESPONSES = {
    "uq_courses_course_id": ConstraintResponse(
        status_code=status.HTTP_409_CONFLICT,
        code="DUPLICATE_COURSE_ID",
        message="A course with this course ID already exists.",
    ),
    "uq_courses_code_semester_section": ConstraintResponse(
        status_code=status.HTTP_409_CONFLICT,
        code="DUPLICATE_COURSE_SECTION",
        message=(
            "This course section already exists for the selected semester."
        ),
    ),
    "ck_courses_credits_positive": ConstraintResponse(
        status_code=422,
        code="INVALID_COURSE_CREDITS",
        message="Course credits must be greater than zero.",
    ),
    "ck_courses_capacity_positive": ConstraintResponse(
        status_code=422,
        code="INVALID_SECTION_CAPACITY",
        message="Section capacity must be greater than zero.",
    ),
    "ck_courses_available_seats_nonnegative": ConstraintResponse(
        status_code=422,
        code="INVALID_AVAILABLE_SEATS",
        message="Available seats cannot be negative.",
    ),
    "ck_courses_available_seats_within_capacity": ConstraintResponse(
        status_code=422,
        code="INVALID_AVAILABLE_SEATS",
        message="Available seats cannot be greater than section capacity.",
    ),
    "ck_courses_course_id_not_blank": ConstraintResponse(
        status_code=422,
        code="INVALID_COURSE_ID",
        message="Course ID cannot be blank.",
    ),
    "ck_courses_code_not_blank": ConstraintResponse(
        status_code=422,
        code="INVALID_COURSE_CODE",
        message="Course code cannot be blank.",
    ),
    "ck_courses_title_not_blank": ConstraintResponse(
        status_code=422,
        code="INVALID_COURSE_TITLE",
        message="Course title cannot be blank.",
    ),
    "ck_courses_department_not_blank": ConstraintResponse(
        status_code=422,
        code="INVALID_COURSE_DEPARTMENT",
        message="Course department cannot be blank.",
    ),
    "ck_courses_semester_not_blank": ConstraintResponse(
        status_code=422,
        code="INVALID_COURSE_SEMESTER",
        message="Course semester cannot be blank.",
    ),
    "ck_courses_instructor_not_blank": ConstraintResponse(
        status_code=422,
        code="INVALID_COURSE_INSTRUCTOR",
        message="Course instructor cannot be blank.",
    ),
    "ck_courses_section_not_blank": ConstraintResponse(
        status_code=422,
        code="INVALID_COURSE_SECTION",
        message="Course section cannot be blank.",
    ),
}


SQLITE_CONSTRAINT_SIGNATURES = {
    "unique constraint failed: courses.course_id": "uq_courses_course_id",
    (
        "unique constraint failed: courses.code, courses.semester, "
        "courses.section"
    ): "uq_courses_code_semester_section",
    "not null constraint failed: courses.section": "ck_courses_section_not_blank",
}


def get_constraint_name(error: IntegrityError) -> str | None:
    original_error = error.orig
    diagnostics = getattr(original_error, "diag", None)
    constraint_name = getattr(diagnostics, "constraint_name", None)

    if constraint_name:
        return constraint_name

    error_message = str(original_error).lower()

    for known_name in CONSTRAINT_RESPONSES:
        if known_name.lower() in error_message:
            return known_name

    for signature, known_name in SQLITE_CONSTRAINT_SIGNATURES.items():
        if signature in error_message:
            return known_name

    return None


async def database_integrity_error_handler(
    _request: Request,
    error: IntegrityError,
) -> JSONResponse:
    constraint_name = get_constraint_name(error)
    response = CONSTRAINT_RESPONSES.get(
        constraint_name,
        ConstraintResponse(
            status_code=status.HTTP_409_CONFLICT,
            code="DATABASE_CONSTRAINT_VIOLATION",
            message=(
                "The request conflicts with an existing or related "
                "database record."
            ),
        ),
    )

    return JSONResponse(
        status_code=response.status_code,
        content=error_response_content(
            code=response.code,
            message=response.message,
        ),
    )
