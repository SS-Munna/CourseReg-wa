from uuid import uuid4

from sqlalchemy import Column, DateTime, String, Uuid, func
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    email = Column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="student", nullable=False)
    account_status = Column(
        String(50),
        default="active",
        nullable=False,
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    student = relationship(
        "Student",
        back_populates="user",
        uselist=False,
    )
    advisor = relationship(
        "Advisor",
        back_populates="user",
        uselist=False,
    )
    instructor = relationship(
        "Instructor",
        back_populates="user",
        uselist=False,
    )
    notifications = relationship(
        "Notification",
        back_populates="user",
    )
    audit_logs = relationship(
        "AuditLog",
        back_populates="user",
    )
