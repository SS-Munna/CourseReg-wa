import logging
from typing import Any

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas.common import (
    ErrorDetail,
    ErrorResponse,
    ValidationErrorDetail,
    ValidationErrorResponse,
    ValidationIssue,
)


logger = logging.getLogger(__name__)


HTTP_ERROR_CODES = {
    status.HTTP_400_BAD_REQUEST: "BAD_REQUEST",
    status.HTTP_401_UNAUTHORIZED: "UNAUTHORIZED",
    status.HTTP_403_FORBIDDEN: "FORBIDDEN",
    status.HTTP_404_NOT_FOUND: "NOT_FOUND",
    status.HTTP_405_METHOD_NOT_ALLOWED: "METHOD_NOT_ALLOWED",
    status.HTTP_409_CONFLICT: "CONFLICT",
    status.HTTP_422_UNPROCESSABLE_CONTENT: "UNPROCESSABLE_CONTENT",
    status.HTTP_429_TOO_MANY_REQUESTS: "TOO_MANY_REQUESTS",
}


STANDARD_ERROR_RESPONSE = {
    "model": ErrorResponse,
    "description": "The request could not be completed.",
}
REQUEST_VALIDATION_ERROR_RESPONSE = {
    "model": ValidationErrorResponse,
    "description": "The request contains invalid values.",
}


def error_response_content(
    *,
    code: str,
    message: str,
    details: Any | None = None,
) -> dict[str, Any]:
    response = ErrorResponse(
        error=ErrorDetail(
            code=code,
            message=message,
            details=details,
        )
    )

    return response.model_dump(mode="json", exclude_none=True)


def get_http_error_values(
    error: StarletteHTTPException,
) -> tuple[str, str, Any | None]:
    default_code = HTTP_ERROR_CODES.get(
        error.status_code,
        "HTTP_ERROR",
    )

    if isinstance(error.detail, dict):
        code = error.detail.get("code", default_code)
        message = error.detail.get("message", "The request failed.")
        details = error.detail.get("details")

        if not isinstance(code, str) or not code:
            code = default_code

        if not isinstance(message, str) or not message:
            message = "The request failed."

        return code, message, details

    if isinstance(error.detail, str) and error.detail:
        return default_code, error.detail, None

    return default_code, "The request failed.", None


async def api_http_exception_handler(
    _request: Request,
    error: StarletteHTTPException,
) -> JSONResponse:
    code, message, details = get_http_error_values(error)

    return JSONResponse(
        status_code=error.status_code,
        content=error_response_content(
            code=code,
            message=message,
            details=details,
        ),
        headers=error.headers,
    )


async def api_validation_exception_handler(
    _request: Request,
    error: RequestValidationError,
) -> JSONResponse:
    issues = [
        ValidationIssue(
            field=".".join(str(part) for part in item.get("loc", ()))
            or "request",
            message=item.get("msg", "Invalid value."),
            type=item.get("type", "value_error"),
        )
        for item in error.errors()
    ]
    response = ValidationErrorResponse(
        error=ValidationErrorDetail(
            code="REQUEST_VALIDATION_ERROR",
            message="The request contains invalid values.",
            details=issues,
        )
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=response.model_dump(mode="json"),
    )


async def api_unhandled_exception_handler(
    _request: Request,
    error: Exception,
) -> JSONResponse:
    logger.error(
        "Unhandled API exception",
        exc_info=(type(error), error, error.__traceback__),
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response_content(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected server error occurred.",
        ),
    )
