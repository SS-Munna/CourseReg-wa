import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.authorization import (
    UserRole,
    ensure_owner_or_roles,
    require_roles,
)
from app.database import get_db
from app.models.user import User
from app.security import create_access_token


class AuthorizationTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = FastAPI()
        cls.app.dependency_overrides[get_db] = lambda: object()

        staff_roles = (
            UserRole.ADVISOR,
            UserRole.DEPARTMENT_ADMIN,
            UserRole.SYSTEM_ADMIN,
        )

        @cls.app.get("/staff-only")
        def staff_only(
            current_user: User = Depends(
                require_roles(*staff_roles)
            ),
        ):
            return {
                "id": current_user.id,
                "role": current_user.role,
            }

        cls.client = TestClient(cls.app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        cls.app.dependency_overrides.clear()

    def request_as_role(self, role: str):
        user = SimpleNamespace(
            id=7,
            name="RBAC Test User",
            email="rbac@example.com",
            role=role,
        )
        token = create_access_token(7)

        with patch(
            "app.authorization.find_user_by_id",
            return_value=user,
        ):
            return self.client.get(
                "/staff-only",
                headers={"Authorization": f"Bearer {token}"},
            )

    def test_missing_token_returns_401(self):
        response = self.client.get("/staff-only")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.headers.get("www-authenticate"),
            "Bearer",
        )

    def test_unknown_user_returns_401(self):
        token = create_access_token(7)

        with patch(
            "app.authorization.find_user_by_id",
            return_value=None,
        ):
            response = self.client.get(
                "/staff-only",
                headers={"Authorization": f"Bearer {token}"},
            )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json()["detail"],
            "The access token does not identify an existing user.",
        )

    def test_student_cannot_access_staff_route(self):
        response = self.request_as_role(UserRole.STUDENT.value)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()["detail"],
            "You do not have permission to access this resource.",
        )

    def test_allowed_staff_roles_can_access_route(self):
        allowed_roles = (
            UserRole.ADVISOR,
            UserRole.DEPARTMENT_ADMIN,
            UserRole.SYSTEM_ADMIN,
        )

        for role in allowed_roles:
            with self.subTest(role=role.value):
                response = self.request_as_role(role.value)

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["role"], role.value)

    def test_invalid_stored_role_returns_403(self):
        response = self.request_as_role("super-admin")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()["detail"],
            "The account does not have a valid role.",
        )

    def test_owner_can_access_owned_resource(self):
        user = SimpleNamespace(role=UserRole.STUDENT.value)

        result = ensure_owner_or_roles(
            user,
            is_owner=True,
        )

        self.assertIs(result, user)

    def test_override_roles_can_access_non_owned_resource(self):
        override_roles = (
            UserRole.DEPARTMENT_ADMIN,
            UserRole.SYSTEM_ADMIN,
        )

        for role in override_roles:
            with self.subTest(role=role.value):
                user = SimpleNamespace(role=role.value)

                result = ensure_owner_or_roles(
                    user,
                    is_owner=False,
                    allowed_roles=override_roles,
                )

                self.assertIs(result, user)

    def test_non_owner_without_override_role_is_forbidden(self):
        user = SimpleNamespace(role=UserRole.ADVISOR.value)

        with self.assertRaises(HTTPException) as context:
            ensure_owner_or_roles(
                user,
                is_owner=False,
                allowed_roles=(
                    UserRole.DEPARTMENT_ADMIN,
                    UserRole.SYSTEM_ADMIN,
                ),
            )

        self.assertEqual(context.exception.status_code, 403)

    def test_role_dependency_requires_an_allowed_role(self):
        with self.assertRaisesRegex(
            ValueError,
            "At least one allowed role is required.",
        ):
            require_roles()


if __name__ == "__main__":
    unittest.main()