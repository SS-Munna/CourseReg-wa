from uuid import uuid4

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Uuid,
)
from sqlalchemy.orm import relationship

from app.database import Base


class RegistrationPeriod(Base):
    __tablename__ = "registration_periods"
    __table_args__ = (
        CheckConstraint(
            "closing_time >= opening_time",
            name="ck_registration_period_time_range",
        ),
        CheckConstraint(
            "minimum_credit >= 0",
            name="ck_registration_period_minimum_credit_nonnegative",
        ),
        CheckConstraint(
            "maximum_credit >= minimum_credit",
            name="ck_registration_period_credit_range",
        ),
        CheckConstraint(
            "TRIM(status) <> ''",
            name="ck_registration_period_status_not_blank",
        ),
        Index(
            "ix_registration_period_semester_opening",
            "semester_id",
            "opening_time",
        ),
        Index(
            "ix_registration_period_semester_drop_deadline",
            "semester_id",
            "drop_deadline",
        ),
    )

    id = Column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    semester_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("semesters.id"),
        nullable=False,
    )
    opening_time = Column(DateTime(timezone=True), nullable=False)
    closing_time = Column(DateTime(timezone=True), nullable=False)
    drop_deadline = Column(Date, nullable=False)
    minimum_credit = Column(Integer, nullable=False)
    maximum_credit = Column(Integer, nullable=False)
    status = Column(String(50), default="scheduled", nullable=False)

    semester = relationship(
        "Semester",
        back_populates="registration_periods",
    )
