from sqlalchemy import Boolean, Column, Integer, JSON, String, Text

from app.database import Base


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(String, unique=True, index=True, nullable=False)
    code = Column(String, index=True, nullable=False)
    title = Column(String, index=True, nullable=False)
    department = Column(String, index=True, nullable=False)
    semester = Column(String, index=True, nullable=False)
    instructor = Column(String, nullable=False)
    credits = Column(Integer, nullable=False)
    capacity = Column(Integer, nullable=False)
    available_seats = Column(Integer, nullable=False)
    is_mandatory = Column(Boolean, default=False, nullable=False)
    level = Column(String, default="Undergraduate")
    description = Column(Text, nullable=True)
    prerequisites = Column(JSON, default=list)
    section = Column(String, nullable=True)
    schedule = Column(JSON, default=list)