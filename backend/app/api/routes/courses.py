from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.api.errors import (
    REQUEST_VALIDATION_ERROR_RESPONSE,
    STANDARD_ERROR_RESPONSE,
)
from app.database import get_db
from app.repositories.course_repository import (
    CourseRepositoryError,
    get_section_availability,
    list_courses,
)
from app.schemas.course import (
    CourseListResponse,
    SectionAvailabilityResponse,
)

router = APIRouter(prefix="/api/courses", tags=["Courses"])


@router.get(
    "",
    response_model=CourseListResponse,
    responses={
        status.HTTP_422_UNPROCESSABLE_CONTENT: (
            REQUEST_VALIDATION_ERROR_RESPONSE
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: STANDARD_ERROR_RESPONSE,
    },
)
def get_courses(
    search: Optional[str] = Query(
        default=None,
        description="Search by course code or title",
    ),
    department: Optional[str] = Query(
        default=None,
        description="Filter by department",
    ),
    semester: Optional[str] = Query(
        default=None,
        description="Filter by semester",
    ),
    is_mandatory: Optional[bool] = Query(
        default=None,
        description="Filter mandatory courses",
    ),
    available_only: bool = Query(
        default=False,
        description="Show only courses with available seats",
    ),
    db: Session = Depends(get_db),
):
    try:
        courses = list_courses(
            db=db,
            search=search,
            department=department,
            semester=semester,
            is_mandatory=is_mandatory,
            available_only=available_only,
        )
        return CourseListResponse(data=courses)

    except CourseRepositoryError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "DATABASE_OPERATION_FAILED",
                "message": (
                    "Unable to retrieve course records from the "
                    "database."
                ),
            },
        ) from error


@router.get(
    "/{course_id}/availability",
    response_model=SectionAvailabilityResponse,
    responses={
        status.HTTP_404_NOT_FOUND: STANDARD_ERROR_RESPONSE,
        status.HTTP_422_UNPROCESSABLE_CONTENT: (
            REQUEST_VALIDATION_ERROR_RESPONSE
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: STANDARD_ERROR_RESPONSE,
    },
)
def get_course_section_availability(
    course_id: str = Path(
        ...,
        min_length=1,
        max_length=255,
        pattern=r".*\S.*",
        description="Public identifier of the course-section offering",
    ),
    db: Session = Depends(get_db),
):
    try:
        section = get_section_availability(
            db=db,
            course_id=course_id,
        )

        if section is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "SECTION_NOT_FOUND",
                    "message": "The requested course section was not found.",
                },
            )

        return SectionAvailabilityResponse(data=section)

    except CourseRepositoryError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "DATABASE_OPERATION_FAILED",
                "message": (
                    "Unable to retrieve section availability from the "
                    "database."
                ),
            },
        ) from error
