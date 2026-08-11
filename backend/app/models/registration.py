from enum import Enum
from uuid import uuid4

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class RegistrationStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DROPPED = "dropped"


class Registration(Base):
    __tablename__ = "registrations"
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "section_id",
            name="uq_registration_student_section",
        ),
        CheckConstraint(
            "registration_status IN "
            "('draft', 'pending', 'approved', 'rejected', 'dropped')",
            name="ck_registration_status",
        ),
        Index(
            "ix_registration_student_status",
            "student_id",
            "registration_status",
        ),
        Index(
            "ix_registration_section_status",
            "section_id",
            "registration_status",
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
    section_id = Column(
        Integer,
        ForeignKey("courses.id"),
        nullable=False,
    )
    reviewed_by = Column(
        Uuid(as_uuid=True),
        ForeignKey("advisors.id"),
        nullable=True,
        index=True,
    )
    registration_status = Column(
        String(32),
        default=RegistrationStatus.DRAFT.value,
        nullable=False,
    )
    advisor_comment = Column(Text, nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    student = relationship("Student", back_populates="registrations")
    section = relationship("Course", back_populates="registrations")
    reviewer = relationship(
        "Advisor",
        back_populates="reviewed_registrations",
    )
