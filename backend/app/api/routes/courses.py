from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.repositories.course_repository import CourseRepositoryError, list_courses
from app.schemas.course import CourseListResponse

router = APIRouter(prefix="/api/courses", tags=["Courses"])


@router.get("", response_model=CourseListResponse)
def get_courses(
    search: Optional[str] = Query(default=None, description="Search by course code or title"),
    department: Optional[str] = Query(default=None, description="Filter by department"),
    semester: Optional[str] = Query(default=None, description="Filter by semester"),
    is_mandatory: Optional[bool] = Query(default=None, description="Filter mandatory courses"),
    available_only: bool = Query(default=False, description="Show only courses with available seats"),
):
    try:
        courses = list_courses(
            search=search,
            department=department,
            semester=semester,
            is_mandatory=is_mandatory,
            available_only=available_only,
        )
        return CourseListResponse(data=courses)

    except CourseRepositoryError as error:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "DYNAMODB_OPERATION_FAILED",
                "message": "Unable to retrieve course records from DynamoDB.",
                "details": str(error),
            },
        ) from error