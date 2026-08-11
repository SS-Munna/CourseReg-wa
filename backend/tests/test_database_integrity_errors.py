import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app.database_errors import database_integrity_error_handler
from app.main import app as coursepilot_app


class FakeDiagnostics:
    def __init__(self, constraint_name: str):
        self.constraint_name = constraint_name


class FakePostgreSQLError(Exception):
    def __init__(self, constraint_name: str):
        super().__init__("sensitive PostgreSQL error details")
        self.diag = FakeDiagnostics(constraint_name)


class DatabaseIntegrityErrorsTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = FastAPI()
        cls.app.add_exception_handler(
            IntegrityError,
            database_integrity_error_handler,
        )

        @cls.app.get("/constraint/{constraint_case}")
        def raise_constraint_error(constraint_case: str):
            original_errors = {
                "sqlite-course-id": Exception(
                    "UNIQUE constraint failed: courses.course_id"
                ),
                "sqlite-section": Exception(
                    "UNIQUE constraint failed: courses.code, "
                    "courses.semester, courses.section"
                ),
                "sqlite-seats": Exception(
                    "CHECK constraint failed: "
                    "ck_courses_available_seats_within_capacity"
                ),
                "postgres-capacity": FakePostgreSQLError(
                    "ck_courses_capacity_positive"
                ),
                "sqlite-prerequisite": Exception(
                    "UNIQUE constraint failed: "
                    "course_prerequisites.course_id, "
                    "course_prerequisites.prerequisite_course_id"
                ),
                "postgres-grade": FakePostgreSQLError(
                    "ck_completed_course_grade"
                ),
                "sqlite-selection": Exception(
                    "UNIQUE constraint failed: "
                    "registrations.student_id, registrations.section_id"
                ),
                "postgres-selection": FakePostgreSQLError(
                    "uq_registration_student_section"
                ),
                "unknown": Exception(
                    "sensitive database connection and record details"
                ),
            }
            raise IntegrityError(
                "INSERT INTO courses ...",
                {},
                original_errors[constraint_case],
            )

        cls.client = TestClient(cls.app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    def test_duplicate_course_id_returns_clear_conflict(self):
        response = self.client.get("/constraint/sqlite-course-id")

        self.assertEqual(response.status_code, 409)
        self.assertFalse(response.json()["success"])
        self.assertEqual(
            response.json()["error"],
            {
                "code": "DUPLICATE_COURSE_ID",
                "message": "A course with this course ID already exists.",
            },
        )

    def test_coursepilot_app_registers_integrity_error_handler(self):
        self.assertIs(
            coursepilot_app.exception_handlers[IntegrityError],
            database_integrity_error_handler,
        )

    def test_duplicate_section_returns_clear_conflict(self):
        response = self.client.get("/constraint/sqlite-section")

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.json()["error"]["code"],
            "DUPLICATE_COURSE_SECTION",
        )

    def test_sqlite_check_constraint_returns_validation_error(self):
        response = self.client.get("/constraint/sqlite-seats")

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json()["error"],
            {
                "code": "INVALID_AVAILABLE_SEATS",
                "message": (
                    "Available seats cannot be greater than section "
                    "capacity."
                ),
            },
        )

    def test_postgresql_constraint_name_is_translated(self):
        response = self.client.get("/constraint/postgres-capacity")

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json()["error"]["code"],
            "INVALID_SECTION_CAPACITY",
        )

    def test_prerequisite_constraints_use_clear_errors(self):
        duplicate = self.client.get("/constraint/sqlite-prerequisite")
        invalid_grade = self.client.get("/constraint/postgres-grade")

        self.assertEqual(duplicate.status_code, 409)
        self.assertEqual(
            duplicate.json()["error"]["code"],
            "DUPLICATE_COURSE_PREREQUISITE",
        )
        self.assertEqual(invalid_grade.status_code, 422)
        self.assertEqual(
            invalid_grade.json()["error"]["code"],
            "INVALID_COMPLETED_COURSE_GRADE",
        )

    def test_duplicate_selection_constraint_is_translated(self):
        sqlite_response = self.client.get(
            "/constraint/sqlite-selection"
        )
        postgres_response = self.client.get(
            "/constraint/postgres-selection"
        )

        for response in (sqlite_response, postgres_response):
            self.assertEqual(response.status_code, 409)
            self.assertEqual(
                response.json()["error"],
                {
                    "code": "DUPLICATE_SELECTION",
                    "message": (
                        "This course section is already selected or "
                        "registered."
                    ),
                },
            )

    def test_unknown_integrity_error_is_safe(self):
        response = self.client.get("/constraint/unknown")
        response_text = response.text.lower()

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.json()["error"]["code"],
            "DATABASE_CONSTRAINT_VIOLATION",
        )
        self.assertNotIn("connection", response_text)
        self.assertNotIn("record details", response_text)


if __name__ == "__main__":
    unittest.main()
