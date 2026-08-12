from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


PromotionOutcome = Literal[
    "promoted",
    "section_full",
    "queue_empty",
    "no_eligible_student",
]


class WaitlistPromotionResult(BaseModel):
    course_id: str = Field(..., min_length=1)
    code: str = Field(..., min_length=1)
    section: str = Field(..., min_length=1)
    promoted: bool
    outcome: PromotionOutcome
    capacity: int = Field(..., ge=1)
    approved_enrollment: int = Field(..., ge=0)
    available_seats: int = Field(..., ge=0)
    expired_waitlist_entry_ids: list[UUID] = Field(default_factory=list)
    waitlist_entry_id: UUID | None = None
    student_id: UUID | None = None
    registration_id: UUID | None = None
    registration_status: Literal["approved"] | None = None
    waitlist_status: Literal["promoted"] | None = None
    promoted_at: datetime | None = None
    notification_id: UUID | None = None
    audit_log_id: UUID | None = None
