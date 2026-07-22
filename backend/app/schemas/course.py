from typing import List, Optional

from pydantic import BaseModel, Field


class SectionSchedule(BaseModel):
    day: str = Field(..., description="Class meeting day")
    start_time: str = Field(..., description="Class start time in HH:MM format")
    end_time: str = Field(..., description="Class end time in HH:MM format")
    room: Optional[str] = Field(default=None, description="Classroom or lab room")


class CourseBase(BaseModel):
    course_id: str = Field(..., description="Unique DynamoDB course identifier")
    code: str = Field(..., description="Course code, such as CSE 101")
    title: str = Field(..., description="Course title")
    department: str = Field(..., description="Department offering the course")
    semester: str = Field(..., description="Academic semester")
    instructor: str = Field(..., description="Course instructor")
    credits: int = Field(..., ge=1, description="Course credit value")
    capacity: int = Field(..., ge=1, description="Maximum seat capacity")
    available_seats: int = Field(..., ge=0, description="Currently available seats")
    is_mandatory: bool = Field(..., description="Whether the course is mandatory")
    level: Optional[str] = Field(default="Undergraduate", description="Course level")
    description: Optional[str] = Field(default=None, description="Course description")
    prerequisites: List[str] = Field(
        default_factory=list,
        description="List of prerequisite course codes",
    )
    section: Optional[str] = Field(default=None, description="Course section label")
    schedule: List[SectionSchedule] = Field(
        default_factory=list,
        description="Course meeting schedule",
    )


class CourseCreate(CourseBase):
    pass


class CourseResponse(CourseBase):
    pass


class CourseUpdate(BaseModel):
    title: Optional[str] = None
    department: Optional[str] = None
    semester: Optional[str] = None
    instructor: Optional[str] = None
    credits: Optional[int] = Field(default=None, ge=1)
    capacity: Optional[int] = Field(default=None, ge=1)
    available_seats: Optional[int] = Field(default=None, ge=0)
    is_mandatory: Optional[bool] = None
    level: Optional[str] = None
    description: Optional[str] = None
    prerequisites: Optional[List[str]] = None
    section: Optional[str] = None
    schedule: Optional[List[SectionSchedule]] = None


class CourseListResponse(BaseModel):
    success: bool = True
    data: List[CourseResponse]