from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class SeatAllocationResult(BaseModel):
    registration_id: UUID
    student_id: UUID
    course_id: str = Field(..., min_length=1)
    code: str = Field(..., min_length=1)
    section: str = Field(..., min_length=1)
    registration_status: Literal["approved"]
    newly_allocated: bool
    capacity: int = Field(..., ge=1)
    approved_enrollment: int = Field(..., ge=1)
    available_seats: int = Field(..., ge=0)
