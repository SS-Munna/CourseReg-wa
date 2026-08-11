import unittest
from unittest.mock import patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.errors import (
    api_http_exception_handler,
    api_unhandled_exception_handler,
    api_validation_exception_handler,
)
from app.api.routes.selections import router as selections_router
from app.database import Base, get_db
from app.database_errors import database_integrity_error_handler
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
from app.repositories.credit_repository import (
    CreditRepositoryError,
    InvalidCreditLoadError,
    require_valid_credit_load,
    selected_credit_total_query,
)
from app.security import create_access_token


class CreditValidationTestCase(unittest.TestCase):
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

        cls.session_factory = sessionmaker(bind=cls.engine)
        cls.app = FastAPI()
        cls.app.add_exception_handler(
            IntegrityError,
            database_integrity_error_handler,
        )
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
        cls.app.include_router(selections_router)

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

    def setUp(self):
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)
        self.db = self.session_factory()

    def tearDown(self):
        self.db.rollback()
        self.db.close()

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
        suffix: str,
        minimum_credit: int = 6,
        maximum_credit: int = 9,
    ) -> Student:
        department = Department(
            department_code=f"D-{suffix}",
            department_name=f"Department {suffix}",
        )
        program = Program(
            department=department,
            program_code=f"P-{suffix}",
            program_name=f"Program {suffix}",
            minimum_credit=minimum_credit,
            maximum_credit=maximum_credit,
        )
        advisor = Advisor(
            user=self.make_user(suffix=suffix, role="advisor"),
            department=department,
            employee_number=f"ADV-{suffix}",
        )
        student = Student(
            user=self.make_user(suffix=suffix, role="student"),
            program=program,
            advisor=advisor,
            student_number=f"STU-{suffix}",
            current_trimester=3,
        )
        self.db.add(student)
        self.db.flush()
        return student

    @staticmethod
    def make_course(*, suffix: str, credits: int = 3) -> Course:
        return Course(
            course_id=f"course-{suffix}",
            code=f"CSE-{suffix}",
            title=f"Course {suffix}",
            department="CSE",
            semester="Fall 2026",
            instructor="Dr. Credit",
            credits=credits,
            capacity=30,
            available_seats=30,
            is_mandatory=False,
            prerequisites=[],
            section="A",
            schedule=[],
        )

    @staticmethod
    def authorization_header(user: User) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {create_access_token(user.id)}"
        }

    def add_registration(
        self,
        *,
        student: Student,
        course: Course,
        registration_status: str,
    ) -> Registration:
        registration = Registration(
            student=student,
            section=course,
            registration_status=registration_status,
        )
        self.db.add(registration)
        return registration

    def test_selection_responses_update_credit_totals_after_mutations(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(suffix=suffix)
        first = self.make_course(
            suffix=f"{suffix}-first",
            credits=3,
        )
        second = self.make_course(
            suffix=f"{suffix}-second",
            credits=3,
        )
        self.db.add_all([first, second])
        self.db.commit()
        headers = self.authorization_header(student.user)

        first_response = self.client.post(
            "/api/selections",
            json={"course_id": first.course_id},
            headers=headers,
        )
        first_credit = first_response.json()["credit_validation"]

        self.assertEqual(first_response.status_code, 201)
        self.assertEqual(first_credit["selected_credits"], 3)
        self.assertEqual(
            first_credit["validation_status"],
            "below_minimum",
        )
        self.assertEqual(first_credit["minimum_shortfall"], 3)

        second_response = self.client.post(
            "/api/selections",
            json={"course_id": second.course_id},
            headers=headers,
        )
        second_credit = second_response.json()["credit_validation"]

        self.assertEqual(second_response.status_code, 201)
        self.assertEqual(second_credit["selected_credits"], 6)
        self.assertEqual(
            second_credit["validation_status"],
            "within_range",
        )
        self.assertTrue(second_credit["is_valid"])

        listed = self.client.get("/api/selections", headers=headers)

        self.assertEqual(listed.status_code, 200)
        self.assertEqual(len(listed.json()["data"]), 2)
        self.assertEqual(
            listed.json()["credit_validation"],
            second_credit,
        )

        removed = self.client.delete(
            f"/api/selections/{second.course_id}",
            headers=headers,
        )

        self.assertEqual(removed.status_code, 200)
        self.assertEqual(
            removed.json()["credit_validation"]["selected_credits"],
            3,
        )
        self.assertFalse(
            removed.json()["credit_validation"]["is_valid"]
        )

    def test_below_minimum_final_load_is_blocked_with_clear_values(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(
            suffix=suffix,
            minimum_credit=9,
            maximum_credit=18,
        )
        course = self.make_course(suffix=suffix, credits=6)
        self.add_registration(
            student=student,
            course=course,
            registration_status=RegistrationStatus.DRAFT.value,
        )
        self.db.commit()

        response = self.client.post(
            "/api/selections/credit-validation",
            headers=self.authorization_header(student.user),
        )

        self.assertEqual(response.status_code, 422)
        error = response.json()["error"]
        self.assertEqual(error["code"], "CREDIT_LOAD_BELOW_MINIMUM")
        self.assertEqual(error["details"]["selected_credits"], 6)
        self.assertEqual(error["details"]["minimum_credit"], 9)
        self.assertEqual(error["details"]["minimum_shortfall"], 3)
        self.assertIn("at least 9 credits", error["message"])
        self.assertIn("6 credits", error["message"])

    def test_above_maximum_draft_is_allowed_but_final_load_is_blocked(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(
            suffix=suffix,
            minimum_credit=3,
            maximum_credit=5,
        )
        first = self.make_course(
            suffix=f"{suffix}-first",
            credits=3,
        )
        second = self.make_course(
            suffix=f"{suffix}-second",
            credits=3,
        )
        self.db.add_all([first, second])
        self.db.commit()
        headers = self.authorization_header(student.user)

        self.client.post(
            "/api/selections",
            json={"course_id": first.course_id},
            headers=headers,
        )
        added = self.client.post(
            "/api/selections",
            json={"course_id": second.course_id},
            headers=headers,
        )
        validation = self.client.post(
            "/api/selections/credit-validation",
            headers=headers,
        )

        self.assertEqual(added.status_code, 201)
        self.assertEqual(
            added.json()["credit_validation"]["validation_status"],
            "above_maximum",
        )
        self.assertEqual(validation.status_code, 422)
        error = validation.json()["error"]
        self.assertEqual(error["code"], "CREDIT_LOAD_ABOVE_MAXIMUM")
        self.assertEqual(error["details"]["selected_credits"], 6)
        self.assertEqual(error["details"]["maximum_credit"], 5)
        self.assertEqual(error["details"]["maximum_excess"], 1)
        self.db.expire_all()
        self.assertEqual(self.db.query(Registration).count(), 2)

    def test_minimum_and_maximum_boundaries_pass_final_validation(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(
            suffix=suffix,
            minimum_credit=3,
            maximum_credit=6,
        )
        first = self.make_course(
            suffix=f"{suffix}-first",
            credits=3,
        )
        second = self.make_course(
            suffix=f"{suffix}-second",
            credits=3,
        )
        self.add_registration(
            student=student,
            course=first,
            registration_status=RegistrationStatus.DRAFT.value,
        )
        self.db.commit()
        headers = self.authorization_header(student.user)

        minimum = self.client.post(
            "/api/selections/credit-validation",
            headers=headers,
        )

        self.add_registration(
            student=student,
            course=second,
            registration_status=RegistrationStatus.PENDING.value,
        )
        self.db.commit()
        maximum = self.client.post(
            "/api/selections/credit-validation",
            headers=headers,
        )

        self.assertEqual(minimum.status_code, 200)
        self.assertEqual(minimum.json()["data"]["selected_credits"], 3)
        self.assertTrue(minimum.json()["data"]["is_valid"])
        self.assertEqual(maximum.status_code, 200)
        self.assertEqual(maximum.json()["data"]["selected_credits"], 6)
        self.assertTrue(maximum.json()["data"]["is_valid"])

    def test_only_active_registration_statuses_count_toward_load(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(
            suffix=suffix,
            minimum_credit=0,
            maximum_credit=20,
        )
        status_credits = (
            (RegistrationStatus.DRAFT.value, 1),
            (RegistrationStatus.PENDING.value, 2),
            (RegistrationStatus.APPROVED.value, 3),
            (RegistrationStatus.REJECTED.value, 4),
            (RegistrationStatus.DROPPED.value, 5),
        )

        for index, (registration_status, credits) in enumerate(
            status_credits
        ):
            course = self.make_course(
                suffix=f"{suffix}-{index}",
                credits=credits,
            )
            self.add_registration(
                student=student,
                course=course,
                registration_status=registration_status,
            )

        self.db.commit()

        response = self.client.get(
            "/api/selections/credit-validation",
            headers=self.authorization_header(student.user),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["selected_credits"], 6)
        self.assertTrue(response.json()["data"]["is_valid"])

    def test_credit_totals_are_scoped_to_authenticated_student(self):
        suffix = uuid4().hex[:8]
        owner = self.make_student(
            suffix=f"{suffix}-owner",
            minimum_credit=0,
            maximum_credit=9,
        )
        other = self.make_student(
            suffix=f"{suffix}-other",
            minimum_credit=0,
            maximum_credit=9,
        )
        owner_course = self.make_course(
            suffix=f"{suffix}-owner",
            credits=3,
        )
        other_course = self.make_course(
            suffix=f"{suffix}-other",
            credits=6,
        )
        self.add_registration(
            student=owner,
            course=owner_course,
            registration_status=RegistrationStatus.DRAFT.value,
        )
        self.add_registration(
            student=other,
            course=other_course,
            registration_status=RegistrationStatus.APPROVED.value,
        )
        self.db.commit()

        response = self.client.get(
            "/api/selections/credit-validation",
            headers=self.authorization_header(owner.user),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["selected_credits"], 3)

    def test_credit_routes_enforce_authentication_role_and_profile(self):
        suffix = uuid4().hex[:8]
        advisor = self.make_user(suffix=suffix, role="advisor")
        profileless = self.make_user(
            suffix=f"{suffix}-profileless",
            role="student",
        )
        self.db.add_all([advisor, profileless])
        self.db.commit()

        unauthenticated = self.client.get(
            "/api/selections/credit-validation"
        )
        forbidden = self.client.get(
            "/api/selections/credit-validation",
            headers=self.authorization_header(advisor),
        )
        missing_profile = self.client.get(
            "/api/selections/credit-validation",
            headers=self.authorization_header(profileless),
        )

        self.assertEqual(unauthenticated.status_code, 401)
        self.assertEqual(forbidden.status_code, 403)
        self.assertEqual(missing_profile.status_code, 404)
        self.assertEqual(
            missing_profile.json()["error"]["code"],
            "STUDENT_PROFILE_NOT_FOUND",
        )

    def test_repository_failures_are_safely_wrapped(self):
        student = self.make_student(suffix=uuid4().hex[:8])
        self.db.commit()

        with patch(
            "app.api.routes.selections.get_credit_load_validation",
            side_effect=CreditRepositoryError(
                "sensitive database server and stored values"
            ),
        ):
            response = self.client.get(
                "/api/selections/credit-validation",
                headers=self.authorization_header(student.user),
            )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json()["error"]["code"],
            "DATABASE_OPERATION_FAILED",
        )
        self.assertNotIn("database server", response.text.lower())
        self.assertNotIn("stored values", response.text.lower())

    def test_credit_calculation_failure_rolls_back_selection_mutations(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(suffix=suffix)
        add_course = self.make_course(
            suffix=f"{suffix}-add",
            credits=3,
        )
        remove_course = self.make_course(
            suffix=f"{suffix}-remove",
            credits=3,
        )
        existing = self.add_registration(
            student=student,
            course=remove_course,
            registration_status=RegistrationStatus.DRAFT.value,
        )
        self.db.add(add_course)
        self.db.commit()
        headers = self.authorization_header(student.user)

        with patch(
            "app.repositories.selection_repository."
            "get_credit_load_validation",
            side_effect=CreditRepositoryError("calculation failed"),
        ):
            added = self.client.post(
                "/api/selections",
                json={"course_id": add_course.course_id},
                headers=headers,
            )
            removed = self.client.delete(
                f"/api/selections/{remove_course.course_id}",
                headers=headers,
            )

        self.assertEqual(added.status_code, 500)
        self.assertEqual(removed.status_code, 500)
        self.db.expire_all()
        registrations = self.db.query(Registration).all()
        self.assertEqual(registrations, [existing])

    def test_reusable_guard_rejects_invalid_load_and_returns_valid_load(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(
            suffix=suffix,
            minimum_credit=3,
            maximum_credit=6,
        )
        self.db.commit()

        with self.assertRaises(InvalidCreditLoadError) as context:
            require_valid_credit_load(
                self.db,
                student_id=student.id,
            )

        self.assertEqual(
            context.exception.validation.validation_status,
            "below_minimum",
        )

        course = self.make_course(suffix=suffix, credits=3)
        self.add_registration(
            student=student,
            course=course,
            registration_status=RegistrationStatus.DRAFT.value,
        )
        self.db.commit()

        validation = require_valid_credit_load(
            self.db,
            student_id=student.id,
        )

        self.assertTrue(validation.is_valid)
        self.assertEqual(validation.selected_credits, 3)

    def test_openapi_documents_credit_read_and_final_validation(self):
        operations = coursepilot_app.openapi()["paths"][
            "/api/selections/credit-validation"
        ]

        for method in ("get", "post"):
            response_schema = operations[method]["responses"]["200"][
                "content"
            ]["application/json"]["schema"]
            self.assertTrue(
                response_schema["$ref"].endswith(
                    "/CreditLoadValidationResponse"
                )
            )

        error_schema = operations["post"]["responses"]["422"][
            "content"
        ]["application/json"]["schema"]
        self.assertTrue(error_schema["$ref"].endswith("/ErrorResponse"))

    def test_credit_total_query_compiles_for_postgresql(self):
        with Session() as db:
            statement = selected_credit_total_query(
                db,
                student_id=uuid4(),
            ).statement

        sql = str(
            statement.compile(
                dialect=postgresql.dialect(),
                compile_kwargs={"literal_binds": True},
            )
        )

        self.assertIn("sum(courses.credits)", sql)
        self.assertIn("registrations JOIN courses", sql)
        self.assertIn("registrations.student_id", sql)
        self.assertIn("'draft'", sql)
        self.assertIn("'pending'", sql)
        self.assertIn("'approved'", sql)


if __name__ == "__main__":
    unittest.main()
