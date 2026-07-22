from fastapi import APIRouter, HTTPException

from app.repositories.course_repository import CourseRepositoryError, list_courses
from app.schemas.course import CourseListResponse

router = APIRouter(prefix="/api/courses", tags=["Courses"])


@router.get("", response_model=CourseListResponse)
def get_courses():
    try:
        courses = list_courses()
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

    