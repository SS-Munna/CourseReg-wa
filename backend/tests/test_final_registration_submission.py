from datetime import date
from pathlib import Path
import tempfile
import threading
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
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.errors import (
    api_http_exception_handler,
    api_unhandled_exception_handler,
    api_validation_exception_handler,
)
from app.api.routes.registrations import router as registrations_router
from app.database import Base, get_db
from app.database_errors import database_integrity_error_handler
from app.main import app as coursepilot_app
from app.models import (
    Advisor,
    CompletedCourse,
    CompletionStatus,
    Course,
    CoursePrerequisite,
    Department,
    Program,
    Registration,
    RegistrationStatus,
    Student,
    User,
)
from app.repositories.registration_submission_repository import (
    NoDraftSelectionsError,
    RegistrationSubmissionRepositoryError,
    locked_draft_registrations_query,
    locked_draft_sections_query,
    submit_final_registration,
)
from app.security import create_access_token


class FinalRegistrationSubmissionTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary_directory = tempfile.TemporaryDirectory()
        database_path = (
            Path(cls.temporary_directory.name) / "submission.sqlite"
        )
        cls.engine = create_engine(
            f"sqlite:///{database_path}",
            connect_args={
                "check_same_thread": False,
                "timeout": 10,
            },
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
        cls.app.include_router(registrations_router)

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
        cls.temporary_directory.cleanup()

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

    def make_student(
        self,
        *,
        suffix: str,
        minimum_credit: int = 6,
        maximum_credit: int = 9,
        program: Program | None = None,
        advisor: Advisor | None = None,
    ) -> Student:
        if program is None or advisor is None:
            department = Department(
                department_code=f"D-{suffix}",
                department_name=f"Department {suffix}",
            )
            program = Program(
                department=department,
                program_code=f"P-{suffix}",
                program_name=f"Program {suffix}",
                minimum_credit=minimum_credit,
                maximum_credit=maximum_credit,
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
        code: str | None = None,
        section: str = "A",
        semester: str = "Fall 2026",
        credits: int = 3,
        capacity: int = 10,
        available_seats: int | None = None,
        day: str = "Sunday",
        start_time: str = "09:00",
        end_time: str = "10:00",
        prerequisites: list[str] | None = None,
    ) -> Course:
        return Course(
            course_id=f"course-{suffix}",
            code=code or f"CSE {suffix}",
            title=f"Course {suffix}",
            department="CSE",
            semester=semester,
            instructor="Dr. Submission",
            credits=credits,
            capacity=capacity,
            available_seats=(
                capacity
                if available_seats is None
                else available_seats
            ),
            is_mandatory=False,
            prerequisites=prerequisites or [],
            section=section,
            schedule=[
                {
                    "day": day,
                    "start_time": start_time,
                    "end_time": end_time,
                    "room": f"ROOM-{suffix}",
                }
            ],
        )

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
        registration_status: str = RegistrationStatus.DRAFT.value,
    ) -> Registration:
        registration = Registration(
            student=student,
            section=course,
            registration_status=registration_status,
        )
        self.db.add(registration)
        self.db.flush()
        return registration

    def add_valid_drafts(
        self,
        *,
        student: Student,
        suffix: str,
    ) -> list[Registration]:
        courses = [
            self.make_course(
                suffix=f"{suffix}-first",
                code=f"CSE {suffix}1",
                day="Sunday",
            ),
            self.make_course(
                suffix=f"{suffix}-second",
                code=f"CSE {suffix}2",
                day="Monday",
            ),
        ]
        self.db.add_all(courses)
        self.db.flush()
        return [
            self.add_registration(student=student, course=course)
            for course in courses
        ]

    def test_valid_submission_moves_every_owned_draft_to_pending(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(suffix=f"{suffix}-owner")
        other = self.make_student(suffix=f"{suffix}-other")
        drafts = self.add_valid_drafts(student=student, suffix=suffix)
        other_course = self.make_course(
            suffix=f"{suffix}-other",
            code=f"EEE {suffix}",
            day="Tuesday",
        )
        self.db.add(other_course)
        self.db.flush()
        other_draft = self.add_registration(
            student=other,
            course=other_course,
        )
        draft_ids = {str(registration.id) for registration in drafts}
        self.db.commit()

        response = self.client.post(
            "/api/registrations/submit",
            headers=self.authorization_header(student.user),
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["success"])
        submission = body["data"]
        self.assertEqual(submission["registration_status"], "pending")
        self.assertEqual(submission["submitted_count"], 2)
        self.assertEqual(
            submission["credit_validation"]["selected_credits"],
            6,
        )
        self.assertTrue(submission["credit_validation"]["is_valid"])
        self.assertFalse(
            submission["schedule_validation"]["has_conflicts"]
        )
        self.assertEqual(
            {
                item["registration_id"]
                for item in submission["registrations"]
            },
            draft_ids,
        )
        self.assertEqual(
            {
                item["submitted_at"]
                for item in submission["registrations"]
            },
            {submission["submitted_at"]},
        )
        self.assertTrue(
            all(
                item["registration_status"] == "pending"
                for item in submission["registrations"]
            )
        )

        self.db.expire_all()
        stored = {
            registration.id: registration
            for registration in self.db.query(Registration).all()
        }

        for draft in drafts:
            self.assertEqual(
                stored[draft.id].registration_status,
                RegistrationStatus.PENDING.value,
            )
            self.assertIsNotNone(stored[draft.id].submitted_at)

        self.assertEqual(
            stored[other_draft.id].registration_status,
            RegistrationStatus.DRAFT.value,
        )
        self.assertIsNone(stored[other_draft.id].submitted_at)
        self.assertEqual(
            self.db.query(Registration)
            .filter(
                Registration.registration_status
                == RegistrationStatus.APPROVED.value
            )
            .count(),
            0,
        )

    def test_submission_changes_only_current_drafts(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(
            suffix=suffix,
            minimum_credit=9,
            maximum_credit=9,
        )
        draft_course = self.make_course(
            suffix=f"{suffix}-draft",
            code=f"CSE {suffix}1",
            day="Sunday",
        )
        pending_course = self.make_course(
            suffix=f"{suffix}-pending",
            code=f"CSE {suffix}2",
            day="Monday",
        )
        approved_course = self.make_course(
            suffix=f"{suffix}-approved",
            code=f"CSE {suffix}3",
            day="Tuesday",
        )
        self.db.add_all(
            [draft_course, pending_course, approved_course]
        )
        self.db.flush()
        draft = self.add_registration(
            student=student,
            course=draft_course,
        )
        pending = self.add_registration(
            student=student,
            course=pending_course,
            registration_status=RegistrationStatus.PENDING.value,
        )
        approved = self.add_registration(
            student=student,
            course=approved_course,
            registration_status=RegistrationStatus.APPROVED.value,
        )
        draft_id = draft.id
        pending_id = pending.id
        approved_id = approved.id
        self.db.commit()

        response = self.client.post(
            "/api/registrations/submit",
            headers=self.authorization_header(student.user),
        )

        self.assertEqual(response.status_code, 200)
        submission = response.json()["data"]
        self.assertEqual(submission["submitted_count"], 1)
        self.assertEqual(
            submission["registrations"][0]["registration_id"],
            str(draft_id),
        )
        self.assertEqual(
            submission["credit_validation"]["selected_credits"],
            9,
        )
        self.db.expire_all()
        self.assertEqual(
            self.db.get(Registration, draft_id).registration_status,
            RegistrationStatus.PENDING.value,
        )
        self.assertEqual(
            self.db.get(Registration, pending_id).registration_status,
            RegistrationStatus.PENDING.value,
        )
        self.assertEqual(
            self.db.get(Registration, approved_id).registration_status,
            RegistrationStatus.APPROVED.value,
        )
        self.assertIsNone(
            self.db.get(Registration, pending_id).submitted_at
        )
        self.assertIsNone(
            self.db.get(Registration, approved_id).submitted_at
        )

    def test_second_submission_is_rejected_when_no_drafts_remain(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(suffix=suffix)
        self.add_valid_drafts(student=student, suffix=suffix)
        self.db.commit()
        headers = self.authorization_header(student.user)

        first = self.client.post(
            "/api/registrations/submit",
            headers=headers,
        )
        second = self.client.post(
            "/api/registrations/submit",
            headers=headers,
        )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 409)
        self.assertEqual(
            second.json()["error"]["code"],
            "NO_DRAFT_SELECTIONS",
        )

    def test_invalid_credit_load_is_clear_and_keeps_draft_state(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(
            suffix=suffix,
            minimum_credit=6,
            maximum_credit=9,
        )
        course = self.make_course(suffix=suffix, code=f"CSE {suffix}")
        self.db.add(course)
        self.db.flush()
        draft = self.add_registration(student=student, course=course)
        draft_id = draft.id
        self.db.commit()

        response = self.client.post(
            "/api/registrations/submit",
            headers=self.authorization_header(student.user),
        )

        self.assertEqual(response.status_code, 422)
        error = response.json()["error"]
        self.assertEqual(error["code"], "CREDIT_LOAD_BELOW_MINIMUM")
        self.assertEqual(error["details"]["selected_credits"], 3)
        self.assertEqual(error["details"]["minimum_credit"], 6)
        self.db.expire_all()
        stored = self.db.get(Registration, draft_id)
        self.assertEqual(stored.registration_status, "draft")
        self.assertIsNone(stored.submitted_at)

    def test_above_maximum_credit_load_keeps_every_draft(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(
            suffix=suffix,
            minimum_credit=3,
            maximum_credit=3,
        )
        drafts = self.add_valid_drafts(
            student=student,
            suffix=suffix,
        )
        draft_ids = [registration.id for registration in drafts]
        self.db.commit()

        response = self.client.post(
            "/api/registrations/submit",
            headers=self.authorization_header(student.user),
        )

        self.assertEqual(response.status_code, 422)
        error = response.json()["error"]
        self.assertEqual(error["code"], "CREDIT_LOAD_ABOVE_MAXIMUM")
        self.assertEqual(error["details"]["selected_credits"], 6)
        self.assertEqual(error["details"]["maximum_credit"], 3)
        self.db.expire_all()
        stored = [
            self.db.get(Registration, registration_id)
            for registration_id in draft_ids
        ]
        self.assertEqual(
            {registration.registration_status for registration in stored},
            {RegistrationStatus.DRAFT.value},
        )
        self.assertTrue(
            all(registration.submitted_at is None for registration in stored)
        )

    def test_prerequisites_are_revalidated_before_submission(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(
            suffix=suffix,
            minimum_credit=3,
            maximum_credit=9,
        )
        required = self.make_course(
            suffix=f"{suffix}-required",
            code=f"CSE {suffix}1",
        )
        selected = self.make_course(
            suffix=f"{suffix}-selected",
            code=f"CSE {suffix}2",
            day="Monday",
        )
        self.db.add_all([required, selected])
        self.db.flush()
        self.db.add(
            CoursePrerequisite(
                course=selected,
                prerequisite_course=required,
                minimum_grade="C",
            )
        )
        draft = self.add_registration(student=student, course=selected)
        draft_id = draft.id
        self.db.commit()

        response = self.client.post(
            "/api/registrations/submit",
            headers=self.authorization_header(student.user),
        )

        self.assertEqual(response.status_code, 422)
        error = response.json()["error"]
        self.assertEqual(error["code"], "PREREQUISITES_NOT_MET")
        self.assertEqual(
            error["details"]["missing_prerequisites"][0]["code"],
            required.code.upper(),
        )
        self.db.expire_all()
        self.assertEqual(
            self.db.get(Registration, draft_id).registration_status,
            "draft",
        )

    def test_schedule_conflict_is_clear_and_keeps_all_drafts(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(suffix=suffix)
        first = self.make_course(
            suffix=f"{suffix}-first",
            code=f"CSE {suffix}1",
            start_time="09:00",
            end_time="10:30",
        )
        second = self.make_course(
            suffix=f"{suffix}-second",
            code=f"CSE {suffix}2",
            start_time="10:00",
            end_time="11:00",
        )
        self.db.add_all([first, second])
        self.db.flush()
        drafts = [
            self.add_registration(student=student, course=first),
            self.add_registration(student=student, course=second),
        ]
        draft_ids = [registration.id for registration in drafts]
        self.db.commit()

        response = self.client.post(
            "/api/registrations/submit",
            headers=self.authorization_header(student.user),
        )

        self.assertEqual(response.status_code, 409)
        error = response.json()["error"]
        self.assertEqual(error["code"], "SCHEDULE_CONFLICT")
        conflict = error["details"]["conflicts"][0]
        self.assertEqual(conflict["overlap_start_time"], "10:00")
        self.assertEqual(conflict["overlap_end_time"], "10:30")
        self.db.expire_all()
        self.assertEqual(
            {
                self.db.get(Registration, registration_id)
                .registration_status
                for registration_id in draft_ids
            },
            {"draft"},
        )

    def test_live_enrollment_blocks_a_full_section(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(
            suffix=f"{suffix}-owner",
            minimum_credit=3,
            maximum_credit=9,
        )
        enrolled_student = self.make_student(
            suffix=f"{suffix}-enrolled",
        )
        course = self.make_course(
            suffix=suffix,
            code=f"CSE {suffix}",
            capacity=1,
            available_seats=1,
        )
        self.db.add(course)
        self.db.flush()
        draft = self.add_registration(student=student, course=course)
        self.add_registration(
            student=enrolled_student,
            course=course,
            registration_status=RegistrationStatus.APPROVED.value,
        )
        draft_id = draft.id
        self.db.commit()

        response = self.client.post(
            "/api/registrations/submit",
            headers=self.authorization_header(student.user),
        )

        self.assertEqual(response.status_code, 409)
        error = response.json()["error"]
        self.assertEqual(error["code"], "SECTION_FULL")
        section = error["details"]["sections"][0]
        self.assertEqual(section["capacity"], 1)
        self.assertEqual(section["approved_enrollment"], 1)
        self.assertEqual(section["available_seats"], 0)
        self.assertTrue(section["waitlist_available"])
        self.db.expire_all()
        self.assertEqual(
            self.db.get(Registration, draft_id).registration_status,
            "draft",
        )

    def test_previously_completed_course_is_blocked_by_normalized_code(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(
            suffix=suffix,
            minimum_credit=3,
            maximum_credit=9,
        )
        historical = self.make_course(
            suffix=f"{suffix}-history",
            code="CSE 201",
            semester="Spring 2025",
        )
        selected = self.make_course(
            suffix=f"{suffix}-selected",
            code="  cse   201  ",
            semester="Fall 2026",
            day="Monday",
        )
        self.db.add_all([historical, selected])
        self.db.flush()
        self.db.add(
            CompletedCourse(
                student=student,
                course=historical,
                grade="B+",
                completion_status=CompletionStatus.COMPLETED.value,
                completed_at=date(2025, 5, 20),
            )
        )
        draft = self.add_registration(student=student, course=selected)
        draft_id = draft.id
        self.db.commit()

        response = self.client.post(
            "/api/registrations/submit",
            headers=self.authorization_header(student.user),
        )

        self.assertEqual(response.status_code, 422)
        error = response.json()["error"]
        self.assertEqual(error["code"], "COURSE_ALREADY_COMPLETED")
        conflict = error["details"]["courses"][0]
        self.assertEqual(conflict["completed_code"], "CSE 201")
        self.assertEqual(conflict["grade"], "B+")
        self.assertEqual(conflict["completed_at"], "2025-05-20")
        self.db.expire_all()
        self.assertEqual(
            self.db.get(Registration, draft_id).registration_status,
            "draft",
        )

    def test_duplicate_course_sections_are_blocked_by_normalized_code(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(suffix=suffix)
        first = self.make_course(
            suffix=f"{suffix}-a",
            code="CSE 305",
            section="A",
            day="Sunday",
        )
        second = self.make_course(
            suffix=f"{suffix}-b",
            code=" cse   305 ",
            section="B",
            day="Monday",
        )
        self.db.add_all([first, second])
        self.db.flush()
        drafts = [
            self.add_registration(student=student, course=first),
            self.add_registration(student=student, course=second),
        ]
        draft_ids = [registration.id for registration in drafts]
        self.db.commit()

        response = self.client.post(
            "/api/registrations/submit",
            headers=self.authorization_header(student.user),
        )

        self.assertEqual(response.status_code, 409)
        error = response.json()["error"]
        self.assertEqual(
            error["code"],
            "DUPLICATE_COURSE_SELECTIONS",
        )
        duplicate = error["details"]["duplicates"][0]
        self.assertEqual(duplicate["code"], "CSE 305")
        self.assertEqual(
            {item["section"] for item in duplicate["selections"]},
            {"A", "B"},
        )
        self.db.expire_all()
        self.assertEqual(
            {
                self.db.get(Registration, registration_id)
                .registration_status
                for registration_id in draft_ids
            },
            {"draft"},
        )

    def test_only_students_with_profiles_can_submit(self):
        suffix = uuid4().hex[:8]
        advisor_user = self.make_user(suffix=suffix, role="advisor")
        student_without_profile = self.make_user(
            suffix=f"{suffix}-missing",
            role="student",
        )
        self.db.add_all([advisor_user, student_without_profile])
        self.db.commit()

        forbidden = self.client.post(
            "/api/registrations/submit",
            headers=self.authorization_header(advisor_user),
        )
        missing_profile = self.client.post(
            "/api/registrations/submit",
            headers=self.authorization_header(student_without_profile),
        )

        self.assertEqual(forbidden.status_code, 403)
        self.assertEqual(missing_profile.status_code, 404)
        self.assertEqual(
            missing_profile.json()["error"]["code"],
            "STUDENT_PROFILE_NOT_FOUND",
        )

    def test_repository_failure_returns_safe_error(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(suffix=suffix)
        self.add_valid_drafts(student=student, suffix=suffix)
        self.db.commit()

        with patch(
            "app.api.routes.registrations.submit_final_registration",
            side_effect=RegistrationSubmissionRepositoryError(
                "sensitive database details"
            ),
        ):
            response = self.client.post(
                "/api/registrations/submit",
                headers=self.authorization_header(student.user),
            )

        self.assertEqual(response.status_code, 500)
        body = response.json()
        self.assertEqual(
            body["error"]["code"],
            "DATABASE_OPERATION_FAILED",
        )
        self.assertNotIn("sensitive", response.text.lower())

    def test_write_failure_rolls_back_every_status_change(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(suffix=suffix)
        drafts = self.add_valid_drafts(student=student, suffix=suffix)
        draft_ids = [registration.id for registration in drafts]
        student_id = student.id
        self.db.commit()

        with patch.object(
            self.db,
            "flush",
            side_effect=RuntimeError("sensitive write failure"),
        ):
            with self.assertRaises(
                RegistrationSubmissionRepositoryError
            ):
                submit_final_registration(
                    self.db,
                    student_id=student_id,
                )

        self.db.expire_all()
        stored = [
            self.db.get(Registration, registration_id)
            for registration_id in draft_ids
        ]
        self.assertEqual(
            {registration.registration_status for registration in stored},
            {"draft"},
        )
        self.assertTrue(
            all(registration.submitted_at is None for registration in stored)
        )

    def test_concurrent_submission_transitions_each_draft_once(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(suffix=suffix)
        drafts = self.add_valid_drafts(student=student, suffix=suffix)
        draft_ids = [registration.id for registration in drafts]
        student_id = student.id
        self.db.commit()
        start = threading.Barrier(3)
        outcome_lock = threading.Lock()
        outcomes = []

        def submit():
            db = self.session_factory()
            try:
                start.wait(timeout=5)
                result = submit_final_registration(
                    db,
                    student_id=student_id,
                )
                outcome = ("submitted", result.submitted_count)
            except NoDraftSelectionsError:
                outcome = ("no_drafts", 0)
            except Exception as error:  # pragma: no cover - diagnostic
                outcome = (type(error).__name__, 0)
            finally:
                db.close()

            with outcome_lock:
                outcomes.append(outcome)

        threads = [threading.Thread(target=submit) for _ in range(2)]

        for thread in threads:
            thread.start()

        start.wait(timeout=5)

        for thread in threads:
            thread.join(timeout=10)
            self.assertFalse(thread.is_alive())

        self.assertEqual(
            sorted(outcome[0] for outcome in outcomes),
            ["no_drafts", "submitted"],
        )
        self.assertEqual(
            sum(outcome[1] for outcome in outcomes),
            2,
        )
        self.db.expire_all()
        stored = [
            self.db.get(Registration, registration_id)
            for registration_id in draft_ids
        ]
        self.assertEqual(
            {registration.registration_status for registration in stored},
            {"pending"},
        )

    def test_submission_lock_queries_compile_for_postgresql(self):
        student_id = uuid4()

        with Session() as db:
            section_statement = locked_draft_sections_query(
                db,
                student_id=student_id,
            ).statement
            registration_statement = locked_draft_registrations_query(
                db,
                student_id=student_id,
            ).statement

        section_sql = str(
            section_statement.compile(
                dialect=postgresql.dialect(),
                compile_kwargs={"literal_binds": True},
            )
        )
        registration_sql = str(
            registration_statement.compile(
                dialect=postgresql.dialect(),
                compile_kwargs={"literal_binds": True},
            )
        )

        self.assertIn("JOIN registrations", section_sql)
        self.assertIn("ORDER BY courses.id", section_sql)
        self.assertIn("FOR UPDATE OF courses", section_sql)
        self.assertIn("ORDER BY registrations.id", registration_sql)
        self.assertIn(
            "FOR UPDATE OF registrations",
            registration_sql,
        )

    def test_openapi_exposes_protected_submission_contract(self):
        operation = coursepilot_app.openapi()["paths"][
            "/api/registrations/submit"
        ]["post"]

        self.assertIn("security", operation)
        self.assertIn("200", operation["responses"])
        self.assertIn("409", operation["responses"])
        self.assertIn("422", operation["responses"])
        response_schema = operation["responses"]["200"]["content"][
            "application/json"
        ]["schema"]
        self.assertEqual(
            response_schema["$ref"],
            (
                "#/components/schemas/"
                "FinalRegistrationSubmissionResponse"
            ),
        )


if __name__ == "__main__":
    unittest.main()
