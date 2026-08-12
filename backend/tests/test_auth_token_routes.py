import unittest
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.errors import api_http_exception_handler
from app.api.routes.auth import router
from app.database import get_db
from app.security import decode_access_token


class AuthTokenRoutesTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = FastAPI()
        cls.app.add_exception_handler(
            StarletteHTTPException,
            api_http_exception_handler,
        )
        cls.app.include_router(router)
        cls.app.dependency_overrides[get_db] = lambda: object()
        cls.client = TestClient(cls.app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        cls.app.dependency_overrides.clear()

    def assert_valid_jwt_response(self, response, user_id):
        self.assertIn(response.status_code, (200, 201))

        response_data = response.json()
        self.assertTrue(response_data["success"])
        token = response_data["data"]["token"]

        self.assertNotEqual(token, f"demo-token-{user_id}")
        self.assertEqual(token.count("."), 2)

        payload = decode_access_token(token)
        self.assertEqual(payload["sub"], str(user_id))
        self.assertIn("iat", payload)
        self.assertIn("exp", payload)

        self.assertEqual(
            response_data["data"]["user"]["id"],
            str(user_id),
        )
        self.assertEqual(
            response_data["data"]["user"]["role"],
            "student",
        )

    def test_registration_returns_signed_jwt(self):
        user_id = uuid4()
        user = SimpleNamespace(
            id=user_id,
            full_name="New Student",
            email="newstudent@example.com",
            role="student",
        )

        with (
            patch(
                "app.api.routes.auth.find_user_by_email",
                return_value=None,
            ),
            patch(
                "app.api.routes.auth.create_user",
                return_value=user,
            ),
        ):
            response = self.client.post(
                "/api/auth/register",
                json={
                    "name": "New Student",
                    "email": "newstudent@example.com",
                    "password": "SecurePass123!",
                },
            )

        self.assert_valid_jwt_response(response, user_id)

    def test_login_returns_signed_jwt(self):
        user_id = uuid4()
        user = SimpleNamespace(
            id=user_id,
            full_name="Existing Student",
            email="student@example.com",
            role="student",
        )

        with patch(
            "app.api.routes.auth.verify_user_credentials",
            return_value=user,
        ):
            response = self.client.post(
                "/api/auth/login",
                json={
                    "email": "student@example.com",
                    "password": "SecurePass123!",
                },
            )

        self.assert_valid_jwt_response(response, user_id)

    def test_duplicate_registration_uses_shared_error_response(self):
        with patch(
            "app.api.routes.auth.find_user_by_email",
            return_value=object(),
        ):
            response = self.client.post(
                "/api/auth/register",
                json={
                    "name": "Existing Student",
                    "email": "existing@example.com",
                    "password": "SecurePass123!",
                },
            )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.json(),
            {
                "success": False,
                "error": {
                    "code": "EMAIL_ALREADY_REGISTERED",
                    "message": (
                        "An account with this email already exists."
                    ),
                },
            },
        )

    def test_invalid_login_uses_shared_error_response(self):
        with patch(
            "app.api.routes.auth.verify_user_credentials",
            return_value=None,
        ):
            response = self.client.post(
                "/api/auth/login",
                json={
                    "email": "student@example.com",
                    "password": "SecurePass123!",
                },
            )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json(),
            {
                "success": False,
                "error": {
                    "code": "INVALID_CREDENTIALS",
                    "message": "Invalid email or password.",
                },
            },
        )


    def test_inactive_account_cannot_log_in(self):
        user = SimpleNamespace(
            id=uuid4(),
            full_name="Pending Advisor",
            email="pending@example.com",
            role="advisor",
            account_status="pending",
        )

        with patch(
            "app.api.routes.auth.verify_user_credentials",
            return_value=user,
        ):
            response = self.client.post(
                "/api/auth/login",
                json={
                    "email": "pending@example.com",
                    "password": "SecurePass123!",
                },
            )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()["error"],
            {
                "code": "ACCOUNT_NOT_ACTIVE",
                "message": (
                    "This account is not active. Contact an administrator "
                    "if you believe access should be restored."
                ),
            },
        )


if __name__ == "__main__":
    unittest.main()
