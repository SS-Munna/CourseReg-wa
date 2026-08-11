from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import SuccessResponse


ActiveRegistrationStatus = Literal["draft", "pending", "approved"]


class ScheduleConflictCourse(BaseModel):
    course_id: str = Field(..., min_length=1)
    code: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    section: str = Field(..., min_length=1)
    registration_status: ActiveRegistrationStatus
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    end_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")


class ScheduleConflict(BaseModel):
    selected_course: ScheduleConflictCourse
    conflicting_course: ScheduleConflictCourse
    day: str = Field(..., min_length=1)
    overlap_start_time: str = Field(
        ...,
        pattern=r"^\d{2}:\d{2}$",
    )
    overlap_end_time: str = Field(
        ...,
        pattern=r"^\d{2}:\d{2}$",
    )
    message: str = Field(..., min_length=1)


class ScheduleConflictValidation(BaseModel):
    has_conflicts: bool
    conflict_count: int = Field(..., ge=0)
    conflicts: list[ScheduleConflict]
    message: str = Field(..., min_length=1)


class ScheduleConflictValidationResponse(
    SuccessResponse[ScheduleConflictValidation]
):
    pass
