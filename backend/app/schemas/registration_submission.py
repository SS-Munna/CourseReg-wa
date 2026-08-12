from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import SuccessResponse
from app.schemas.course import CourseResponse
from app.schemas.credit import CreditLoadValidation
from app.schemas.schedule_conflict import ScheduleConflictValidation


class SubmissionCourse(BaseModel):
    course_id: str = Field(..., min_length=1)
    code: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    semester: str = Field(..., min_length=1)
    section: str = Field(..., min_length=1)
    registration_status: Literal["draft", "pending", "approved"]


class DuplicateCourseSelection(BaseModel):
    code: str = Field(..., min_length=1)
    selections: list[SubmissionCourse] = Field(..., min_length=2)


class CompletedCourseConflict(BaseModel):
    selected_course: SubmissionCourse
    completed_course_id: str = Field(..., min_length=1)
    completed_code: str = Field(..., min_length=1)
    completed_title: str = Field(..., min_length=1)
    completed_semester: str = Field(..., min_length=1)
    grade: str = Field(..., min_length=1)
    completed_at: date


class FullSection(BaseModel):
    course_id: str = Field(..., min_length=1)
    code: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    semester: str = Field(..., min_length=1)
    section: str = Field(..., min_length=1)
    capacity: int = Field(..., ge=1)
    approved_enrollment: int = Field(..., ge=0)
    available_seats: Literal[0] = 0
    waitlist_available: Literal[True] = True


class SubmittedRegistration(BaseModel):
    registration_id: UUID
    registration_status: Literal["pending"]
    submitted_at: datetime
    course: CourseResponse


class FinalRegistrationSubmission(BaseModel):
    registration_status: Literal["pending"]
    submitted_count: int = Field(..., ge=1)
    submitted_at: datetime
    registrations: list[SubmittedRegistration] = Field(
        ...,
        min_length=1,
    )
    credit_validation: CreditLoadValidation
    schedule_validation: ScheduleConflictValidation
    message: str = Field(..., min_length=1)


class FinalRegistrationSubmissionResponse(
    SuccessResponse[FinalRegistrationSubmission]
):
    pass
