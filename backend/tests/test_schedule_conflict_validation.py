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
from app.repositories.schedule_conflict_repository import (
    ScheduleConflictError,
    ScheduleConflictRepositoryError,
    active_schedule_query,
    require_no_schedule_conflicts,
)
from app.security import create_access_token


class ScheduleConflictValidationTestCase(unittest.TestCase):
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
            minimum_credit=0,
            maximum_credit=30,
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
        code: str,
        section: str,
        schedule: list[dict[str, str]],
        semester: str = "Fall 2026",
    ) -> Course:
        return Course(
            course_id=f"course-{suffix}",
            code=code,
            title=f"Title for {code}",
            department="CSE",
            semester=semester,
            instructor="Dr. Schedule",
            credits=3,
            capacity=30,
            available_seats=30,
            is_mandatory=False,
            prerequisites=[],
            section=section,
            schedule=schedule,
        )

    @staticmethod
    def meeting(
        day: str,
        start_time: str,
        end_time: str,
    ) -> dict[str, str]:
        return {
            "day": day,
            "start_time": start_time,
            "end_time": end_time,
            "room": "CSE-201",
        }

    @staticmethod
    def authorization_header(user: User) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {create_access_token(user.id)}"
        }

    def add_registration(
        self,
        *,
        student: Student,
        course: Course,
        registration_status: str,
    ) -> Registration:
        registration = Registration(
            student=student,
            section=course,
            registration_status=registration_status,
        )
        self.db.add(registration)
        return registration

    def test_overlapping_selection_is_blocked_with_complete_details(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(suffix=suffix)
        existing = self.make_course(
            suffix=f"{suffix}-existing",
            code="CSE 301",
            section="A",
            schedule=[self.meeting("Sunday", "10:00", "11:30")],
        )
        candidate = self.make_course(
            suffix=f"{suffix}-candidate",
            code="CSE 305",
            section="B",
            schedule=[self.meeting("Sunday", "11:00", "12:15")],
        )
        self.add_registration(
            student=student,
            course=existing,
            registration_status=RegistrationStatus.DRAFT.value,
        )
        self.db.add(candidate)
        self.db.commit()

        response = self.client.post(
            "/api/selections",
            json={"course_id": candidate.course_id},
            headers=self.authorization_header(student.user),
        )

        self.assertEqual(response.status_code, 409)
        error = response.json()["error"]
        self.assertEqual(error["code"], "SCHEDULE_CONFLICT")
        self.assertEqual(error["details"]["conflict_count"], 1)
        self.assertTrue(error["details"]["has_conflicts"])
        conflict = error["details"]["conflicts"][0]
        self.assertEqual(conflict["day"], "Sunday")
        self.assertEqual(conflict["overlap_start_time"], "11:00")
        self.assertEqual(conflict["overlap_end_time"], "11:30")
        self.assertEqual(
            conflict["selected_course"],
            {
                "course_id": candidate.course_id,
                "code": "CSE 305",
                "title": "Title for CSE 305",
                "section": "B",
                "registration_status": "draft",
                "start_time": "11:00",
                "end_time": "12:15",
            },
        )
        self.assertEqual(
            conflict["conflicting_course"],
            {
                "course_id": existing.course_id,
                "code": "CSE 301",
                "title": "Title for CSE 301",
                "section": "A",
                "registration_status": "draft",
                "start_time": "10:00",
                "end_time": "11:30",
            },
        )
        self.assertIn("CSE 305, Section B", error["message"])
        self.assertIn("CSE 301, Section A", error["message"])
        self.assertIn("Sunday from 11:00 to 11:30", error["message"])
        self.db.expire_all()
        self.assertEqual(self.db.query(Registration).count(), 1)

    def test_only_draft_pending_and_approved_statuses_block_selection(self):
        statuses = (
            (RegistrationStatus.DRAFT.value, True),
            (RegistrationStatus.PENDING.value, True),
            (RegistrationStatus.APPROVED.value, True),
            (RegistrationStatus.REJECTED.value, False),
            (RegistrationStatus.DROPPED.value, False),
        )

        for index, (registration_status, should_block) in enumerate(
            statuses
        ):
            with self.subTest(registration_status=registration_status):
                suffix = f"{uuid4().hex[:6]}-{index}"
                student = self.make_student(suffix=suffix)
                existing = self.make_course(
                    suffix=f"{suffix}-existing",
                    code=f"CSE {index}01",
                    section="A",
                    schedule=[
                        self.meeting("Monday", "09:00", "10:30")
                    ],
                )
                candidate = self.make_course(
                    suffix=f"{suffix}-candidate",
                    code=f"CSE {index}02",
                    section="B",
                    schedule=[
                        self.meeting("Monday", "10:00", "11:30")
                    ],
                )
                self.add_registration(
                    student=student,
                    course=existing,
                    registration_status=registration_status,
                )
                self.db.add(candidate)
                self.db.commit()

                response = self.client.post(
                    "/api/selections",
                    json={"course_id": candidate.course_id},
                    headers=self.authorization_header(student.user),
                )

                self.assertEqual(
                    response.status_code,
                    409 if should_block else 201,
                )

                if should_block:
                    conflict = response.json()["error"]["details"][
                        "conflicts"
                    ][0]
                    self.assertEqual(
                        conflict["conflicting_course"][
                            "registration_status"
                        ],
                        registration_status,
                    )

    def test_boundaries_different_days_and_other_semesters_are_allowed(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(suffix=suffix)
        existing = self.make_course(
            suffix=f"{suffix}-existing",
            code="CSE 401",
            section="A",
            schedule=[self.meeting("Sunday", "10:00", "11:30")],
        )
        adjacent = self.make_course(
            suffix=f"{suffix}-adjacent",
            code="CSE 402",
            section="B",
            schedule=[self.meeting("Sunday", "11:30", "13:00")],
        )
        different_day = self.make_course(
            suffix=f"{suffix}-day",
            code="CSE 403",
            section="C",
            schedule=[self.meeting("Monday", "10:30", "12:00")],
        )
        other_semester = self.make_course(
            suffix=f"{suffix}-semester",
            code="CSE 404",
            section="D",
            semester="Spring 2027",
            schedule=[self.meeting("Sunday", "10:30", "12:00")],
        )
        self.add_registration(
            student=student,
            course=existing,
            registration_status=RegistrationStatus.APPROVED.value,
        )
        self.db.add_all([adjacent, different_day, other_semester])
        self.db.commit()
        headers = self.authorization_header(student.user)

        responses = [
            self.client.post(
                "/api/selections",
                json={"course_id": course.course_id},
                headers=headers,
            )
            for course in (adjacent, different_day, other_semester)
        ]

        self.assertEqual(
            [response.status_code for response in responses],
            [201, 201, 201],
        )

    def test_day_and_semester_matching_is_case_and_space_insensitive(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(suffix=suffix)
        existing = self.make_course(
            suffix=f"{suffix}-existing",
            code="CSE 411",
            section="A",
            semester="Fall 2026",
            schedule=[self.meeting("  Sunday ", "10:00", "11:00")],
        )
        candidate = self.make_course(
            suffix=f"{suffix}-candidate",
            code="CSE 412",
            section="B",
            semester=" fall   2026 ",
            schedule=[self.meeting("sUnDaY", "10:30", "11:30")],
        )
        self.add_registration(
            student=student,
            course=existing,
            registration_status=RegistrationStatus.PENDING.value,
        )
        self.db.add(candidate)
        self.db.commit()

        response = self.client.post(
            "/api/selections",
            json={"course_id": candidate.course_id},
            headers=self.authorization_header(student.user),
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.json()["error"]["details"]["conflicts"][0][
                "day"
            ],
            "sUnDaY",
        )

    def test_unrelated_semester_schedule_data_does_not_block_selection(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(suffix=suffix)
        historical = self.make_course(
            suffix=f"{suffix}-historical",
            code="CSE 415",
            section="A",
            semester="Spring 2026",
            schedule=[self.meeting("Sunday", "invalid", "11:00")],
        )
        candidate = self.make_course(
            suffix=f"{suffix}-candidate",
            code="CSE 416",
            section="B",
            semester="Fall 2026",
            schedule=[self.meeting("Sunday", "10:30", "12:00")],
        )
        self.add_registration(
            student=student,
            course=historical,
            registration_status=RegistrationStatus.APPROVED.value,
        )
        self.db.add(candidate)
        self.db.commit()

        response = self.client.post(
            "/api/selections",
            json={"course_id": candidate.course_id},
            headers=self.authorization_header(student.user),
        )

        self.assertEqual(response.status_code, 201)

    def test_all_meetings_are_checked_and_exact_overlap_is_reported(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(suffix=suffix)
        existing = self.make_course(
            suffix=f"{suffix}-existing",
            code="CSE 421",
            section="A",
            schedule=[
                self.meeting("Sunday", "08:00", "09:00"),
                self.meeting("Tuesday", "14:00", "15:30"),
            ],
        )
        candidate = self.make_course(
            suffix=f"{suffix}-candidate",
            code="CSE 422",
            section="B",
            schedule=[
                self.meeting("Monday", "08:00", "09:00"),
                self.meeting("Tuesday", "15:00", "16:00"),
            ],
        )
        self.add_registration(
            student=student,
            course=existing,
            registration_status=RegistrationStatus.DRAFT.value,
        )
        self.db.add(candidate)
        self.db.commit()

        response = self.client.post(
            "/api/selections",
            json={"course_id": candidate.course_id},
            headers=self.authorization_header(student.user),
        )

        conflict = response.json()["error"]["details"]["conflicts"][0]
        self.assertEqual(response.status_code, 409)
        self.assertEqual(conflict["day"], "Tuesday")
        self.assertEqual(conflict["overlap_start_time"], "15:00")
        self.assertEqual(conflict["overlap_end_time"], "15:30")

    def test_read_reports_all_conflicts_and_final_guard_blocks(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(suffix=suffix)
        courses = [
            self.make_course(
                suffix=f"{suffix}-{index}",
                code=f"CSE 43{index}",
                section=chr(ord("A") + index),
                schedule=[self.meeting("Wednesday", "10:00", "12:00")],
            )
            for index in range(3)
        ]
        statuses = (
            RegistrationStatus.DRAFT.value,
            RegistrationStatus.PENDING.value,
            RegistrationStatus.APPROVED.value,
        )

        for course, registration_status in zip(courses, statuses):
            self.add_registration(
                student=student,
                course=course,
                registration_status=registration_status,
            )

        self.db.commit()
        headers = self.authorization_header(student.user)

        read_response = self.client.get(
            "/api/selections/schedule-conflict-validation",
            headers=headers,
        )
        blocking_response = self.client.post(
            "/api/selections/schedule-conflict-validation",
            headers=headers,
        )

        self.assertEqual(read_response.status_code, 200)
        validation = read_response.json()["data"]
        self.assertTrue(validation["has_conflicts"])
        self.assertEqual(validation["conflict_count"], 3)
        self.assertEqual(len(validation["conflicts"]), 3)
        self.assertEqual(blocking_response.status_code, 409)
        self.assertEqual(
            blocking_response.json()["error"]["code"],
            "SCHEDULE_CONFLICT",
        )
        self.assertEqual(
            blocking_response.json()["error"]["details"],
            validation,
        )

    def test_conflict_free_read_and_final_guard_succeed(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(suffix=suffix)
        first = self.make_course(
            suffix=f"{suffix}-first",
            code="CSE 441",
            section="A",
            schedule=[],
        )
        second = self.make_course(
            suffix=f"{suffix}-second",
            code="CSE 442",
            section="B",
            schedule=[self.meeting("Thursday", "10:00", "11:00")],
        )
        self.add_registration(
            student=student,
            course=first,
            registration_status=RegistrationStatus.DRAFT.value,
        )
        self.add_registration(
            student=student,
            course=second,
            registration_status=RegistrationStatus.APPROVED.value,
        )
        self.db.commit()
        headers = self.authorization_header(student.user)

        for method in (self.client.get, self.client.post):
            response = method(
                "/api/selections/schedule-conflict-validation",
                headers=headers,
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.json()["data"],
                {
                    "has_conflicts": False,
                    "conflict_count": 0,
                    "conflicts": [],
                    "message": "No schedule conflicts were found.",
                },
            )

    def test_conflicts_are_scoped_to_the_authenticated_student(self):
        suffix = uuid4().hex[:8]
        owner = self.make_student(suffix=f"{suffix}-owner")
        other = self.make_student(suffix=f"{suffix}-other")
        first = self.make_course(
            suffix=f"{suffix}-first",
            code="CSE 451",
            section="A",
            schedule=[self.meeting("Sunday", "10:00", "11:30")],
        )
        second = self.make_course(
            suffix=f"{suffix}-second",
            code="CSE 452",
            section="B",
            schedule=[self.meeting("Sunday", "10:30", "12:00")],
        )
        self.add_registration(
            student=other,
            course=first,
            registration_status=RegistrationStatus.DRAFT.value,
        )
        self.add_registration(
            student=other,
            course=second,
            registration_status=RegistrationStatus.APPROVED.value,
        )
        self.db.commit()

        response = self.client.get(
            "/api/selections/schedule-conflict-validation",
            headers=self.authorization_header(owner.user),
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["data"]["has_conflicts"])

    def test_invalid_stored_schedule_is_safe_and_selection_rolls_back(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(suffix=suffix)
        existing = self.make_course(
            suffix=f"{suffix}-existing",
            code="CSE 461",
            section="A",
            schedule=[self.meeting("Sunday", "10:00", "11:00")],
        )
        invalid = self.make_course(
            suffix=f"{suffix}-invalid",
            code="CSE 462",
            section="B",
            schedule=[self.meeting("Sunday", "10:30", "25:00")],
        )
        self.add_registration(
            student=student,
            course=existing,
            registration_status=RegistrationStatus.DRAFT.value,
        )
        self.db.add(invalid)
        self.db.commit()

        response = self.client.post(
            "/api/selections",
            json={"course_id": invalid.course_id},
            headers=self.authorization_header(student.user),
        )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json()["error"]["code"],
            "DATABASE_OPERATION_FAILED",
        )
        self.assertNotIn("25:00", response.text)
        self.db.expire_all()
        self.assertEqual(self.db.query(Registration).count(), 1)

    def test_routes_enforce_authentication_role_and_student_profile(self):
        suffix = uuid4().hex[:8]
        advisor = self.make_user(suffix=suffix, role="advisor")
        profileless = self.make_user(
            suffix=f"{suffix}-profileless",
            role="student",
        )
        self.db.add_all([advisor, profileless])
        self.db.commit()
        path = "/api/selections/schedule-conflict-validation"

        unauthenticated = self.client.get(path)
        forbidden = self.client.get(
            path,
            headers=self.authorization_header(advisor),
        )
        missing_profile = self.client.get(
            path,
            headers=self.authorization_header(profileless),
        )

        self.assertEqual(unauthenticated.status_code, 401)
        self.assertEqual(forbidden.status_code, 403)
        self.assertEqual(missing_profile.status_code, 404)
        self.assertEqual(
            missing_profile.json()["error"]["code"],
            "STUDENT_PROFILE_NOT_FOUND",
        )

    def test_repository_failures_return_a_safe_error(self):
        student = self.make_student(suffix=uuid4().hex[:8])
        self.db.commit()

        with patch(
            "app.api.routes.selections."
            "get_schedule_conflict_validation",
            side_effect=ScheduleConflictRepositoryError(
                "sensitive schedule data and database host"
            ),
        ):
            response = self.client.get(
                "/api/selections/schedule-conflict-validation",
                headers=self.authorization_header(student.user),
            )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json()["error"]["code"],
            "DATABASE_OPERATION_FAILED",
        )
        self.assertNotIn("database host", response.text.lower())
        self.assertNotIn("schedule data", response.text.lower())

    def test_reusable_final_guard_rejects_and_then_accepts_load(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(suffix=suffix)
        first = self.make_course(
            suffix=f"{suffix}-first",
            code="CSE 471",
            section="A",
            schedule=[self.meeting("Sunday", "10:00", "11:30")],
        )
        second = self.make_course(
            suffix=f"{suffix}-second",
            code="CSE 472",
            section="B",
            schedule=[self.meeting("Sunday", "11:00", "12:30")],
        )
        second_registration = self.add_registration(
            student=student,
            course=second,
            registration_status=RegistrationStatus.PENDING.value,
        )
        self.add_registration(
            student=student,
            course=first,
            registration_status=RegistrationStatus.DRAFT.value,
        )
        self.db.commit()

        with self.assertRaises(ScheduleConflictError) as context:
            require_no_schedule_conflicts(
                self.db,
                student_id=student.id,
            )

        self.assertEqual(context.exception.validation.conflict_count, 1)

        second_registration.registration_status = (
            RegistrationStatus.DROPPED.value
        )
        self.db.commit()
        validation = require_no_schedule_conflicts(
            self.db,
            student_id=student.id,
        )

        self.assertFalse(validation.has_conflicts)

    def test_openapi_documents_conflict_read_and_blocking_validation(self):
        operations = coursepilot_app.openapi()["paths"][
            "/api/selections/schedule-conflict-validation"
        ]

        for method in ("get", "post"):
            response_schema = operations[method]["responses"]["200"][
                "content"
            ]["application/json"]["schema"]
            self.assertTrue(
                response_schema["$ref"].endswith(
                    "/ScheduleConflictValidationResponse"
                )
            )

        error_schema = operations["post"]["responses"]["409"][
            "content"
        ]["application/json"]["schema"]
        self.assertTrue(error_schema["$ref"].endswith("/ErrorResponse"))

    def test_active_schedule_query_compiles_for_postgresql(self):
        with Session() as db:
            statement = active_schedule_query(
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
        self.assertIn("registrations.registration_status IN", sql)
        self.assertIn("'draft'", sql)
        self.assertIn("'pending'", sql)
        self.assertIn("'approved'", sql)


if __name__ == "__main__":
    unittest.main()
