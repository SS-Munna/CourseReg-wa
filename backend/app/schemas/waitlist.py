from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import SuccessResponse
from app.schemas.course import CourseResponse


class WaitlistJoinRequest(BaseModel):
    course_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        pattern=r".*\S.*",
        description="Public identifier of the full course-section offering",
    )

    @field_validator("course_id")
    @classmethod
    def strip_course_id(cls, value: str) -> str:
        return value.strip()


class WaitlistEntryDetails(BaseModel):
    waitlist_entry_id: UUID
    waitlist_status: Literal["active"]
    joined_at: datetime
    queue_position: int = Field(..., ge=1)
    total_waiting: int = Field(..., ge=1)
    course: CourseResponse


class WaitlistLeaveResult(BaseModel):
    waitlist_entry_id: UUID
    course_id: str = Field(..., min_length=1)
    waitlist_status: Literal["removed"]
    removed_at: datetime
    previous_queue_position: int = Field(..., ge=1)
    remaining_waiting: int = Field(..., ge=0)


class WaitlistEntryResponse(SuccessResponse[WaitlistEntryDetails]):
    pass


class WaitlistListResponse(
    SuccessResponse[list[WaitlistEntryDetails]]
):
    pass


class WaitlistLeaveResponse(SuccessResponse[WaitlistLeaveResult]):
    pass
