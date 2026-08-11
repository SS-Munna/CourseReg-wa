import unittest
from datetime import date
from unittest.mock import patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.errors import (
    api_http_exception_handler,
    api_unhandled_exception_handler,
    api_validation_exception_handler,
)
from app.api.routes.courses import router as courses_router
from app.database import Base, get_db
from app.main import app as coursepilot_app
from app.models import (
    Advisor,
    CompletedCourse,
    CompletionStatus,
    Course,
    CoursePrerequisite,
    Department,
    Program,
    Student,
    User,
)
from app.repositories.prerequisite_repository import (
    PrerequisiteRepositoryError,
    PrerequisitesNotMetError,
    completed_course_query,
    require_prerequisites_met,
)
from app.security import create_access_token


class PrerequisiteValidationTestCase(unittest.TestCase):
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
        cls.app.include_router(courses_router)

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
    def make_course(
        *,
        suffix: str,
        code: str,
        semester: str = "Fall 2026",
        section: str = "A",
        prerequisites: list[str] | None = None,
    ) -> Course:
        return Course(
            course_id=f"course-{suffix}",
            code=code,
            title=f"Title for {code}",
            department="CSE",
            semester=semester,
            instructor="Dr. Prerequisite",
            credits=3,
            capacity=30,
            available_seats=30,
            is_mandatory=True,
            prerequisites=prerequisites or [],
            section=section,
        )

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
    def authorization_header(user: User) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {create_access_token(user.id)}"
        }

    def test_missing_and_low_grade_requirements_are_identified(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(suffix=suffix)
        first_required = self.make_course(
            suffix=f"{suffix}-first",
            code="CSE 201",
        )
        second_required = self.make_course(
            suffix=f"{suffix}-second",
            code="MAT 201",
        )
        target = self.make_course(
            suffix=f"{suffix}-target",
            code="CSE 301",
        )
        self.db.add_all([first_required, second_required, target])
        self.db.flush()
        self.db.add_all(
            [
                CoursePrerequisite(
                    course=target,
                    prerequisite_course=first_required,
                    minimum_grade="B",
                ),
                CoursePrerequisite(
                    course=target,
                    prerequisite_course=second_required,
                    minimum_grade="C",
                ),
                CompletedCourse(
                    student=student,
                    course=first_required,
                    grade="C+",
                    completed_at=date(2026, 5, 1),
                ),
            ]
        )
        self.db.commit()

        response = self.client.get(
            f"/api/courses/{target.course_id}/prerequisite-validation",
            headers=self.authorization_header(student.user),
        )
        data = response.json()["data"]

        self.assertEqual(response.status_code, 200)
        self.assertFalse(data["eligible"])
        self.assertEqual(len(data["requirements"]), 2)
        missing_by_code = {
            item["code"]: item for item in data["missing_prerequisites"]
        }
        self.assertEqual(
            missing_by_code["CSE 201"]["reason"],
            "minimum_grade_not_met",
        )
        self.assertEqual(
            missing_by_code["CSE 201"]["earned_grade"],
            "C+",
        )
        self.assertEqual(
            missing_by_code["MAT 201"]["reason"],
            "not_completed",
        )
        self.assertEqual(
            missing_by_code["MAT 201"]["title"],
            "Title for MAT 201",
        )

        with self.assertRaises(PrerequisitesNotMetError) as context:
            require_prerequisites_met(
                self.db,
                student_id=student.id,
                course_id=target.course_id,
            )

        self.assertEqual(
            len(context.exception.validation.missing_prerequisites),
            2,
        )

    def test_completed_course_with_required_grade_is_eligible(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(suffix=suffix)
        current_required = self.make_course(
            suffix=f"{suffix}-current",
            code="CSE 101",
            semester="Fall 2026",
        )
        historical_required = self.make_course(
            suffix=f"{suffix}-historical",
            code="CSE 101",
            semester="Spring 2026",
        )
        target = self.make_course(
            suffix=f"{suffix}-target",
            code="CSE 201",
        )
        self.db.add_all(
            [current_required, historical_required, target]
        )
        self.db.flush()
        self.db.add_all(
            [
                CoursePrerequisite(
                    course=target,
                    prerequisite_course=current_required,
                    minimum_grade="B",
                ),
                CompletedCourse(
                    student=student,
                    course=current_required,
                    grade="A+",
                    completion_status=CompletionStatus.IN_PROGRESS.value,
                    completed_at=None,
                ),
                CompletedCourse(
                    student=student,
                    course=historical_required,
                    grade="B+",
                    completed_at=date(2026, 5, 1),
                ),
            ]
        )
        self.db.commit()

        response = self.client.get(
            f"/api/courses/{target.course_id}/prerequisite-validation",
            headers=self.authorization_header(student.user),
        )
        data = response.json()["data"]

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data["eligible"])
        self.assertEqual(data["missing_prerequisites"], [])
        self.assertTrue(data["requirements"][0]["satisfied"])
        self.assertEqual(data["requirements"][0]["earned_grade"], "B+")

        validation = require_prerequisites_met(
            self.db,
            student_id=student.id,
            course_id=target.course_id,
        )
        self.assertTrue(validation.eligible)

    def test_legacy_json_prerequisites_remain_supported(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(suffix=suffix)
        required = self.make_course(
            suffix=f"{suffix}-required",
            code="CSE 101",
        )
        target = self.make_course(
            suffix=f"{suffix}-target",
            code="CSE 201",
            prerequisites=["cse   101"],
        )
        self.db.add_all([required, target])
        self.db.flush()
        self.db.add(
            CompletedCourse(
                student=student,
                course=required,
                grade="D",
                completed_at=date(2026, 5, 1),
            )
        )
        self.db.commit()

        response = self.client.get(
            f"/api/courses/{target.course_id}/prerequisite-validation",
            headers=self.authorization_header(student.user),
        )
        data = response.json()["data"]

        self.assertTrue(data["eligible"])
        self.assertEqual(data["requirements"][0]["code"], "CSE 101")
        self.assertIsNone(data["requirements"][0]["minimum_grade"])
        self.assertEqual(data["requirements"][0]["earned_grade"], "D")

    def test_course_without_prerequisites_is_eligible(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(suffix=suffix)
        target = self.make_course(
            suffix=f"{suffix}-target",
            code="CSE 101",
        )
        self.db.add(target)
        self.db.commit()

        response = self.client.get(
            f"/api/courses/{target.course_id}/prerequisite-validation",
            headers=self.authorization_header(student.user),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["data"],
            {
                "course_id": target.course_id,
                "code": target.code,
                "eligible": True,
                "requirements": [],
                "missing_prerequisites": [],
            },
        )

    def test_endpoint_requires_student_identity_and_profile(self):
        target = self.make_course(
            suffix=uuid4().hex[:8],
            code="CSE 101",
        )
        advisor = self.make_user(
            suffix=uuid4().hex[:8],
            role="advisor",
        )
        profileless_student = self.make_user(
            suffix=uuid4().hex[:8],
            role="student",
        )
        self.db.add_all([target, advisor, profileless_student])
        self.db.commit()

        unauthenticated = self.client.get(
            f"/api/courses/{target.course_id}/prerequisite-validation"
        )
        forbidden = self.client.get(
            f"/api/courses/{target.course_id}/prerequisite-validation",
            headers=self.authorization_header(advisor),
        )
        missing_profile = self.client.get(
            f"/api/courses/{target.course_id}/prerequisite-validation",
            headers=self.authorization_header(profileless_student),
        )

        self.assertEqual(unauthenticated.status_code, 401)
        self.assertEqual(forbidden.status_code, 403)
        self.assertEqual(
            missing_profile.json()["error"]["code"],
            "STUDENT_PROFILE_NOT_FOUND",
        )

    def test_missing_section_and_database_failures_are_safe(self):
        student = self.make_student(suffix=uuid4().hex[:8])
        self.db.commit()
        headers = self.authorization_header(student.user)

        missing = self.client.get(
            "/api/courses/does-not-exist/prerequisite-validation",
            headers=headers,
        )
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(
            missing.json()["error"]["code"],
            "SECTION_NOT_FOUND",
        )

        with patch(
            "app.api.routes.courses.get_prerequisite_validation",
            side_effect=PrerequisiteRepositoryError(
                "sensitive database host and stored values"
            ),
        ):
            failed = self.client.get(
                "/api/courses/section-id/prerequisite-validation",
                headers=headers,
            )

        self.assertEqual(failed.status_code, 500)
        self.assertEqual(
            failed.json()["error"]["code"],
            "DATABASE_OPERATION_FAILED",
        )
        self.assertNotIn("database host", failed.text.lower())
        self.assertNotIn("stored values", failed.text.lower())

    def test_openapi_documents_prerequisite_contract(self):
        responses = coursepilot_app.openapi()["paths"][
            "/api/courses/{course_id}/prerequisite-validation"
        ]["get"]["responses"]

        success_schema = responses["200"]["content"][
            "application/json"
        ]["schema"]
        forbidden_schema = responses["403"]["content"][
            "application/json"
        ]["schema"]

        self.assertTrue(
            success_schema["$ref"].endswith(
                "/PrerequisiteValidationResponse"
            )
        )
        self.assertTrue(
            forbidden_schema["$ref"].endswith("/ErrorResponse")
        )

    def test_completed_course_query_compiles_for_postgresql(self):
        with Session() as db:
            statement = completed_course_query(
                db,
                student_id=uuid4(),
                course_codes=["CSE 101", "MAT 101"],
            ).statement

        sql = str(
            statement.compile(
                dialect=postgresql.dialect(),
                compile_kwargs={"literal_binds": True},
            )
        )

        self.assertIn("completed_courses JOIN courses", sql)
        self.assertIn("completed_courses.student_id", sql)
        self.assertIn("upper(trim(courses.code)) IN", sql)


if __name__ == "__main__":
    unittest.main()
