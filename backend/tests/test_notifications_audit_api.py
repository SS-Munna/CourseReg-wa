from pathlib import Path
import tempfile
import unittest
from uuid import UUID, uuid4

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
from app.api.routes.audit_logs import router as audit_router
from app.api.routes.notifications import router as notification_router
from app.database import Base, get_db
from app.database_errors import database_integrity_error_handler
from app.models import AuditLog, Department, Notification, User
from app.security import create_access_token


class NotificationsAuditApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary_directory = tempfile.TemporaryDirectory()
        database_path = Path(cls.temporary_directory.name) / "activity.sqlite"
        cls.engine = create_engine(
            f"sqlite:///{database_path}",
            connect_args={"check_same_thread": False},
        )
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
        cls.app.include_router(notification_router)
        cls.app.include_router(audit_router)
        cls.app.include_router(admin_router)

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

    def add_user(self, role: str, suffix: str) -> User:
        user = User(
            full_name=f"{role.title()} {suffix}",
            email=f"{role}-{suffix}@example.com",
            password_hash="test-password-hash",
            role=role,
            account_status="active",
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    @staticmethod
    def auth(user: User) -> dict[str, str]:
        return {"Authorization": f"Bearer {create_access_token(user.id)}"}

    def test_user_lists_only_owned_notifications_and_unread_count(self):
        suffix = uuid4().hex[:8]
        student = self.add_user("student", suffix)
        other = self.add_user("student", f"{suffix}-other")
        self.db.add_all(
            [
                Notification(
                    user_id=student.id,
                    notification_type="registration_approved",
                    title="Approved",
                    message="Your registration was approved.",
                ),
                Notification(
                    user_id=student.id,
                    notification_type="course_drop",
                    title="Course dropped",
                    message="The course was dropped.",
                    is_read=True,
                ),
                Notification(
                    user_id=other.id,
                    notification_type="private",
                    title="Other account",
                    message="Do not expose this notification.",
                ),
            ]
        )
        self.db.commit()

        response = self.client.get(
            "/api/notifications?page=1&page_size=10",
            headers=self.auth(student),
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["unread_count"], 1)
        self.assertEqual(len(data["notifications"]), 2)
        self.assertNotIn(
            "Other account",
            {item["title"] for item in data["notifications"]},
        )

    def test_user_marks_owned_notification_read_but_not_another_users(self):
        suffix = uuid4().hex[:8]
        student = self.add_user("student", suffix)
        other = self.add_user("student", f"{suffix}-other")
        owned = Notification(
            user_id=student.id,
            notification_type="test",
            title="Owned",
            message="Owned notification",
        )
        foreign = Notification(
            user_id=other.id,
            notification_type="test",
            title="Foreign",
            message="Foreign notification",
        )
        self.db.add_all([owned, foreign])
        self.db.commit()
        self.db.refresh(owned)
        self.db.refresh(foreign)

        success = self.client.patch(
            f"/api/notifications/{owned.id}/read",
            headers=self.auth(student),
        )
        forbidden = self.client.patch(
            f"/api/notifications/{foreign.id}/read",
            headers=self.auth(student),
        )

        self.assertEqual(success.status_code, 200)
        self.assertTrue(success.json()["data"]["is_read"])
        self.assertEqual(forbidden.status_code, 404)

    def test_mark_all_read_updates_only_current_user(self):
        suffix = uuid4().hex[:8]
        student = self.add_user("student", suffix)
        other = self.add_user("student", f"{suffix}-other")
        self.db.add_all(
            [
                Notification(
                    user_id=student.id,
                    notification_type="one",
                    title="One",
                    message="First",
                ),
                Notification(
                    user_id=student.id,
                    notification_type="two",
                    title="Two",
                    message="Second",
                ),
                Notification(
                    user_id=other.id,
                    notification_type="other",
                    title="Other",
                    message="Other",
                ),
            ]
        )
        self.db.commit()

        response = self.client.post(
            "/api/notifications/read-all",
            headers=self.auth(student),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["updated_count"], 2)
        self.assertEqual(
            self.db.query(Notification)
            .filter(
                Notification.user_id == other.id,
                Notification.is_read.is_(False),
            )
            .count(),
            1,
        )

    def test_system_admin_reads_audit_log_but_department_admin_cannot(self):
        suffix = uuid4().hex[:8]
        system_admin = self.add_user("system-admin", suffix)
        department_admin = self.add_user("department-admin", f"{suffix}-dept")
        self.db.add(
            AuditLog(
                user_id=system_admin.id,
                action_type="account_access_updated",
                entity_type="user",
                entity_id=department_admin.id,
                action_details='{"account_status":"active"}',
            )
        )
        self.db.commit()

        allowed = self.client.get(
            "/api/admin/audit-logs",
            headers=self.auth(system_admin),
        )
        denied = self.client.get(
            "/api/admin/audit-logs",
            headers=self.auth(department_admin),
        )

        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(len(allowed.json()["data"]), 1)
        self.assertEqual(
            allowed.json()["data"][0]["actor_email"],
            system_admin.email,
        )
        self.assertEqual(denied.status_code, 403)

    def test_admin_provisioning_emits_audit_and_notification(self):
        suffix = uuid4().hex[:8]
        system_admin = self.add_user("system-admin", suffix)
        department = Department(
            department_code=f"CSE-{suffix}",
            department_name="Computer Science",
        )
        self.db.add(department)
        self.db.commit()
        self.db.refresh(department)

        response = self.client.post(
            "/api/admin/staff",
            headers=self.auth(system_admin),
            json={
                "name": "Dr. Nadia Rahman",
                "email": f"nadia-{suffix}@example.com",
                "password": "TemporaryPass123!",
                "role": "advisor",
                "account_status": "active",
                "department_id": str(department.id),
                "employee_number": f"FAC-{suffix}",
            },
        )

        self.assertEqual(response.status_code, 201)
        created_user_id = UUID(response.json()["data"]["id"])
        self.assertEqual(
            self.db.query(AuditLog)
            .filter(AuditLog.action_type == "staff_account_created")
            .count(),
            1,
        )
        self.assertEqual(
            self.db.query(Notification)
            .filter(Notification.user_id == created_user_id)
            .count(),
            1,
        )


if __name__ == "__main__":
    unittest.main()
