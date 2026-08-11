import unittest
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.auth import router
from app.database import get_db
from app.security import decode_access_token


class AuthTokenRoutesTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = FastAPI()
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
        token = response_data["token"]

        self.assertNotEqual(token, f"demo-token-{user_id}")
        self.assertEqual(token.count("."), 2)

        payload = decode_access_token(token)
        self.assertEqual(payload["sub"], str(user_id))
        self.assertIn("iat", payload)
        self.assertIn("exp", payload)

        self.assertEqual(response_data["user"]["id"], str(user_id))
        self.assertEqual(response_data["user"]["role"], "student")

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


if __name__ == "__main__":
    unittest.main()
