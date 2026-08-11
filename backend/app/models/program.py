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


class Program(Base):
    __tablename__ = "programs"
    __table_args__ = (
        CheckConstraint(
            "minimum_credit >= 0",
            name="ck_program_minimum_credit_nonnegative",
        ),
        CheckConstraint(
            "maximum_credit >= minimum_credit",
            name="ck_program_credit_range",
        ),
    )

    id = Column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    department_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("departments.id"),
        nullable=False,
        index=True,
    )
    program_code = Column(
        String(32),
        unique=True,
        index=True,
        nullable=False,
    )
    program_name = Column(String(255), nullable=False)
    minimum_credit = Column(Integer, nullable=False)
    maximum_credit = Column(Integer, nullable=False)

    department = relationship("Department", back_populates="programs")
    students = relationship("Student", back_populates="program")
