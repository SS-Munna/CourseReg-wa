import unittest
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.errors import api_http_exception_handler
from app.api.routes.auth import router
from app.database import get_db
from app.security import create_access_token


class AuthMeRouteTestCase(unittest.TestCase):
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

    def test_missing_bearer_token_returns_401(self):
        response = self.client.get("/api/auth/me")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.headers.get("www-authenticate"),
            "Bearer",
        )
        self.assertEqual(
            response.json()["error"]["code"],
            "AUTHENTICATION_REQUIRED",
        )

    def test_invalid_tokens_return_401(self):
        user_id = uuid4()
        expired_token = create_access_token(
            user_id,
            expires_delta=timedelta(seconds=-1),
        )

        token_parts = create_access_token(user_id).split(".")
        signature = token_parts[2]
        replacement = "A" if signature[0] != "A" else "B"
        token_parts[2] = replacement + signature[1:]
        tampered_token = ".".join(token_parts)

        invalid_tokens = [
            "not-a-valid-jwt",
            "demo-token-7",
            expired_token,
            tampered_token,
        ]

        for token in invalid_tokens:
            with self.subTest(token_type=token[:12]):
                response = self.client.get(
                    "/api/auth/me",
                    headers={
                        "Authorization": f"Bearer {token}"
                    },
                )

                self.assertEqual(response.status_code, 401)

    def test_wrong_authentication_scheme_returns_401(self):
        response = self.client.get(
            "/api/auth/me",
            headers={"Authorization": "Basic credentials"},
        )

        self.assertEqual(response.status_code, 401)

    @patch("app.authorization.find_user_by_id")
    def test_valid_token_returns_current_user(
        self,
        mock_find_user_by_id,
    ):
        user_id = uuid4()
        mock_find_user_by_id.return_value = SimpleNamespace(
            id=user_id,
            full_name="JWT Test User",
            email="jwt@example.com",
            role="student",
        )

        token = create_access_token(user_id)
        response = self.client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "success": True,
                "data": {
                    "id": str(user_id),
                    "name": "JWT Test User",
                    "email": "jwt@example.com",
                    "role": "student",
                },
            },
        )
        self.assertEqual(
            mock_find_user_by_id.call_args.args[1],
            user_id,
        )


if __name__ == "__main__":
    unittest.main()
