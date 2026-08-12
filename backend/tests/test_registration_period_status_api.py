from datetime import date, datetime, timedelta, timezone
import unittest
from unittest.mock import patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.errors import (
    api_http_exception_handler,
    api_unhandled_exception_handler,
    api_validation_exception_handler,
)
from app.api.routes.registration_periods import (
    router as registration_periods_router,
)
from app.database import Base, get_db
from app.main import app as coursepilot_app
from app.models import RegistrationPeriod, Semester, User
from app.repositories.registration_period_status_repository import (
    RegistrationPeriodStatusRepositoryError,
)
from app.security import create_access_token


class RegistrationPeriodStatusApiTestCase(unittest.TestCase):
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
        cls.app.include_router(registration_periods_router)

        def override_get_db():
            db = cls.session_factory()
            try:
                yield db
            finally:
                db.close()

        cls.app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(cls.app, raise_server_exceptions=False)

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

    def add_user(self, *, role: str = "student") -> User:
        suffix = uuid4().hex[:10]
        user = User(
            email=f"{role}-{suffix}@example.com",
            password_hash="test-password-hash",
            full_name=f"{role.title()} {suffix}",
            role=role,
        )
        self.db.add(user)
        self.db.commit()
        return user

    @staticmethod
    def headers_for(user: User) -> dict[str, str]:
        return {
            "Authorization": (
                f"Bearer {create_access_token(user_id=user.id)}"
            )
        }

    def add_period(
        self,
        *,
        opening_time: datetime,
        closing_time: datetime,
        stored_status: str = "scheduled",
        semester_name: str = "Fall",
        academic_year: int = 2026,
    ) -> RegistrationPeriod:
        semester = Semester(
            semester_name=semester_name,
            academic_year=academic_year,
            start_date=date(academic_year, 1, 1),
            end_date=date(academic_year, 12, 31),
            status="active",
        )
        period = RegistrationPeriod(
            semester=semester,
            opening_time=opening_time,
            closing_time=closing_time,
            drop_deadline=date(academic_year, 10, 15),
            minimum_credit=9,
            maximum_credit=18,
            status=stored_status,
        )
        self.db.add(period)
        self.db.commit()
        return period

    def test_open_period_returns_registration_window(self):
        now = datetime.now(timezone.utc)
        self.add_period(
            opening_time=now - timedelta(days=2),
            closing_time=now + timedelta(days=2),
        )
        user = self.add_user()

        response = self.client.get(
            "/api/registration-periods/current",
            headers=self.headers_for(user),
        )
        data = response.json()["data"]

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertEqual(data["effective_status"], "open")
        self.assertTrue(data["registration_enabled"])
        self.assertEqual(data["semester"], "Fall 2026")
        self.assertEqual(data["minimum_credit"], 9)
        self.assertEqual(data["maximum_credit"], 18)
        self.assertIsNotNone(data["closing_time"])

    def test_upcoming_and_explicit_closed_statuses_are_derived_safely(self):
        user = self.add_user()
        now = datetime.now(timezone.utc)
        self.add_period(
            opening_time=now + timedelta(days=2),
            closing_time=now + timedelta(days=5),
            semester_name="Spring",
            academic_year=2027,
        )
        self.add_period(
            opening_time=now - timedelta(days=2),
            closing_time=now + timedelta(days=2),
            stored_status="closed",
            semester_name="Summer",
            academic_year=2027,
        )

        upcoming = self.client.get(
            "/api/registration-periods/current",
            params={"semester": "  spring   2027  "},
            headers=self.headers_for(user),
        ).json()["data"]
        closed = self.client.get(
            "/api/registration-periods/current",
            params={"semester": "Summer 2027"},
            headers=self.headers_for(user),
        ).json()["data"]

        self.assertEqual(upcoming["effective_status"], "upcoming")
        self.assertFalse(upcoming["registration_enabled"])
        self.assertEqual(closed["effective_status"], "closed")
        self.assertFalse(closed["registration_enabled"])

    def test_no_configured_period_is_a_browsable_success_state(self):
        user = self.add_user()

        response = self.client.get(
            "/api/registration-periods/current",
            params={"semester": "Fall 2030"},
            headers=self.headers_for(user),
        )
        data = response.json()["data"]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["effective_status"], "not_configured")
        self.assertFalse(data["registration_enabled"])
        self.assertEqual(data["semester"], "Fall 2030")
        self.assertIn("browsing remains available", data["message"].lower())

    def test_student_role_is_required_but_student_profile_is_not(self):
        without_auth = self.client.get(
            "/api/registration-periods/current"
        )
        advisor = self.add_user(role="advisor")
        forbidden = self.client.get(
            "/api/registration-periods/current",
            headers=self.headers_for(advisor),
        )
        student_without_profile = self.add_user(role="student")
        allowed = self.client.get(
            "/api/registration-periods/current",
            headers=self.headers_for(student_without_profile),
        )

        self.assertEqual(without_auth.status_code, 401)
        self.assertEqual(forbidden.status_code, 403)
        self.assertEqual(allowed.status_code, 200)

    def test_blank_semester_uses_shared_validation_contract(self):
        user = self.add_user()
        response = self.client.get(
            "/api/registration-periods/current",
            params={"semester": "   "},
            headers=self.headers_for(user),
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json()["error"]["code"],
            "REQUEST_VALIDATION_ERROR",
        )
        self.assertEqual(
            response.json()["error"]["details"][0]["field"],
            "query.semester",
        )

    def test_repository_failure_returns_safe_error(self):
        user = self.add_user()

        with patch(
            "app.api.routes.registration_periods."
            "get_current_registration_period_status",
            side_effect=RegistrationPeriodStatusRepositoryError(
                "sensitive database host and statement"
            ),
        ):
            response = self.client.get(
                "/api/registration-periods/current",
                headers=self.headers_for(user),
            )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json()["error"]["code"],
            "DATABASE_OPERATION_FAILED",
        )
        self.assertNotIn("database host", response.text.lower())

    def test_openapi_documents_period_status_contract(self):
        responses = coursepilot_app.openapi()["paths"][
            "/api/registration-periods/current"
        ]["get"]["responses"]

        self.assertTrue(
            responses["200"]["content"]["application/json"]["schema"][
                "$ref"
            ].endswith("/CurrentRegistrationPeriodResponse")
        )
        self.assertTrue(
            responses["401"]["content"]["application/json"]["schema"][
                "$ref"
            ].endswith("/ErrorResponse")
        )


if __name__ == "__main__":
    unittest.main()
