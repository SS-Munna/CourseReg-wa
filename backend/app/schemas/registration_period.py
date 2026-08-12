from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import SuccessResponse


RegistrationPeriodState = Literal[
    "open",
    "closed",
    "upcoming",
    "not_configured",
]


class CurrentRegistrationPeriod(BaseModel):
    effective_status: RegistrationPeriodState
    registration_enabled: bool
    semester: str | None = None
    opening_time: datetime | None = None
    closing_time: datetime | None = None
    drop_deadline: date | None = None
    minimum_credit: int | None = Field(default=None, ge=0)
    maximum_credit: int | None = Field(default=None, ge=0)
    message: str = Field(..., min_length=1)


class CurrentRegistrationPeriodResponse(
    SuccessResponse[CurrentRegistrationPeriod]
):
    pass
