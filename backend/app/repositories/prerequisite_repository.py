from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.completed_course import (
    CompletionStatus,
    CompletedCourse,
)
from app.models.course import Course
from app.models.course_prerequisite import CoursePrerequisite
from app.schemas.prerequisite import (
    PrerequisiteRequirement,
    PrerequisiteValidation,
)


GRADE_RANK = {
    grade: rank
    for rank, grade in enumerate(
        (
            "F",
            "D",
            "D+",
            "C-",
            "C",
            "C+",
            "B-",
            "B",
            "B+",
            "A-",
            "A",
            "A+",
        )
    )
}


class PrerequisiteRepositoryError(RuntimeError):
    """Raised when prerequisite data cannot be read safely."""


class PrerequisitesNotMetError(ValueError):
    def __init__(self, validation: PrerequisiteValidation):
        super().__init__("The student has unmet course prerequisites.")
        self.validation = validation


@dataclass(frozen=True)
class RequirementSource:
    course_id: str | None
    code: str
    title: str | None
    minimum_grade: str | None


def normalize_course_code(code: str) -> str:
    return " ".join(code.strip().upper().split())


def normalize_grade(grade: str) -> str:
    return grade.strip().upper()


def grade_meets_minimum(
    *,
    earned_grade: str,
    minimum_grade: str,
) -> bool:
    earned_rank = GRADE_RANK.get(normalize_grade(earned_grade))
    minimum_rank = GRADE_RANK.get(normalize_grade(minimum_grade))

    if earned_rank is None or minimum_rank is None:
        return False

    return earned_rank >= minimum_rank


def completed_course_query(
    db: Session,
    *,
    student_id: UUID,
    course_codes: list[str],
):
    normalized_codes = [
        normalize_course_code(code) for code in course_codes
    ]

    return (
        db.query(CompletedCourse, Course)
        .join(Course, CompletedCourse.course_id == Course.id)
        .filter(
            CompletedCourse.student_id == student_id,
            func.upper(func.trim(Course.code)).in_(normalized_codes),
        )
    )


def _legacy_requirement_sources(
    db: Session,
    *,
    course: Course,
    normalized_rule_codes: set[str],
) -> list[RequirementSource]:
    legacy_codes = []

    for value in course.prerequisites or []:
        if not isinstance(value, str) or not value.strip():
            continue

        normalized_code = normalize_course_code(value)

        if normalized_code not in normalized_rule_codes:
            legacy_codes.append(normalized_code)

    if not legacy_codes:
        return []

    legacy_courses = (
        db.query(Course)
        .filter(func.upper(func.trim(Course.code)).in_(legacy_codes))
        .order_by(Course.code, Course.id)
        .all()
    )
    courses_by_code = {}

    for legacy_course in legacy_courses:
        courses_by_code.setdefault(
            normalize_course_code(legacy_course.code),
            legacy_course,
        )

    return [
        RequirementSource(
            course_id=(
                courses_by_code[code].course_id
                if code in courses_by_code
                else None
            ),
            code=code,
            title=(
                courses_by_code[code].title
                if code in courses_by_code
                else None
            ),
            minimum_grade=None,
        )
        for code in dict.fromkeys(legacy_codes)
    ]


def _requirement_sources(
    db: Session,
    *,
    course: Course,
) -> list[RequirementSource]:
    rules = (
        db.query(CoursePrerequisite)
        .options(joinedload(CoursePrerequisite.prerequisite_course))
        .filter(CoursePrerequisite.course_id == course.id)
        .order_by(CoursePrerequisite.id)
        .all()
    )
    sources = [
        RequirementSource(
            course_id=rule.prerequisite_course.course_id,
            code=normalize_course_code(rule.prerequisite_course.code),
            title=rule.prerequisite_course.title,
            minimum_grade=rule.minimum_grade,
        )
        for rule in rules
    ]
    normalized_rule_codes = {source.code for source in sources}

    sources.extend(
        _legacy_requirement_sources(
            db,
            course=course,
            normalized_rule_codes=normalized_rule_codes,
        )
    )

    return sources


def _best_grade(grades: list[str]) -> str | None:
    if not grades:
        return None

    return max(
        (normalize_grade(grade) for grade in grades),
        key=lambda grade: GRADE_RANK.get(grade, -1),
    )


def get_prerequisite_validation(
    db: Session,
    *,
    student_id: UUID,
    course_id: str,
) -> PrerequisiteValidation | None:
    try:
        course = (
            db.query(Course)
            .filter(Course.course_id == course_id)
            .one_or_none()
        )

        if course is None:
            return None

        sources = _requirement_sources(db, course=course)
        completed_by_code: dict[str, list[str]] = {}

        if sources:
            completed_rows = completed_course_query(
                db,
                student_id=student_id,
                course_codes=[source.code for source in sources],
            ).all()

            for record, completed_course in completed_rows:
                if (
                    record.completion_status
                    != CompletionStatus.COMPLETED.value
                    or normalize_grade(record.grade) == "F"
                ):
                    continue

                normalized_code = normalize_course_code(
                    completed_course.code
                )
                completed_by_code.setdefault(normalized_code, []).append(
                    record.grade
                )

        requirements = []

        for source in sources:
            earned_grade = _best_grade(
                completed_by_code.get(source.code, [])
            )
            has_completed = earned_grade is not None
            satisfies_grade = (
                has_completed
                and (
                    source.minimum_grade is None
                    or grade_meets_minimum(
                        earned_grade=earned_grade,
                        minimum_grade=source.minimum_grade,
                    )
                )
            )
            reason = None

            if not has_completed:
                reason = "not_completed"
            elif not satisfies_grade:
                reason = "minimum_grade_not_met"

            requirements.append(
                PrerequisiteRequirement(
                    course_id=source.course_id,
                    code=source.code,
                    title=source.title,
                    minimum_grade=source.minimum_grade,
                    earned_grade=earned_grade,
                    satisfied=satisfies_grade,
                    reason=reason,
                )
            )

        missing_prerequisites = [
            requirement
            for requirement in requirements
            if not requirement.satisfied
        ]

        return PrerequisiteValidation(
            course_id=course.course_id,
            code=course.code,
            eligible=not missing_prerequisites,
            requirements=requirements,
            missing_prerequisites=missing_prerequisites,
        )

    except Exception as error:
        raise PrerequisiteRepositoryError(str(error)) from error


def require_prerequisites_met(
    db: Session,
    *,
    student_id: UUID,
    course_id: str,
) -> PrerequisiteValidation | None:
    validation = get_prerequisite_validation(
        db,
        student_id=student_id,
        course_id=course_id,
    )

    if validation is not None and not validation.eligible:
        raise PrerequisitesNotMetError(validation)

    return validation
