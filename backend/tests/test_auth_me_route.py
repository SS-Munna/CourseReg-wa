import unittest
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.auth import router
from app.database import get_db
from app.security import create_access_token


class AuthMeRouteTestCase(unittest.TestCase):
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

    def test_missing_bearer_token_returns_401(self):
        response = self.client.get("/api/auth/me")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.headers.get("www-authenticate"),
            "Bearer",
        )

    def test_invalid_tokens_return_401(self):
        expired_token = create_access_token(
            7,
            expires_delta=timedelta(seconds=-1),
        )

        token_parts = create_access_token(7).split(".")
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
        mock_find_user_by_id.return_value = SimpleNamespace(
            id=7,
            name="JWT Test User",
            email="jwt@example.com",
            role="student",
        )

        token = create_access_token(7)
        response = self.client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "id": 7,
                "name": "JWT Test User",
                "email": "jwt@example.com",
                "role": "student",
            },
        )
        self.assertEqual(
            mock_find_user_by_id.call_args.args[1],
            7,
        )


if __name__ == "__main__":
    unittest.main()