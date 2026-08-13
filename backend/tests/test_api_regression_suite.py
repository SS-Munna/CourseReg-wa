from pathlib import Path
import tempfile
import unittest
from uuid import uuid4

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.errors import (
    api_http_exception_handler,
    api_unhandled_exception_handler,
    api_validation_exception_handler,
)
from app.api.routes.admin import router as admin_router
from app.api.routes.advisor_reviews import router as advisor_reviews_router
from app.api.routes.audit_logs import router as audit_logs_router
from app.api.routes.auth import router as auth_router
from app.api.routes.courses import router as courses_router
from app.api.routes.notifications import router as notifications_router
from app.api.routes.registration_periods import router as registration_periods_router
from app.api.routes.registrations import router as registrations_router
from app.api.routes.selections import router as selections_router
from app.api.routes.waitlists import router as waitlists_router
from app.database import Base, get_db
from app.database_errors import database_integrity_error_handler
from app.models import User
from app.security import create_access_token, verify_password


class ApiRegressionSuiteTestCase(unittest.TestCase):
    """Cross-route regression checks for the public CoursePilot API surface."""

    @classmethod
    def setUpClass(cls):
        cls.temporary_directory = tempfile.TemporaryDirectory()
        database_path = Path(cls.temporary_directory.name) / "api-regression.sqlite"
        cls.engine = create_engine(
            f"sqlite:///{database_path}",
            connect_args={"check_same_thread": False},
        )
        cls.session_factory = sessionmaker(bind=cls.engine)

        cls.app = FastAPI(title="CoursePilot API regression suite")
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
        cls.app.include_router(auth_router)
        cls.app.include_router(notifications_router)
        cls.app.include_router(admin_router)
        cls.app.include_router(audit_logs_router)
        cls.app.include_router(courses_router)
        cls.app.include_router(registration_periods_router)
        cls.app.include_router(selections_router)
        cls.app.include_router(registrations_router)
        cls.app.include_router(waitlists_router)
        cls.app.include_router(advisor_reviews_router)

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
        cls.temporary_directory.cleanup()

    def setUp(self):
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)
        self.db = self.session_factory()

    def tearDown(self):
        self.db.rollback()
        self.db.close()

    def add_user(
        self,
        role: str,
        *,
        status: str = "active",
        suffix: str | None = None,
    ) -> User:
        unique = suffix or uuid4().hex[:10]
        user = User(
            full_name=f"{role.title()} Regression User",
            email=f"{role}-{unique}@example.com",
            password_hash="test-password-hash",
            role=role,
            account_status=status,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    @staticmethod
    def auth(user: User) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {create_access_token(user.id)}"
        }

    def assert_error(
        self,
        response,
        *,
        status_code: int,
        code: str,
    ) -> None:
        self.assertEqual(response.status_code, status_code)
        payload = response.json()
        self.assertFalse(payload["success"])
        self.assertEqual(payload["error"]["code"], code)

    def test_expected_api_surface_is_registered(self):
        expected_operations = {
            ("post", "/api/auth/register"),
            ("post", "/api/auth/login"),
            ("get", "/api/auth/me"),
            ("get", "/api/courses"),
            ("get", "/api/courses/{course_id}/availability"),
            ("get", "/api/courses/{course_id}/prerequisite-validation"),
            ("get", "/api/registration-periods/current"),
            ("get", "/api/selections"),
            ("post", "/api/selections"),
            ("get", "/api/selections/credit-validation"),
            ("post", "/api/selections/credit-validation"),
            ("get", "/api/selections/schedule-conflict-validation"),
            ("post", "/api/selections/schedule-conflict-validation"),
            ("delete", "/api/selections/{course_id}"),
            ("get", "/api/registrations"),
            ("post", "/api/registrations/submit"),
            ("post", "/api/registrations/{registration_id}/drop"),
            ("get", "/api/waitlists"),
            ("post", "/api/waitlists"),
            ("delete", "/api/waitlists/{course_id}"),
            ("get", "/api/advisor/registration-requests"),
            ("get", "/api/advisor/registration-requests/{request_id}"),
            (
                "post",
                "/api/advisor/registration-requests/{request_id}/decision",
            ),
            ("get", "/api/notifications"),
            ("patch", "/api/notifications/{notification_id}/read"),
            ("post", "/api/notifications/read-all"),
            ("get", "/api/admin/overview"),
            ("get", "/api/admin/users"),
            ("get", "/api/admin/departments"),
            ("post", "/api/admin/departments"),
            ("get", "/api/admin/programs"),
            ("post", "/api/admin/programs"),
            ("get", "/api/admin/advisors"),
            ("post", "/api/admin/students/{user_id}/profile"),
            ("post", "/api/admin/staff"),
            ("patch", "/api/admin/users/{user_id}/access"),
            ("get", "/api/admin/audit-logs"),
        }
        schema = self.app.openapi()
        actual_operations = {
            (method.lower(), path)
            for path, operations in schema["paths"].items()
            for method in operations
            if method.lower()
            in {"get", "post", "put", "patch", "delete"}
        }

        self.assertTrue(
            expected_operations.issubset(actual_operations),
            expected_operations - actual_operations,
        )

    def test_protected_get_routes_require_bearer_token(self):
        protected_paths = (
            "/api/auth/me",
            "/api/notifications",
            "/api/admin/overview",
            "/api/admin/audit-logs",
            "/api/registration-periods/current",
            "/api/selections",
            "/api/registrations",
            "/api/waitlists",
            "/api/advisor/registration-requests",
            "/api/courses/missing/prerequisite-validation",
        )

        for path in protected_paths:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assert_error(
                    response,
                    status_code=401,
                    code="AUTHENTICATION_REQUIRED",
                )
                self.assertEqual(
                    response.headers.get("www-authenticate"),
                    "Bearer",
                )

    def test_invalid_token_is_rejected_consistently(self):
        headers = {"Authorization": "Bearer definitely-not-a-jwt"}

        for path in (
            "/api/auth/me",
            "/api/notifications",
            "/api/admin/overview",
            "/api/selections",
        ):
            with self.subTest(path=path):
                response = self.client.get(path, headers=headers)
                self.assert_error(
                    response,
                    status_code=401,
                    code="INVALID_ACCESS_TOKEN",
                )

    def test_token_for_unknown_user_is_rejected(self):
        response = self.client.get(
            "/api/auth/me",
            headers={
                "Authorization": (
                    f"Bearer {create_access_token(uuid4())}"
                )
            },
        )

        self.assert_error(
            response,
            status_code=401,
            code="TOKEN_USER_NOT_FOUND",
        )

    def test_suspended_user_token_is_rejected_across_resources(self):
        suspended = self.add_user("student", status="suspended")

        for path in ("/api/auth/me", "/api/notifications", "/api/selections"):
            with self.subTest(path=path):
                response = self.client.get(path, headers=self.auth(suspended))
                self.assert_error(
                    response,
                    status_code=403,
                    code="ACCOUNT_NOT_ACTIVE",
                )

    def test_student_cannot_enter_privileged_workspaces(self):
        student = self.add_user("student")

        for path in (
            "/api/admin/overview",
            "/api/admin/audit-logs",
            "/api/advisor/registration-requests",
        ):
            with self.subTest(path=path):
                response = self.client.get(path, headers=self.auth(student))
                self.assert_error(
                    response,
                    status_code=403,
                    code="INSUFFICIENT_PERMISSIONS",
                )

    def test_advisor_cannot_enter_student_or_admin_workspaces(self):
        advisor = self.add_user("advisor")

        for path in ("/api/selections", "/api/admin/overview"):
            with self.subTest(path=path):
                response = self.client.get(path, headers=self.auth(advisor))
                self.assert_error(
                    response,
                    status_code=403,
                    code="INSUFFICIENT_PERMISSIONS",
                )

    def test_department_admin_cannot_enter_student_advisor_or_audit_routes(self):
        department_admin = self.add_user("department-admin")

        for path in (
            "/api/selections",
            "/api/advisor/registration-requests",
            "/api/admin/audit-logs",
        ):
            with self.subTest(path=path):
                response = self.client.get(
                    path,
                    headers=self.auth(department_admin),
                )
                self.assert_error(
                    response,
                    status_code=403,
                    code="INSUFFICIENT_PERMISSIONS",
                )

    def test_system_admin_can_read_administration_resources(self):
        system_admin = self.add_user("system-admin")

        for path in (
            "/api/admin/overview",
            "/api/admin/users",
            "/api/admin/departments",
            "/api/admin/programs",
            "/api/admin/advisors",
            "/api/admin/audit-logs",
        ):
            with self.subTest(path=path):
                response = self.client.get(
                    path,
                    headers=self.auth(system_admin),
                )
                self.assertEqual(response.status_code, 200, response.text)
                self.assertTrue(response.json()["success"])

    def test_public_registration_cannot_self_assign_privileged_access(self):
        suffix = uuid4().hex[:10]
        password = "StudentPass123!"
        email = f"self-register-{suffix}@example.com"

        response = self.client.post(
            "/api/auth/register",
            json={
                "name": "Self Registered Student",
                "email": email,
                "password": password,
                "role": "system-admin",
                "account_status": "active",
            },
        )

        self.assertEqual(response.status_code, 201, response.text)
        payload = response.json()["data"]
        self.assertEqual(payload["user"]["role"], "student")
        self.assertNotIn("password", response.text.lower())

        stored = self.db.query(User).filter(User.email == email).one()
        self.assertEqual(stored.role, "student")
        self.assertEqual(stored.account_status, "active")
        self.assertNotEqual(stored.password_hash, password)
        self.assertTrue(verify_password(password, stored.password_hash))

    def test_registration_login_and_me_form_real_auth_lifecycle(self):
        suffix = uuid4().hex[:10]
        email = f"lifecycle-{suffix}@example.com"
        password = "LifecyclePass123!"

        registered = self.client.post(
            "/api/auth/register",
            json={
                "name": "Lifecycle Student",
                "email": email,
                "password": password,
            },
        )
        self.assertEqual(registered.status_code, 201)

        logged_in = self.client.post(
            "/api/auth/login",
            json={"email": email, "password": password},
        )
        self.assertEqual(logged_in.status_code, 200)
        token = logged_in.json()["data"]["token"]

        current = self.client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(current.status_code, 200)
        self.assertEqual(current.json()["data"]["email"], email)
        self.assertEqual(current.json()["data"]["role"], "student")

    def test_duplicate_registration_and_bad_login_use_safe_errors(self):
        suffix = uuid4().hex[:10]
        email = f"safe-errors-{suffix}@example.com"
        payload = {
            "name": "Safe Error Student",
            "email": email,
            "password": "CorrectPass123!",
        }
        first = self.client.post("/api/auth/register", json=payload)
        duplicate = self.client.post("/api/auth/register", json=payload)
        bad_login = self.client.post(
            "/api/auth/login",
            json={"email": email, "password": "WrongPass123!"},
        )

        self.assertEqual(first.status_code, 201)
        self.assert_error(
            duplicate,
            status_code=409,
            code="EMAIL_ALREADY_REGISTERED",
        )
        self.assert_error(
            bad_login,
            status_code=401,
            code="INVALID_CREDENTIALS",
        )
        self.assertNotIn("password_hash", duplicate.text)
        self.assertNotIn("password_hash", bad_login.text)

    def test_public_course_catalog_is_available_without_authentication(self):
        response = self.client.get("/api/courses")

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["data"], [])

    def test_authenticated_notification_feed_starts_empty(self):
        student = self.add_user("student")

        response = self.client.get(
            "/api/notifications",
            headers=self.auth(student),
        )

        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()["data"]
        self.assertEqual(data["unread_count"], 0)
        self.assertEqual(data["notifications"], [])

    def test_request_validation_uses_shared_error_contract(self):
        response = self.client.post(
            "/api/auth/register",
            json={
                "name": "A",
                "email": "not-an-email",
                "password": "123",
            },
        )

        self.assert_error(
            response,
            status_code=422,
            code="REQUEST_VALIDATION_ERROR",
        )
        fields = {
            item["field"]
            for item in response.json()["error"]["details"]
        }
        self.assertIn("body.name", fields)
        self.assertIn("body.email", fields)
        self.assertIn("body.password", fields)

    def test_pending_and_rejected_accounts_cannot_reuse_protected_routes(self):
        cases = (
            ("advisor", "pending"),
            ("department-admin", "rejected"),
        )

        for role, status in cases:
            with self.subTest(role=role, status=status):
                user = self.add_user(role, status=status)
                response = self.client.get(
                    "/api/auth/me",
                    headers=self.auth(user),
                )
                self.assert_error(
                    response,
                    status_code=403,
                    code="ACCOUNT_NOT_ACTIVE",
                )

    def test_system_admin_cannot_use_student_registration_routes(self):
        system_admin = self.add_user("system-admin")

        for path in ("/api/selections", "/api/registrations", "/api/waitlists"):
            with self.subTest(path=path):
                response = self.client.get(
                    path,
                    headers=self.auth(system_admin),
                )
                self.assert_error(
                    response,
                    status_code=403,
                    code="INSUFFICIENT_PERMISSIONS",
                )

    def test_advisor_cannot_read_global_audit_history(self):
        advisor = self.add_user("advisor")

        response = self.client.get(
            "/api/admin/audit-logs",
            headers=self.auth(advisor),
        )

        self.assert_error(
            response,
            status_code=403,
            code="INSUFFICIENT_PERMISSIONS",
        )

    def test_openapi_keeps_security_sensitive_error_responses_documented(self):
        schema = self.app.openapi()
        cases = {
            ("/api/auth/me", "get"): {"200", "401"},
            ("/api/selections", "get"): {"200", "401", "403"},
            ("/api/admin/overview", "get"): {"200", "401", "403"},
            (
                "/api/advisor/registration-requests",
                "get",
            ): {"200", "401", "403"},
            ("/api/notifications", "get"): {"200", "401", "403"},
            ("/api/admin/audit-logs", "get"): {"200", "401", "403"},
        }

        for (path, method), expected_codes in cases.items():
            with self.subTest(path=path, method=method):
                documented = set(
                    schema["paths"][path][method]["responses"]
                )
                self.assertTrue(
                    expected_codes.issubset(documented),
                    expected_codes - documented,
                )


if __name__ == "__main__":
    unittest.main()
