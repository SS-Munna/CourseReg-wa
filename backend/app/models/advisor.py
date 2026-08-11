from uuid import uuid4

from sqlalchemy import Column, ForeignKey, String, Uuid
from sqlalchemy.orm import relationship

from app.database import Base


class Advisor(Base):
    __tablename__ = "advisors"

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
    department_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("departments.id"),
        nullable=False,
        index=True,
    )
    employee_number = Column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
    )

    user = relationship("User", back_populates="advisor")
    department = relationship("Department", back_populates="advisors")
    students = relationship("Student", back_populates="advisor")
    reviewed_registrations = relationship(
        "Registration",
        back_populates="reviewer",
    )
