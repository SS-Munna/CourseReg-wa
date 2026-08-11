import unittest
from unittest.mock import patch

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.errors import (
    api_http_exception_handler,
    api_unhandled_exception_handler,
    api_validation_exception_handler,
)
from app.api.routes.courses import router as courses_router
from app.database import get_db
from app.main import app as coursepilot_app
from app.repositories.course_repository import CourseRepositoryError
from app.schemas.common import (
    PaginatedResponse,
    PaginationMeta,
    SuccessResponse,
)


class QuantityRequest(BaseModel):
    quantity: int = Field(..., ge=1)


class ApiContractTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = FastAPI()
        cls.app.add_exception_handler(
            StarletteHTTPException,
            api_http_exception_handler,
        )
        cls.app.add_exception_handler(
            RequestValidationError,
            api_validation_exception_handler,
        )
        cls.app.add_exception_handler(
            Exception,
            api_unhandled_exception_handler,
        )
        cls.app.include_router(courses_router)
        cls.app.dependency_overrides[get_db] = lambda: object()

        @cls.app.get(
            "/success",
            response_model=SuccessResponse[dict[str, str]],
        )
        def success_response():
            return SuccessResponse(data={"status": "ready"})

        @cls.app.get("/http-error")
        def http_error_response():
            raise HTTPException(
                status_code=401,
                detail="A Bearer access token is required.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        @cls.app.get("/structured-error")
        def structured_error_response():
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "DUPLICATE_RECORD",
                    "message": "The record already exists.",
                    "details": {"field": "email"},
                },
            )

        @cls.app.post("/validate")
        def validate_request(payload: QuantityRequest):
            return SuccessResponse(data=payload)

        @cls.app.get("/unhandled")
        def unhandled_error_response():
            raise RuntimeError("sensitive database connection details")

        cls.client = TestClient(
            cls.app,
            raise_server_exceptions=False,
        )

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        cls.app.dependency_overrides.clear()

    def test_success_response_has_shared_envelope(self):
        response = self.client.get("/success")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "success": True,
                "data": {"status": "ready"},
            },
        )

    def test_pagination_response_calculates_total_pages(self):
        pagination = PaginationMeta.from_total(
            page=2,
            page_size=25,
            total_items=51,
        )
        response = PaginatedResponse[str](
            data=["course-a", "course-b"],
            pagination=pagination,
        )

        self.assertEqual(pagination.total_pages, 3)
        self.assertEqual(
            response.model_dump(),
            {
                "success": True,
                "data": ["course-a", "course-b"],
                "pagination": {
                    "page": 2,
                    "page_size": 25,
                    "total_items": 51,
                    "total_pages": 3,
                },
            },
        )

    def test_invalid_pagination_values_are_rejected(self):
        invalid_arguments = (
            {"page": 0, "page_size": 20, "total_items": 1},
            {"page": 1, "page_size": 0, "total_items": 1},
            {"page": 1, "page_size": 20, "total_items": -1},
        )

        for arguments in invalid_arguments:
            with self.subTest(arguments=arguments):
                with self.assertRaises(ValueError):
                    PaginationMeta.from_total(**arguments)

    def test_http_errors_use_shared_envelope_and_keep_headers(self):
        response = self.client.get("/http-error")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.headers.get("www-authenticate"),
            "Bearer",
        )
        self.assertEqual(
            response.json(),
            {
                "success": False,
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "A Bearer access token is required.",
                },
            },
        )

    def test_structured_http_error_keeps_code_and_safe_details(self):
        response = self.client.get("/structured-error")

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.json()["error"],
            {
                "code": "DUPLICATE_RECORD",
                "message": "The record already exists.",
                "details": {"field": "email"},
            },
        )

    def test_request_validation_errors_list_affected_fields(self):
        response = self.client.post(
            "/validate",
            json={"quantity": 0},
        )

        self.assertEqual(response.status_code, 422)
        self.assertFalse(response.json()["success"])
        self.assertEqual(
            response.json()["error"]["code"],
            "REQUEST_VALIDATION_ERROR",
        )
        self.assertEqual(
            response.json()["error"]["details"][0]["field"],
            "body.quantity",
        )

    def test_unhandled_errors_return_safe_server_response(self):
        with self.assertLogs("app.api.errors", level="ERROR"):
            response = self.client.get("/unhandled")
        response_text = response.text.lower()

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json()["error"]["code"],
            "INTERNAL_SERVER_ERROR",
        )
        self.assertNotIn("database connection", response_text)

    def test_repository_errors_do_not_expose_database_details(self):
        with patch(
            "app.api.routes.courses.list_courses",
            side_effect=CourseRepositoryError(
                "sensitive database host and statement"
            ),
        ):
            response = self.client.get("/api/courses")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json()["error"]["code"],
            "DATABASE_OPERATION_FAILED",
        )
        self.assertNotIn("database host", response.text.lower())

    def test_application_registers_all_shared_error_handlers(self):
        self.assertIs(
            coursepilot_app.exception_handlers[
                StarletteHTTPException
            ],
            api_http_exception_handler,
        )
        self.assertIs(
            coursepilot_app.exception_handlers[
                RequestValidationError
            ],
            api_validation_exception_handler,
        )
        self.assertIs(
            coursepilot_app.exception_handlers[Exception],
            api_unhandled_exception_handler,
        )

    def test_openapi_documents_shared_success_and_error_schemas(self):
        openapi_schema = coursepilot_app.openapi()
        register_responses = openapi_schema["paths"][
            "/api/auth/register"
        ]["post"]["responses"]

        success_schema = register_responses["201"]["content"][
            "application/json"
        ]["schema"]
        validation_schema = register_responses["422"]["content"][
            "application/json"
        ]["schema"]

        self.assertTrue(success_schema["$ref"].endswith("/AuthResponse"))
        self.assertTrue(
            validation_schema["$ref"].endswith(
                "/ValidationErrorResponse"
            )
        )


if __name__ == "__main__":
    unittest.main()
