import unittest
from unittest.mock import patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.errors import (
    api_http_exception_handler,
    api_unhandled_exception_handler,
    api_validation_exception_handler,
)
from app.api.routes.selections import router as selections_router
from app.database import Base, get_db
from app.database_errors import database_integrity_error_handler
from app.main import app as coursepilot_app
from app.models import (
    Advisor,
    Course,
    Department,
    Program,
    Registration,
    RegistrationStatus,
    Student,
    User,
)
from app.repositories.selection_repository import (
    SelectionRepositoryError,
    draft_selection_query,
)
from app.security import create_access_token


class SelectedCourseManagementTestCase(unittest.TestCase):
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
        cls.app.include_router(selections_router)

        def override_get_db():
            db = cls.session_factory()
            try:
                yield db
            finally:
                db.close()

        cls.app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(
            cls.app,
            raise_server_exceptions=False,
        )

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

    @staticmethod
    def make_user(*, suffix: str, role: str) -> User:
        return User(
            email=f"{role}-{suffix}@example.com",
            password_hash="test-password-hash",
            full_name=f"{role.title()} {suffix}",
            role=role,
        )

    def make_student(self, *, suffix: str) -> Student:
        department = Department(
            department_code=f"D-{suffix}",
            department_name=f"Department {suffix}",
        )
        program = Program(
            department=department,
            program_code=f"P-{suffix}",
            program_name=f"Program {suffix}",
            minimum_credit=9,
            maximum_credit=18,
        )
        advisor = Advisor(
            user=self.make_user(suffix=suffix, role="advisor"),
            department=department,
            employee_number=f"ADV-{suffix}",
        )
        student = Student(
            user=self.make_user(suffix=suffix, role="student"),
            program=program,
            advisor=advisor,
            student_number=f"STU-{suffix}",
            current_trimester=3,
        )
        self.db.add(student)
        self.db.flush()
        return student

    @staticmethod
    def make_course(
        *,
        suffix: str,
        code: str = "CSE 301",
        prerequisites: list[str] | None = None,
    ) -> Course:
        return Course(
            course_id=f"course-{suffix}",
            code=code,
            title=f"Title for {code}",
            department="CSE",
            semester="Fall 2026",
            instructor="Dr. Selection",
            credits=3,
            capacity=2,
            available_seats=2,
            is_mandatory=True,
            prerequisites=prerequisites or [],
            section="A",
            schedule=[
                {
                    "day": "Sunday",
                    "start_time": "10:00",
                    "end_time": "11:30",
                    "room": "CSE-201",
                }
            ],
        )

    @staticmethod
    def authorization_header(user: User) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {create_access_token(user.id)}"
        }

    def test_student_can_add_list_and_remove_a_draft_selection(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(suffix=f"{suffix}-owner")
        enrolled_student = self.make_student(
            suffix=f"{suffix}-enrolled"
        )
        course = self.make_course(suffix=suffix)
        self.db.add(course)
        self.db.flush()
        approved = Registration(
            student=enrolled_student,
            section=course,
            registration_status=RegistrationStatus.APPROVED.value,
        )
        self.db.add(approved)
        self.db.commit()
        headers = self.authorization_header(student.user)

        created = self.client.post(
            "/api/selections",
            json={"course_id": f"  {course.course_id}  "},
            headers=headers,
        )

        self.assertEqual(created.status_code, 201)
        created_data = created.json()["data"]
        self.assertEqual(created_data["registration_status"], "draft")
        self.assertEqual(
            created_data["course"]["course_id"],
            course.course_id,
        )
        self.assertEqual(created_data["course"]["available_seats"], 1)
        self.assertEqual(
            created_data["course"]["schedule"][0]["room"],
            "CSE-201",
        )

        listed = self.client.get("/api/selections", headers=headers)

        self.assertEqual(listed.status_code, 200)
        self.assertEqual(
            listed.json()["data"],
            [created_data],
        )

        removed = self.client.delete(
            f"/api/selections/{course.course_id}",
            headers=headers,
        )

        self.assertEqual(removed.status_code, 200)
        self.assertEqual(
            removed.json()["data"],
            {
                "registration_id": created_data["registration_id"],
                "course_id": course.course_id,
            },
        )
        self.assertEqual(
            self.client.get(
                "/api/selections",
                headers=headers,
            ).json()["data"],
            [],
        )

        self.db.expire_all()
        remaining = self.db.query(Registration).all()
        self.assertEqual(remaining, [approved])

    def test_duplicate_selection_is_rejected_without_a_second_record(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(suffix=suffix)
        course = self.make_course(suffix=suffix)
        self.db.add(course)
        self.db.commit()
        headers = self.authorization_header(student.user)
        payload = {"course_id": course.course_id}

        first = self.client.post(
            "/api/selections",
            json=payload,
            headers=headers,
        )
        duplicate = self.client.post(
            "/api/selections",
            json=payload,
            headers=headers,
        )

        self.assertEqual(first.status_code, 201)
        self.assertEqual(duplicate.status_code, 409)
        self.assertEqual(
            duplicate.json()["error"]["code"],
            "DUPLICATE_SELECTION",
        )
        self.assertEqual(
            duplicate.json()["error"]["details"],
            {"registration_status": "draft"},
        )
        self.db.expire_all()
        self.assertEqual(self.db.query(Registration).count(), 1)

    def test_unmet_prerequisites_block_persistence_with_details(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(suffix=suffix)
        required = self.make_course(
            suffix=f"{suffix}-required",
            code="CSE 201",
        )
        target = self.make_course(
            suffix=f"{suffix}-target",
            code="CSE 301",
            prerequisites=["CSE 201"],
        )
        self.db.add_all([required, target])
        self.db.commit()

        response = self.client.post(
            "/api/selections",
            json={"course_id": target.course_id},
            headers=self.authorization_header(student.user),
        )

        self.assertEqual(response.status_code, 422)
        error = response.json()["error"]
        self.assertEqual(error["code"], "PREREQUISITES_NOT_MET")
        self.assertEqual(error["details"]["course_id"], target.course_id)
        self.assertEqual(
            error["details"]["missing_prerequisites"][0]["code"],
            "CSE 201",
        )
        self.db.expire_all()
        self.assertEqual(self.db.query(Registration).count(), 0)

    def test_only_the_owners_draft_selection_can_be_removed(self):
        suffix = uuid4().hex[:8]
        owner = self.make_student(suffix=f"{suffix}-owner")
        other = self.make_student(suffix=f"{suffix}-other")
        course = self.make_course(suffix=suffix)
        registration = Registration(
            student=owner,
            section=course,
            registration_status=RegistrationStatus.PENDING.value,
        )
        self.db.add(registration)
        self.db.commit()

        owner_add = self.client.post(
            "/api/selections",
            json={"course_id": course.course_id},
            headers=self.authorization_header(owner.user),
        )

        other_response = self.client.delete(
            f"/api/selections/{course.course_id}",
            headers=self.authorization_header(other.user),
        )
        owner_response = self.client.delete(
            f"/api/selections/{course.course_id}",
            headers=self.authorization_header(owner.user),
        )

        self.assertEqual(owner_add.status_code, 409)
        self.assertEqual(
            owner_add.json()["error"]["details"],
            {"registration_status": "pending"},
        )
        self.assertEqual(other_response.status_code, 404)
        self.assertEqual(
            other_response.json()["error"]["code"],
            "DRAFT_SELECTION_NOT_FOUND",
        )
        self.assertEqual(owner_response.status_code, 409)
        self.assertEqual(
            owner_response.json()["error"]["code"],
            "SELECTION_NOT_DRAFT",
        )
        self.assertEqual(
            owner_response.json()["error"]["details"],
            {"registration_status": "pending"},
        )
        self.db.expire_all()
        self.assertIsNotNone(
            self.db.get(Registration, registration.id)
        )

    def test_authentication_role_and_student_profile_are_enforced(self):
        advisor_user = self.make_user(
            suffix=uuid4().hex[:8],
            role="advisor",
        )
        profileless_student = self.make_user(
            suffix=uuid4().hex[:8],
            role="student",
        )
        self.db.add_all([advisor_user, profileless_student])
        self.db.commit()

        unauthenticated = self.client.get("/api/selections")
        forbidden = self.client.get(
            "/api/selections",
            headers=self.authorization_header(advisor_user),
        )
        missing_profile = self.client.get(
            "/api/selections",
            headers=self.authorization_header(profileless_student),
        )

        self.assertEqual(unauthenticated.status_code, 401)
        self.assertEqual(forbidden.status_code, 403)
        self.assertEqual(missing_profile.status_code, 404)
        self.assertEqual(
            missing_profile.json()["error"]["code"],
            "STUDENT_PROFILE_NOT_FOUND",
        )

    def test_missing_sections_and_invalid_payloads_use_shared_errors(self):
        student = self.make_student(suffix=uuid4().hex[:8])
        self.db.commit()
        headers = self.authorization_header(student.user)

        missing = self.client.post(
            "/api/selections",
            json={"course_id": "does-not-exist"},
            headers=headers,
        )
        invalid = self.client.post(
            "/api/selections",
            json={"course_id": "   "},
            headers=headers,
        )

        self.assertEqual(missing.status_code, 404)
        self.assertEqual(
            missing.json()["error"]["code"],
            "SECTION_NOT_FOUND",
        )
        self.assertEqual(invalid.status_code, 422)
        self.assertEqual(
            invalid.json()["error"]["code"],
            "REQUEST_VALIDATION_ERROR",
        )

    def test_repository_failures_do_not_expose_database_details(self):
        student = self.make_student(suffix=uuid4().hex[:8])
        self.db.commit()

        with patch(
            "app.api.routes.selections.list_draft_selections",
            side_effect=SelectionRepositoryError(
                "sensitive database host and stored values"
            ),
        ):
            response = self.client.get(
                "/api/selections",
                headers=self.authorization_header(student.user),
            )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json()["error"]["code"],
            "DATABASE_OPERATION_FAILED",
        )
        self.assertNotIn("database host", response.text.lower())
        self.assertNotIn("stored values", response.text.lower())

    def test_openapi_documents_all_selection_operations(self):
        paths = coursepilot_app.openapi()["paths"]
        collection = paths["/api/selections"]
        item = paths["/api/selections/{course_id}"]

        self.assertTrue(
            collection["get"]["responses"]["200"]["content"]
            ["application/json"]["schema"]["$ref"].endswith(
                "/DraftSelectionListResponse"
            )
        )
        self.assertTrue(
            collection["post"]["responses"]["201"]["content"]
            ["application/json"]["schema"]["$ref"].endswith(
                "/DraftSelectionResponse"
            )
        )
        self.assertTrue(
            item["delete"]["responses"]["200"]["content"]
            ["application/json"]["schema"]["$ref"].endswith(
                "/DraftSelectionRemovedResponse"
            )
        )

    def test_draft_selection_query_compiles_for_postgresql(self):
        with Session() as db:
            statement = draft_selection_query(
                db,
                student_id=uuid4(),
            ).statement

        sql = str(
            statement.compile(
                dialect=postgresql.dialect(),
                compile_kwargs={"literal_binds": True},
            )
        )

        self.assertIn("registrations JOIN courses", sql)
        self.assertIn("registrations.student_id", sql)
        self.assertIn("registrations.registration_status = 'draft'", sql)
        self.assertIn("approved_enrollment", sql)


if __name__ == "__main__":
    unittest.main()
