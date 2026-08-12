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
from app.database import Base, get_db
from app.database_errors import database_integrity_error_handler
from app.models import Advisor, Department, Program, Student, User
from app.security import create_access_token


class AdminApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary_directory = tempfile.TemporaryDirectory()
        database_path = Path(cls.temporary_directory.name) / "admin.sqlite"
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

    @staticmethod
    def make_user(role: str, suffix: str, status: str = "active") -> User:
        return User(
            full_name=f"{role.title()} {suffix}",
            email=f"{role}-{suffix}@example.com",
            password_hash="test-password-hash",
            role=role,
            account_status=status,
        )

    @staticmethod
    def auth(user: User) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {create_access_token(user.id)}"
        }

    def add_user(self, role: str, suffix: str, status: str = "active") -> User:
        user = self.make_user(role, suffix, status)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def test_student_cannot_access_administration(self):
        student = self.add_user("student", uuid4().hex[:8])

        response = self.client.get(
            "/api/admin/overview",
            headers=self.auth(student),
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()["error"]["code"],
            "INSUFFICIENT_PERMISSIONS",
        )

    def test_department_admin_scope_hides_privileged_admin_accounts(self):
        suffix = uuid4().hex[:8]
        department_admin = self.add_user("department-admin", f"{suffix}-dept")
        student = self.add_user("student", f"{suffix}-student")
        advisor = self.add_user("advisor", f"{suffix}-advisor")
        self.add_user("system-admin", f"{suffix}-system")

        response = self.client.get(
            "/api/admin/users",
            headers=self.auth(department_admin),
        )

        self.assertEqual(response.status_code, 200)
        ids = {item["id"] for item in response.json()["data"]}
        self.assertEqual(ids, {str(student.id), str(advisor.id)})

    def test_system_admin_provisions_complete_advisor_profile(self):
        suffix = uuid4().hex[:8]
        system_admin = self.add_user("system-admin", f"{suffix}-system")
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
                "employee_number": f"ADV-{suffix}",
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["data"]["role"], "advisor")
        self.db.expire_all()
        advisor = (
            self.db.query(Advisor)
            .filter(Advisor.employee_number == f"ADV-{suffix}")
            .one()
        )
        self.assertEqual(advisor.user.account_status, "active")
        self.assertEqual(advisor.department_id, department.id)

    def test_department_admin_cannot_create_another_admin(self):
        suffix = uuid4().hex[:8]
        department_admin = self.add_user("department-admin", suffix)

        response = self.client.post(
            "/api/admin/staff",
            headers=self.auth(department_admin),
            json={
                "name": "Another Administrator",
                "email": f"admin-{suffix}@example.com",
                "password": "TemporaryPass123!",
                "role": "department-admin",
                "account_status": "active",
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()["error"]["code"],
            "ADMIN_ACTION_NOT_ALLOWED",
        )

    def test_system_admin_can_suspend_and_reactivate_non_admin_user(self):
        suffix = uuid4().hex[:8]
        system_admin = self.add_user("system-admin", f"{suffix}-system")
        student = self.add_user("student", f"{suffix}-student")

        suspended = self.client.patch(
            f"/api/admin/users/{student.id}/access",
            headers=self.auth(system_admin),
            json={"account_status": "suspended"},
        )
        active = self.client.patch(
            f"/api/admin/users/{student.id}/access",
            headers=self.auth(system_admin),
            json={"account_status": "active"},
        )

        self.assertEqual(suspended.status_code, 200)
        self.assertEqual(
            suspended.json()["data"]["account_status"],
            "suspended",
        )
        self.assertEqual(active.status_code, 200)
        self.assertEqual(
            active.json()["data"]["account_status"],
            "active",
        )

    def test_system_admin_creates_academic_structure_and_links_student(self):
        suffix = uuid4().hex[:8]
        system_admin = self.add_user("system-admin", f"{suffix}-system")
        student_user = self.add_user("student", f"{suffix}-student")

        department_response = self.client.post(
            "/api/admin/departments",
            headers=self.auth(system_admin),
            json={
                "code": f"CSE{suffix[:3]}",
                "name": "Computer Science",
            },
        )
        self.assertEqual(department_response.status_code, 201)
        department_id = department_response.json()["data"]["id"]

        program_response = self.client.post(
            "/api/admin/programs",
            headers=self.auth(system_admin),
            json={
                "department_id": department_id,
                "code": f"BSC{suffix[:3]}",
                "name": "BSc in Computer Science",
                "minimum_credit": 9,
                "maximum_credit": 18,
            },
        )
        self.assertEqual(program_response.status_code, 201)
        program_id = program_response.json()["data"]["id"]

        advisor_user = self.make_user(
            "advisor",
            f"{suffix}-advisor",
        )
        department = self.db.get(Department, UUID(department_id))
        advisor = Advisor(
            user=advisor_user,
            department=department,
            employee_number=f"ADV-{suffix}",
        )
        self.db.add(advisor)
        self.db.commit()
        self.db.refresh(advisor)

        profile_response = self.client.post(
            f"/api/admin/students/{student_user.id}/profile",
            headers=self.auth(system_admin),
            json={
                "program_id": program_id,
                "advisor_id": str(advisor.id),
                "student_number": f"STU-{suffix}",
                "current_trimester": 2,
            },
        )

        self.assertEqual(profile_response.status_code, 201)
        self.db.expire_all()
        profile = (
            self.db.query(Student)
            .filter(Student.user_id == student_user.id)
            .one()
        )
        self.assertEqual(profile.program_id, self.db.get(Program, UUID(program_id)).id)
        self.assertEqual(profile.advisor_id, advisor.id)
        self.assertEqual(profile.current_trimester, 2)

    def test_student_profile_rejects_cross_department_advisor(self):
        suffix = uuid4().hex[:8]
        system_admin = self.add_user("system-admin", f"{suffix}-system")
        student_user = self.add_user("student", f"{suffix}-student")

        first_department = Department(
            department_code=f"A-{suffix}",
            department_name="Department A",
        )
        second_department = Department(
            department_code=f"B-{suffix}",
            department_name="Department B",
        )
        program = Program(
            department=first_department,
            program_code=f"P-{suffix}",
            program_name="Program A",
            minimum_credit=9,
            maximum_credit=18,
        )
        advisor = Advisor(
            user=self.make_user("advisor", f"{suffix}-advisor"),
            department=second_department,
            employee_number=f"ADV-{suffix}",
        )
        self.db.add_all([program, advisor])
        self.db.commit()

        response = self.client.post(
            f"/api/admin/students/{student_user.id}/profile",
            headers=self.auth(system_admin),
            json={
                "program_id": str(program.id),
                "advisor_id": str(advisor.id),
                "student_number": f"STU-{suffix}",
                "current_trimester": 1,
            },
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.json()["error"]["code"],
            "ADVISOR_PROGRAM_DEPARTMENT_MISMATCH",
        )

    def test_admin_cannot_change_own_access_state(self):
        system_admin = self.add_user(
            "system-admin",
            uuid4().hex[:8],
        )

        response = self.client.patch(
            f"/api/admin/users/{system_admin.id}/access",
            headers=self.auth(system_admin),
            json={"account_status": "suspended"},
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()["error"]["code"],
            "SELF_ACCESS_CHANGE_NOT_ALLOWED",
        )


if __name__ == "__main__":
    unittest.main()
