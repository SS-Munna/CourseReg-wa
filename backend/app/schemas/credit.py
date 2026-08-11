from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import SuccessResponse


CreditLoadStatus = Literal[
    "below_minimum",
    "within_range",
    "above_maximum",
]


class CreditLoadValidation(BaseModel):
    selected_credits: int = Field(..., ge=0)
    minimum_credit: int = Field(..., ge=0)
    maximum_credit: int = Field(..., ge=0)
    validation_status: CreditLoadStatus
    is_valid: bool
    minimum_shortfall: int = Field(..., ge=0)
    maximum_excess: int = Field(..., ge=0)
    message: str = Field(..., min_length=1)


class CreditLoadValidationResponse(
    SuccessResponse[CreditLoadValidation]
):
    pass
