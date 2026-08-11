from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, Field


DataT = TypeVar("DataT")


class SuccessResponse(BaseModel, Generic[DataT]):
    success: Literal[True] = True
    data: DataT


class ValidationIssue(BaseModel):
    field: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    type: str = Field(..., min_length=1)


class ErrorDetail(BaseModel):
    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    details: Any | None = None


class ErrorResponse(BaseModel):
    success: Literal[False] = False
    error: ErrorDetail


class ValidationErrorDetail(ErrorDetail):
    details: list[ValidationIssue]


class ValidationErrorResponse(BaseModel):
    success: Literal[False] = False
    error: ValidationErrorDetail


class PaginationMeta(BaseModel):
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1)
    total_items: int = Field(..., ge=0)
    total_pages: int = Field(..., ge=0)

    @classmethod
    def from_total(
        cls,
        *,
        page: int,
        page_size: int,
        total_items: int,
    ) -> "PaginationMeta":
        if page < 1:
            raise ValueError("page must be greater than or equal to 1")

        if page_size < 1:
            raise ValueError(
                "page_size must be greater than or equal to 1"
            )

        if total_items < 0:
            raise ValueError(
                "total_items must be greater than or equal to 0"
            )

        total_pages = (
            (total_items + page_size - 1) // page_size
            if total_items
            else 0
        )

        return cls(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
        )


class PaginatedResponse(BaseModel, Generic[DataT]):
    success: Literal[True] = True
    data: list[DataT]
    pagination: PaginationMeta
