from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Course(Base):
    __tablename__ = "courses"
    __table_args__ = (
        UniqueConstraint(
            "course_id",
            name="uq_courses_course_id",
        ),
        UniqueConstraint(
            "code",
            "semester",
            "section",
            name="uq_courses_code_semester_section",
        ),
        CheckConstraint(
            "TRIM(course_id) <> ''",
            name="ck_courses_course_id_not_blank",
        ),
        CheckConstraint(
            "TRIM(code) <> ''",
            name="ck_courses_code_not_blank",
        ),
        CheckConstraint(
            "TRIM(title) <> ''",
            name="ck_courses_title_not_blank",
        ),
        CheckConstraint(
            "TRIM(department) <> ''",
            name="ck_courses_department_not_blank",
        ),
        CheckConstraint(
            "TRIM(semester) <> ''",
            name="ck_courses_semester_not_blank",
        ),
        CheckConstraint(
            "TRIM(instructor) <> ''",
            name="ck_courses_instructor_not_blank",
        ),
        CheckConstraint(
            "TRIM(section) <> ''",
            name="ck_courses_section_not_blank",
        ),
        CheckConstraint(
            "credits > 0",
            name="ck_courses_credits_positive",
        ),
        CheckConstraint(
            "capacity > 0",
            name="ck_courses_capacity_positive",
        ),
        CheckConstraint(
            "available_seats >= 0",
            name="ck_courses_available_seats_nonnegative",
        ),
        CheckConstraint(
            "available_seats <= capacity",
            name="ck_courses_available_seats_within_capacity",
        ),
        Index("ix_courses_code", "code"),
        Index("ix_courses_title", "title"),
        Index("ix_courses_department", "department"),
        Index("ix_courses_semester", "semester"),
    )

    id = Column(Integer, primary_key=True)
    course_id = Column(String, nullable=False)
    code = Column(String, nullable=False)
    title = Column(String, nullable=False)
    department = Column(String, nullable=False)
    semester = Column(String, nullable=False)
    instructor = Column(String, nullable=False)
    credits = Column(Integer, nullable=False)
    capacity = Column(Integer, nullable=False)
    available_seats = Column(Integer, nullable=False)
    is_mandatory = Column(Boolean, default=False, nullable=False)
    level = Column(String, default="Undergraduate")
    description = Column(Text, nullable=True)
    prerequisites = Column(JSON, default=list)
    section = Column(String, nullable=False)
    schedule = Column(JSON, default=list)

    registrations = relationship(
        "Registration",
        back_populates="section",
    )
    waitlist_entries = relationship(
        "WaitlistEntry",
        back_populates="section",
    )
