from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.common import PaginatedResponse, SuccessResponse
from app.schemas.course import CourseResponse
from app.schemas.credit import CreditLoadValidation
from app.schemas.prerequisite import PrerequisiteValidation
from app.schemas.schedule_conflict import ScheduleConflictValidation
from app.schemas.waitlist import WaitlistEntryDetails


AdvisorRequestStatus = Literal["pending", "approved", "rejected"]
AdvisorDecision = Literal["approved", "rejected"]


class AdvisorReviewStudent(BaseModel):
    student_id: UUID
    student_number: str = Field(..., min_length=1)
    full_name: str = Field(..., min_length=1)
    email: str = Field(..., min_length=1)
    program_code: str = Field(..., min_length=1)
    program_name: str = Field(..., min_length=1)
    current_trimester: int = Field(..., ge=1)
    academic_status: str = Field(..., min_length=1)


class AdvisorReviewCourseSummary(BaseModel):
    registration_id: UUID
    course_id: str = Field(..., min_length=1)
    code: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    semester: str = Field(..., min_length=1)
    section: str = Field(..., min_length=1)
    credits: int = Field(..., ge=1)


class AdvisorRegistrationRequestSummary(BaseModel):
    request_id: UUID
    request_status: AdvisorRequestStatus
    submitted_at: datetime
    reviewed_at: datetime | None = None
    advisor_comment: str | None = None
    student: AdvisorReviewStudent
    course_count: int = Field(..., ge=1)
    total_credits: int = Field(..., ge=1)
    courses: list[AdvisorReviewCourseSummary]


class AdvisorReviewCourseDetails(BaseModel):
    registration_id: UUID
    registration_status: AdvisorRequestStatus
    course: CourseResponse
    prerequisite_validation: PrerequisiteValidation


class AdvisorRegistrationRequestDetails(BaseModel):
    request_id: UUID
    request_status: AdvisorRequestStatus
    submitted_at: datetime
    reviewed_at: datetime | None = None
    reviewed_by_advisor_id: UUID | None = None
    advisor_comment: str | None = None
    student: AdvisorReviewStudent
    course_count: int = Field(..., ge=1)
    total_credits: int = Field(..., ge=1)
    courses: list[AdvisorReviewCourseDetails]
    credit_validation: CreditLoadValidation
    schedule_validation: ScheduleConflictValidation
    waitlist_entries: list[WaitlistEntryDetails]


class AdvisorReviewDecisionRequest(BaseModel):
    decision: AdvisorDecision
    comment: str | None = Field(default=None, max_length=2000)

    @field_validator("comment")
    @classmethod
    def normalize_comment(cls, value: str | None) -> str | None:
        if value is None:
            return None

        normalized = value.strip()
        return normalized or None

    @model_validator(mode="after")
    def require_rejection_reason(self):
        if self.decision == "rejected" and self.comment is None:
            raise ValueError("A rejection reason is required.")

        return self


class AdvisorReviewDecisionResult(BaseModel):
    request_id: UUID
    request_status: AdvisorDecision
    registration_ids: list[UUID]
    reviewed_at: datetime
    reviewed_by_advisor_id: UUID
    advisor_comment: str | None = None
    notification_id: UUID
    audit_log_id: UUID
    message: str = Field(..., min_length=1)


class AdvisorRegistrationRequestListResponse(
    PaginatedResponse[AdvisorRegistrationRequestSummary]
):
    pass


class AdvisorRegistrationRequestDetailsResponse(
    SuccessResponse[AdvisorRegistrationRequestDetails]
):
    pass


class AdvisorReviewDecisionResponse(
    SuccessResponse[AdvisorReviewDecisionResult]
):
    pass
