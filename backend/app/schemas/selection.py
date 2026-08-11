from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import SuccessResponse
from app.schemas.course import CourseResponse


class DraftSelectionCreate(BaseModel):
    course_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        pattern=r".*\S.*",
        description="Public identifier of the course-section offering",
    )

    @field_validator("course_id")
    @classmethod
    def strip_course_id(cls, value: str) -> str:
        return value.strip()


class DraftSelection(BaseModel):
    registration_id: UUID
    registration_status: Literal["draft"]
    course: CourseResponse


class DraftSelectionRemoved(BaseModel):
    registration_id: UUID
    course_id: str = Field(..., min_length=1)


class DraftSelectionResponse(SuccessResponse[DraftSelection]):
    pass


class DraftSelectionListResponse(
    SuccessResponse[list[DraftSelection]]
):
    pass


class DraftSelectionRemovedResponse(
    SuccessResponse[DraftSelectionRemoved]
):
    pass
