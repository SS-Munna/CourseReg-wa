from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import SuccessResponse


PrerequisiteFailureReason = Literal[
    "not_completed",
    "minimum_grade_not_met",
]


class PrerequisiteRequirement(BaseModel):
    course_id: str | None = Field(
        default=None,
        description="Public ID of the prerequisite course offering",
    )
    code: str = Field(..., min_length=1)
    title: str | None = None
    minimum_grade: str | None = None
    earned_grade: str | None = None
    satisfied: bool
    reason: PrerequisiteFailureReason | None = None


class PrerequisiteValidation(BaseModel):
    course_id: str = Field(..., min_length=1)
    code: str = Field(..., min_length=1)
    eligible: bool
    requirements: list[PrerequisiteRequirement]
    missing_prerequisites: list[PrerequisiteRequirement]


class PrerequisiteValidationResponse(
    SuccessResponse[PrerequisiteValidation]
):
    pass
