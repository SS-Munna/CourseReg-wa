from enum import Enum
from uuid import uuid4

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import relationship

from app.database import Base


SUPPORTED_GRADES = (
    "A+",
    "A",
    "A-",
    "B+",
    "B",
    "B-",
    "C+",
    "C",
    "C-",
    "D+",
    "D",
    "F",
)

GRADE_SQL_VALUES = ", ".join(
    f"'{grade}'" for grade in SUPPORTED_GRADES
)


class CompletionStatus(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"
    WITHDRAWN = "withdrawn"


class CompletedCourse(Base):
    __tablename__ = "completed_courses"
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "course_id",
            name="uq_completed_course_student_course",
        ),
        CheckConstraint(
            f"grade IN ({GRADE_SQL_VALUES})",
            name="ck_completed_course_grade",
        ),
        CheckConstraint(
            "completion_status IN "
            "('completed', 'failed', 'in_progress', 'withdrawn')",
            name="ck_completed_course_status",
        ),
        CheckConstraint(
            "completion_status <> 'completed' OR completed_at IS NOT NULL",
            name="ck_completed_course_completion_date",
        ),
        Index(
            "ix_completed_course_student_status",
            "student_id",
            "completion_status",
        ),
        Index(
            "ix_completed_course_course",
            "course_id",
        ),
    )

    id = Column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    student_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("students.id"),
        nullable=False,
    )
    course_id = Column(
        Integer,
        ForeignKey("courses.id"),
        nullable=False,
    )
    grade = Column(String(8), nullable=False)
    completion_status = Column(
        String(32),
        default=CompletionStatus.COMPLETED.value,
        nullable=False,
    )
    completed_at = Column(Date, nullable=True)

    student = relationship(
        "Student",
        back_populates="completed_courses",
    )
    course = relationship(
        "Course",
        back_populates="completed_course_records",
    )
