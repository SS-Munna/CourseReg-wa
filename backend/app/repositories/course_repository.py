from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.registration import Registration, RegistrationStatus
from app.schemas.course import (
    CourseResponse,
    SectionAvailability,
)


class CourseRepositoryError(RuntimeError):
    """Raised when course data cannot be retrieved from the database."""


def approved_enrollment_expression():
    return (
        select(func.count(Registration.id))
        .where(
            Registration.section_id == Course.id,
            Registration.registration_status
            == RegistrationStatus.APPROVED.value,
        )
        .correlate(Course)
        .scalar_subquery()
    )


def available_seat_count(*, capacity: int, enrollment: int) -> int:
    return max(capacity - enrollment, 0)


def course_to_response(
    course: Course,
    *,
    enrollment: int,
) -> CourseResponse:
    return CourseResponse(
        course_id=course.course_id,
        code=course.code,
        title=course.title,
        department=course.department,
        semester=course.semester,
        instructor=course.instructor,
        credits=course.credits,
        capacity=course.capacity,
        available_seats=available_seat_count(
            capacity=course.capacity,
            enrollment=enrollment,
        ),
        is_mandatory=course.is_mandatory,
        level=course.level,
        description=course.description,
        prerequisites=course.prerequisites or [],
        section=course.section,
        schedule=course.schedule or [],
    )


def section_availability_to_response(
    course: Course,
    *,
    enrollment: int,
) -> SectionAvailability:
    course_data = course_to_response(
        course,
        enrollment=enrollment,
    )

    return SectionAvailability(
        **course_data.model_dump(),
        enrollment=enrollment,
        is_full=course_data.available_seats == 0,
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
        enrollment = approved_enrollment_expression()
        query = db.query(
            Course,
            enrollment.label("approved_enrollment"),
        )

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
            query = query.filter(Course.capacity > enrollment)

        courses = query.order_by(Course.code, Course.section).all()

        return [
            course_to_response(
                course,
                enrollment=int(approved_enrollment),
            )
            for course, approved_enrollment in courses
        ]

    except Exception as error:
        raise CourseRepositoryError(str(error)) from error


def get_section_availability(
    db: Session,
    course_id: str,
) -> SectionAvailability | None:
    try:
        enrollment = approved_enrollment_expression()
        result = (
            db.query(
                Course,
                enrollment.label("approved_enrollment"),
            )
            .filter(Course.course_id == course_id)
            .one_or_none()
        )

        if result is None:
            return None

        course, approved_enrollment = result

        return section_availability_to_response(
            course,
            enrollment=int(approved_enrollment),
        )

    except Exception as error:
        raise CourseRepositoryError(str(error)) from error
