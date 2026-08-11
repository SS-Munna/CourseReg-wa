from uuid import uuid4

from sqlalchemy import (
    CheckConstraint,
    Column,
    ForeignKey,
    Integer,
    String,
    Uuid,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Student(Base):
    __tablename__ = "students"
    __table_args__ = (
        CheckConstraint(
            "current_trimester > 0",
            name="ck_student_current_trimester_positive",
        ),
    )

    id = Column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    user_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
        index=True,
    )
    program_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("programs.id"),
        nullable=False,
        index=True,
    )
    advisor_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("advisors.id"),
        nullable=False,
        index=True,
    )
    student_number = Column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
    )
    current_trimester = Column(Integer, nullable=False)
    academic_status = Column(
        String(50),
        default="active",
        nullable=False,
    )

    user = relationship("User", back_populates="student")
    program = relationship("Program", back_populates="students")
    advisor = relationship("Advisor", back_populates="students")
    registrations = relationship(
        "Registration",
        back_populates="student",
    )
    waitlist_entries = relationship(
        "WaitlistEntry",
        back_populates="student",
    )
    completed_courses = relationship(
        "CompletedCourse",
        back_populates="student",
    )
