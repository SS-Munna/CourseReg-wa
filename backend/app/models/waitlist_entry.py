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
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class WaitlistStatus(str, Enum):
    ACTIVE = "active"
    PROMOTED = "promoted"
    REMOVED = "removed"
    EXPIRED = "expired"


class WaitlistEntry(Base):
    __tablename__ = "waitlist_entries"
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "section_id",
            name="uq_waitlist_student_section",
        ),
        CheckConstraint(
            "waitlist_status IN "
            "('active', 'promoted', 'removed', 'expired')",
            name="ck_waitlist_status",
        ),
        Index(
            "ix_waitlist_section_queue",
            "section_id",
            "waitlist_status",
            "joined_at",
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
    waitlist_status = Column(
        String(32),
        default=WaitlistStatus.ACTIVE.value,
        nullable=False,
    )
    joined_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    promoted_at = Column(DateTime(timezone=True), nullable=True)
    removed_at = Column(DateTime(timezone=True), nullable=True)

    student = relationship("Student", back_populates="waitlist_entries")
    section = relationship("Course", back_populates="waitlist_entries")
