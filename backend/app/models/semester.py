from uuid import uuid4

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    Integer,
    String,
    Uuid,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Semester(Base):
    __tablename__ = "semesters"
    __table_args__ = (
        CheckConstraint(
            "academic_year > 0",
            name="ck_semester_academic_year_positive",
        ),
        CheckConstraint(
            "end_date >= start_date",
            name="ck_semester_date_range",
        ),
    )

    id = Column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    semester_name = Column(String(100), nullable=False)
    academic_year = Column(Integer, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(
        String(50),
        default="upcoming",
        nullable=False,
    )

    registration_periods = relationship(
        "RegistrationPeriod",
        back_populates="semester",
    )
