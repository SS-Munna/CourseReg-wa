from uuid import uuid4

from sqlalchemy import Column, DateTime, String, Uuid, func
from sqlalchemy.orm import relationship

from app.database import Base


class Department(Base):
    __tablename__ = "departments"

    id = Column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    department_code = Column(
        String(32),
        unique=True,
        index=True,
        nullable=False,
    )
    department_name = Column(String(255), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    programs = relationship("Program", back_populates="department")
    advisors = relationship("Advisor", back_populates="department")
    instructors = relationship(
        "Instructor",
        back_populates="department",
    )
