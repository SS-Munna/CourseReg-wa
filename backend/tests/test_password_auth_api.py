import hashlib
from pathlib import Path
import tempfile
import unittest
from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.errors import api_http_exception_handler
from app.api.routes.auth import router
from app.database import Base, get_db
from app.models import User
from app.security import decode_access_token, hash_password, verify_password


class PasswordAuthApiTestCase(unittest.TestCase):
    password = "SecurePass123!"

    @classmethod
    def setUpClass(cls):
        cls.temporary_directory = tempfile.TemporaryDirectory()
        database_path = Path(cls.temporary_directory.name) / "password-auth.sqlite"
        cls.engine = create_engine(
            f"sqlite:///{database_path}",
            connect_args={"check_same_thread": False},
        )
        cls.session_factory = sessionmaker(bind=cls.engine)
        cls.app = FastAPI()
        cls.app.add_exception_handler(
            StarletteHTTPException,
            api_http_exception_handler,
        )
        cls.app.include_router(router)

        def override_get_db():
            with cls.session_factory() as db:
                yield db

        cls.app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(cls.app)

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

    def add_user(self, password_hash, *, status="active", role="student"):
        with self.session_factory() as db:
            user = User(
                full_name="Existing User",
                email=f"{status}@example.com",
                password_hash=password_hash,
                account_status=status,
                role=role,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return user.id, user.email

    def stored_hash(self, user_id):
        # A new session verifies persistence beyond the request's session.
        with self.session_factory() as db:
            return db.get(User, user_id).password_hash

    def login(self, email, password=None):
        return self.client.post(
            "/api/auth/login",
            json={
                "email": email,
                "password": self.password if password is None else password,
            },
        )

    def assert_auth_response(self, response, user_id, role):
        data = response.json()["data"]
        self.assertTrue(response.json()["success"])
        self.assertEqual(data["user"]["id"], str(user_id))
        self.assertEqual(data["user"]["role"], role)
        self.assertEqual(decode_access_token(data["token"])["sub"], str(user_id))
        self.assertNotIn("password", response.text)
        self.assertNotIn("$argon2id$", response.text)
        self.assertNotIn(self.password, response.text)

    def assert_invalid_credentials(self, response):
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

    def test_registration_stores_argon2id_without_exposing_password_material(self):
        response = self.client.post(
            "/api/auth/register",
            json={
                "name": "New Student",
                "email": "newstudent@example.com",
                "password": self.password,
            },
        )

        self.assertEqual(response.status_code, 201)
        user_id = UUID(response.json()["data"]["user"]["id"])
        password_hash = self.stored_hash(user_id)
        self.assertTrue(password_hash.startswith("$argon2id$"))
        self.assertTrue(verify_password(self.password, password_hash))
        self.assertNotIn(password_hash, response.text)
        self.assert_auth_response(response, user_id, "student")

    def test_active_legacy_login_persists_upgrade_and_preserves_identity_and_role(self):
        legacy_hash = hashlib.sha256(self.password.encode("utf-8")).hexdigest()
        user_id, email = self.add_user(legacy_hash, role="advisor")

        response = self.login(email)

        self.assertEqual(response.status_code, 200)
        self.assert_auth_response(response, user_id, "advisor")
        password_hash = self.stored_hash(user_id)
        self.assertNotEqual(password_hash, legacy_hash)
        self.assertTrue(password_hash.startswith("$argon2id$"))
        self.assertTrue(verify_password(self.password, password_hash))
        self.assertNotIn(legacy_hash, response.text)

    def test_wrong_password_does_not_upgrade_legacy_hash(self):
        legacy_hash = hashlib.sha256(self.password.encode("utf-8")).hexdigest()
        user_id, email = self.add_user(legacy_hash)

        response = self.login(email, "WrongPassword123!")

        self.assert_invalid_credentials(response)
        self.assertEqual(self.stored_hash(user_id), legacy_hash)

    def test_inactive_legacy_accounts_remain_blocked_without_hash_changes(self):
        legacy_hash = hashlib.sha256(self.password.encode("utf-8")).hexdigest()
        for status in ("pending", "suspended", "rejected"):
            with self.subTest(status=status):
                user_id, email = self.add_user(legacy_hash, status=status)

                response = self.login(email)

                self.assertEqual(response.status_code, 403)
                self.assertFalse(response.json()["success"])
                self.assertEqual(
                    response.json()["error"]["code"], "ACCOUNT_NOT_ACTIVE"
                )
                self.assertNotIn("token", response.json())
                self.assertNotIn(legacy_hash, response.text)
                self.assertEqual(self.stored_hash(user_id), legacy_hash)

    def test_modern_login_succeeds_without_replacing_current_hash(self):
        password_hash = hash_password(self.password)
        user_id, email = self.add_user(password_hash)

        response = self.login(email)

        self.assertEqual(response.status_code, 200)
        self.assert_auth_response(response, user_id, "student")
        self.assertEqual(self.stored_hash(user_id), password_hash)

    def test_malformed_stored_hash_returns_invalid_credentials(self):
        for password_hash in ("not-a-password-hash", "$argon2id$broken"):
            with self.subTest(password_hash=password_hash):
                user_id, email = self.add_user(password_hash)

                response = self.login(email)

                self.assert_invalid_credentials(response)
                self.assertEqual(self.stored_hash(user_id), password_hash)
                with self.session_factory() as db:
                    db.delete(db.get(User, user_id))
                    db.commit()

    def test_unknown_user_returns_invalid_credentials(self):
        self.assert_invalid_credentials(self.login("unknown@example.com"))


if __name__ == "__main__":
    unittest.main()
