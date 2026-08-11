from typing import List, Optional

from pydantic import BaseModel, Field, model_validator


class SectionSchedule(BaseModel):
    day: str = Field(..., description="Class meeting day")
    start_time: str = Field(..., description="Class start time in HH:MM format")
    end_time: str = Field(..., description="Class end time in HH:MM format")
    room: Optional[str] = Field(default=None, description="Classroom or lab room")


class CourseBase(BaseModel):
    course_id: str = Field(
        ...,
        min_length=1,
        description="Unique course identifier",
    )
    code: str = Field(
        ...,
        min_length=1,
        description="Course code, such as CSE 101",
    )
    title: str = Field(..., min_length=1, description="Course title")
    department: str = Field(
        ...,
        min_length=1,
        description="Department offering the course",
    )
    semester: str = Field(
        ...,
        min_length=1,
        description="Academic semester",
    )
    instructor: str = Field(
        ...,
        min_length=1,
        description="Course instructor",
    )
    credits: int = Field(..., ge=1, description="Course credit value")
    capacity: int = Field(..., ge=1, description="Maximum seat capacity")
    available_seats: int = Field(..., ge=0, description="Currently available seats")
    is_mandatory: bool = Field(..., description="Whether the course is mandatory")
    level: Optional[str] = Field(default="Undergraduate", description="Course level")
    description: Optional[str] = Field(default=None, description="Course description")
    prerequisites: List[str] = Field(default_factory=list)
    section: str = Field(
        ...,
        min_length=1,
        description="Course section label",
    )
    schedule: List[SectionSchedule] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_available_seats(self):
        if self.available_seats > self.capacity:
            raise ValueError(
                "available_seats cannot be greater than capacity"
            )

        return self


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

    @model_validator(mode="after")
    def validate_available_seats(self):
        if (
            self.capacity is not None
            and self.available_seats is not None
            and self.available_seats > self.capacity
        ):
            raise ValueError(
                "available_seats cannot be greater than capacity"
            )

        return self


class CourseListResponse(BaseModel):
    success: bool = True
    data: List[CourseResponse]
