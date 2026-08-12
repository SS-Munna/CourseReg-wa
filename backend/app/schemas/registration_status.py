from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import SuccessResponse
from app.schemas.course import CourseResponse
from app.schemas.waitlist import WaitlistEntryDetails
from app.schemas.waitlist_promotion import WaitlistPromotionResult


RegistrationState = Literal[
    "draft",
    "pending",
    "approved",
    "rejected",
    "dropped",
]
DropEligibilityReason = Literal[
    "eligible",
    "registration_not_approved",
    "drop_period_not_configured",
    "drop_deadline_passed",
]


class DropEligibility(BaseModel):
    eligible: bool
    drop_deadline: date | None = None
    reason: DropEligibilityReason
    message: str = Field(..., min_length=1)


class StudentRegistrationStatus(BaseModel):
    registration_id: UUID
    registration_status: RegistrationState
    submitted_at: datetime | None = None
    reviewed_at: datetime | None = None
    reviewed_by_advisor_id: UUID | None = None
    advisor_comment: str | None = None
    updated_at: datetime
    course: CourseResponse
    drop_eligibility: DropEligibility


class StudentWaitlistStatus(WaitlistEntryDetails):
    registration_status: Literal["waitlisted"] = "waitlisted"


class RegistrationStatusOverview(BaseModel):
    registrations: list[StudentRegistrationStatus]
    waitlist_entries: list[StudentWaitlistStatus]


class CourseDropResult(BaseModel):
    registration_id: UUID
    student_id: UUID
    registration_status: Literal["dropped"]
    dropped_at: datetime
    drop_deadline: date
    course: CourseResponse
    notification_id: UUID
    audit_log_id: UUID
    waitlist_promotion: WaitlistPromotionResult
    message: str = Field(..., min_length=1)


class RegistrationStatusOverviewResponse(
    SuccessResponse[RegistrationStatusOverview]
):
    pass


class CourseDropResponse(SuccessResponse[CourseDropResult]):
    pass
