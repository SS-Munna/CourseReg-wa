from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.course import Course
from app.schemas.course import CourseResponse


class CourseRepositoryError(RuntimeError):
    """Raised when course data cannot be retrieved from the database."""


def course_to_response(course: Course) -> CourseResponse:
    return CourseResponse(
        course_id=course.course_id,
        code=course.code,
        title=course.title,
        department=course.department,
        semester=course.semester,
        instructor=course.instructor,
        credits=course.credits,
        capacity=course.capacity,
        available_seats=course.available_seats,
        is_mandatory=course.is_mandatory,
        level=course.level,
        description=course.description,
        prerequisites=course.prerequisites or [],
        section=course.section,
        schedule=course.schedule or [],
    )


def list_courses(
    db: Session,
    search: Optional[str] = None,
    department: Optional[str] = None,
    semester: Optional[str] = None,
    is_mandatory: Optional[bool] = None,
    available_only: bool = False,
) -> list[CourseResponse]:
    try:
        query = db.query(Course)

        if search:
            search_text = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Course.code.ilike(search_text),
                    Course.title.ilike(search_text),
                )
            )

        if department:
            query = query.filter(Course.department == department)

        if semester:
            query = query.filter(Course.semester == semester)

        if is_mandatory is not None:
            query = query.filter(Course.is_mandatory == is_mandatory)

        if available_only:
            query = query.filter(Course.available_seats > 0)

        courses = query.order_by(Course.code).all()

        return [course_to_response(course) for course in courses]

    except Exception as error:
        raise CourseRepositoryError(str(error)) from error