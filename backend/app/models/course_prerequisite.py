from uuid import uuid4

from sqlalchemy import (
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.completed_course import GRADE_SQL_VALUES


class CoursePrerequisite(Base):
    __tablename__ = "course_prerequisites"
    __table_args__ = (
        UniqueConstraint(
            "course_id",
            "prerequisite_course_id",
            name="uq_course_prerequisite_course_required",
        ),
        CheckConstraint(
            "course_id <> prerequisite_course_id",
            name="ck_course_prerequisite_not_self",
        ),
        CheckConstraint(
            "minimum_grade IS NULL OR "
            f"minimum_grade IN ({GRADE_SQL_VALUES})",
            name="ck_course_prerequisite_minimum_grade",
        ),
        Index(
            "ix_course_prerequisite_required_course",
            "prerequisite_course_id",
        ),
    )

    id = Column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    course_id = Column(
        Integer,
        ForeignKey("courses.id"),
        nullable=False,
    )
    prerequisite_course_id = Column(
        Integer,
        ForeignKey("courses.id"),
        nullable=False,
    )
    minimum_grade = Column(String(8), nullable=True)

    course = relationship(
        "Course",
        foreign_keys=[course_id],
        back_populates="prerequisite_rules",
    )
    prerequisite_course = relationship(
        "Course",
        foreign_keys=[prerequisite_course_id],
        back_populates="required_for_rules",
    )
