import unittest
from unittest.mock import patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.errors import (
    api_http_exception_handler,
    api_unhandled_exception_handler,
    api_validation_exception_handler,
)
from app.api.routes.courses import router as courses_router
from app.database import Base, get_db
from app.main import app as coursepilot_app
from app.models import (
    Advisor,
    Course,
    Department,
    Program,
    Registration,
    RegistrationStatus,
    Student,
    User,
)
from app.repositories.course_repository import (
    CourseRepositoryError,
    approved_enrollment_expression,
)


class SectionAvailabilityApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

        @event.listens_for(cls.engine, "connect")
        def enable_foreign_keys(dbapi_connection, _):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        Base.metadata.create_all(cls.engine)
        cls.session_factory = sessionmaker(bind=cls.engine)

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

        def override_get_db():
            db = cls.session_factory()
            try:
                yield db
            finally:
                db.close()

        cls.app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(
            cls.app,
            raise_server_exceptions=False,
        )

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        cls.app.dependency_overrides.clear()
        Base.metadata.drop_all(cls.engine)
        cls.engine.dispose()

    @staticmethod
    def make_user(*, suffix: str, role: str) -> User:
        return User(
            email=f"{role}-{suffix}@example.com",
            password_hash="test-password-hash",
            full_name=f"{role.title()} {suffix}",
            role=role,
        )

    def make_student(
        self,
        *,
        program: Program,
        advisor: Advisor,
        suffix: str,
    ) -> Student:
        return Student(
            user=self.make_user(suffix=suffix, role="student"),
            program=program,
            advisor=advisor,
            student_number=f"STU-{suffix}",
            current_trimester=3,
        )

    def make_section_context(
        self,
        *,
        db,
        capacity: int,
        statuses: tuple[str, ...],
    ) -> tuple[Course, Program, Advisor]:
        suffix = uuid4().hex[:10]
        department = Department(
            department_code=f"D-{suffix}",
            department_name=f"Department {suffix}",
        )
        program = Program(
            department=department,
            program_code=f"P-{suffix}",
            program_name=f"Program {suffix}",
            minimum_credit=9,
            maximum_credit=18,
        )
        advisor = Advisor(
            user=self.make_user(
                suffix=suffix,
                role="advisor",
            ),
            department=department,
            employee_number=f"ADV-{suffix}",
        )
        section = Course(
            course_id=f"availability-{suffix}",
            code=f"AVL {suffix}",
            title="Availability Test Section",
            department="Testing",
            semester="Fall 2026",
            instructor="Dr. Current Data",
            credits=3,
            capacity=capacity,
            available_seats=capacity,
            is_mandatory=False,
            section="A",
            schedule=[
                {
                    "day": "Sunday",
                    "start_time": "10:00",
                    "end_time": "11:30",
                    "room": "LAB-201",
                },
                {
                    "day": "Tuesday",
                    "start_time": "10:00",
                    "end_time": "11:30",
                    "room": "LAB-202",
                },
            ],
        )
        db.add_all([advisor, program, section])

        for index, registration_status in enumerate(statuses):
            student = self.make_student(
                program=program,
                advisor=advisor,
                suffix=f"{suffix}-{index}",
            )
            db.add(
                Registration(
                    student=student,
                    section=section,
                    registration_status=registration_status,
                )
            )

        db.commit()
        return section, program, advisor

    def test_availability_uses_current_approved_registrations(self):
        db = self.session_factory()
        self.addCleanup(db.close)
        statuses = (
            RegistrationStatus.APPROVED.value,
            RegistrationStatus.APPROVED.value,
            RegistrationStatus.DRAFT.value,
            RegistrationStatus.PENDING.value,
            RegistrationStatus.REJECTED.value,
            RegistrationStatus.DROPPED.value,
        )
        section, program, advisor = self.make_section_context(
            db=db,
            capacity=3,
            statuses=statuses,
        )

        response = self.client.get(
            f"/api/courses/{section.course_id}/availability"
        )
        data = response.json()["data"]

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertEqual(data["enrollment"], 2)
        self.assertEqual(data["capacity"], 3)
        self.assertEqual(data["available_seats"], 1)
        self.assertFalse(data["is_full"])
        self.assertEqual(data["instructor"], "Dr. Current Data")
        self.assertEqual(
            [meeting["room"] for meeting in data["schedule"]],
            ["LAB-201", "LAB-202"],
        )

        final_student = self.make_student(
            program=program,
            advisor=advisor,
            suffix=f"{uuid4().hex[:10]}-final-seat",
        )
        db.add(
            Registration(
                student=final_student,
                section=section,
                registration_status=RegistrationStatus.APPROVED.value,
            )
        )
        db.commit()

        refreshed = self.client.get(
            f"/api/courses/{section.course_id}/availability"
        )
        refreshed_data = refreshed.json()["data"]

        self.assertEqual(refreshed_data["enrollment"], 3)
        self.assertEqual(refreshed_data["available_seats"], 0)
        self.assertTrue(refreshed_data["is_full"])
        self.assertEqual(section.available_seats, 3)

        catalogue = self.client.get(
            "/api/courses",
            params={"search": section.code},
        )
        self.assertEqual(
            catalogue.json()["data"][0]["available_seats"],
            0,
        )

        available_only = self.client.get(
            "/api/courses",
            params={
                "search": section.code,
                "available_only": "true",
            },
        )
        self.assertEqual(available_only.json()["data"], [])

    def test_missing_section_returns_shared_not_found_error(self):
        response = self.client.get(
            "/api/courses/does-not-exist/availability"
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "success": False,
                "error": {
                    "code": "SECTION_NOT_FOUND",
                    "message": (
                        "The requested course section was not found."
                    ),
                },
            },
        )

    def test_catalogue_filters_course_level_case_insensitively(self):
        db = self.session_factory()
        self.addCleanup(db.close)
        suffix = uuid4().hex[:10]
        undergraduate = Course(
            course_id=f"undergraduate-{suffix}",
            code=f"UG {suffix}",
            title="Undergraduate Course",
            department="Testing",
            semester="Fall 2026",
            instructor="Dr. Level",
            credits=3,
            capacity=20,
            available_seats=20,
            is_mandatory=False,
            level="Undergraduate",
            section="A",
        )
        graduate = Course(
            course_id=f"graduate-{suffix}",
            code=f"GR {suffix}",
            title="Graduate Course",
            department="Testing",
            semester="Fall 2026",
            instructor="Dr. Level",
            credits=3,
            capacity=20,
            available_seats=20,
            is_mandatory=False,
            level="Graduate",
            section="A",
        )
        db.add_all([undergraduate, graduate])
        db.commit()

        response = self.client.get(
            "/api/courses",
            params={
                "search": suffix,
                "level": "graduate",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [course["course_id"] for course in response.json()["data"]],
            [graduate.course_id],
        )

    def test_blank_section_identifier_uses_validation_error_contract(self):
        response = self.client.get(
            "/api/courses/%20/availability"
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json()["error"]["code"],
            "REQUEST_VALIDATION_ERROR",
        )
        self.assertEqual(
            response.json()["error"]["details"][0]["field"],
            "path.course_id",
        )

    def test_repository_failure_does_not_expose_database_details(self):
        with patch(
            "app.api.routes.courses.get_section_availability",
            side_effect=CourseRepositoryError(
                "sensitive database host and SQL statement"
            ),
        ):
            response = self.client.get(
                "/api/courses/section-id/availability"
            )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json()["error"]["code"],
            "DATABASE_OPERATION_FAILED",
        )
        self.assertNotIn("database host", response.text.lower())
        self.assertNotIn("sql statement", response.text.lower())

    def test_openapi_documents_availability_response_contract(self):
        responses = coursepilot_app.openapi()["paths"][
            "/api/courses/{course_id}/availability"
        ]["get"]["responses"]

        success_schema = responses["200"]["content"][
            "application/json"
        ]["schema"]
        not_found_schema = responses["404"]["content"][
            "application/json"
        ]["schema"]

        self.assertTrue(
            success_schema["$ref"].endswith(
                "/SectionAvailabilityResponse"
            )
        )
        self.assertTrue(
            not_found_schema["$ref"].endswith("/ErrorResponse")
        )

    def test_availability_query_compiles_for_postgresql(self):
        enrollment = approved_enrollment_expression()

        with Session() as db:
            statement = (
                db.query(
                    Course,
                    enrollment.label("approved_enrollment"),
                )
                .filter(Course.capacity > enrollment)
                .statement
            )

        sql = str(
            statement.compile(
                dialect=postgresql.dialect(),
                compile_kwargs={"literal_binds": True},
            )
        )

        self.assertIn("count(registrations.id)", sql)
        self.assertIn("registration_status = 'approved'", sql)
        self.assertIn("courses.capacity >", sql)


if __name__ == "__main__":
    unittest.main()
