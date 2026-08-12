from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, inspect
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
from app.models import (
    Advisor,
    AuditLog,
    Course,
    Department,
    Notification,
    Program,
    Registration,
    RegistrationPeriod,
    RegistrationStatus,
    Semester,
    Student,
    User,
    WaitlistEntry,
    WaitlistStatus,
)
from app.repositories.course_drop_repository import (
    CourseDropRepositoryError,
    locked_drop_section_query,
    locked_owned_registration_query,
)
from app.repositories.registration_status_repository import (
    RegistrationStatusRepositoryError,
)
from app.repositories.waitlist_promotion_repository import (
    WaitlistPromotionRepositoryError,
)
from app.security import create_access_token


class RegistrationStatusCourseDropTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary_directory = tempfile.TemporaryDirectory()
        database_path = (
            Path(cls.temporary_directory.name) / "registration-status.sqlite"
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

    def make_context(self, *, suffix: str) -> tuple[Program, Advisor]:
        department = Department(
            department_code=f"D-{suffix}",
            department_name=f"Department {suffix}",
        )
        program = Program(
            department=department,
            program_code=f"P-{suffix}",
            program_name=f"Program {suffix}",
            minimum_credit=0,
            maximum_credit=18,
        )
        advisor = Advisor(
            user=self.make_user(suffix=suffix, role="advisor"),
            department=department,
            employee_number=f"ADV-{suffix}",
        )
        self.db.add_all([program, advisor])
        self.db.flush()
        return program, advisor

    def make_student(
        self,
        *,
        suffix: str,
        program: Program,
        advisor: Advisor,
    ) -> Student:
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
        capacity: int = 1,
        semester: str = "Fall 2026",
    ) -> Course:
        return Course(
            course_id=f"drop-{suffix}",
            code=f"CSE {suffix}",
            title=f"Drop Course {suffix}",
            department="CSE",
            semester=semester,
            instructor="Dr. Drop",
            credits=3,
            capacity=capacity,
            available_seats=0,
            is_mandatory=False,
            prerequisites=[],
            section="A",
            schedule=[
                {
                    "day": "Sunday",
                    "start_time": "09:00",
                    "end_time": "10:00",
                    "room": f"ROOM-{suffix}",
                }
            ],
        )

    def add_period(
        self,
        *,
        drop_deadline: date,
        semester_name: str = "Fall",
        academic_year: int = 2026,
        opening_time: datetime | None = None,
        closing_time: datetime | None = None,
    ) -> RegistrationPeriod:
        now = datetime.now(timezone.utc)
        semester = Semester(
            semester_name=semester_name,
            academic_year=academic_year,
            start_date=date(academic_year, 8, 1),
            end_date=date(academic_year, 12, 20),
            status="active",
        )
        period = RegistrationPeriod(
            semester=semester,
            opening_time=opening_time or now - timedelta(days=30),
            closing_time=closing_time or now - timedelta(days=1),
            drop_deadline=drop_deadline,
            minimum_credit=0,
            maximum_credit=18,
            status="closed",
        )
        self.db.add(period)
        self.db.flush()
        return period

    def add_registration(
        self,
        *,
        student: Student,
        course: Course,
        registration_status: str = RegistrationStatus.APPROVED.value,
        advisor_comment: str | None = None,
    ) -> Registration:
        now = datetime.now(timezone.utc)
        registration = Registration(
            student=student,
            section=course,
            registration_status=registration_status,
            advisor_comment=advisor_comment,
            submitted_at=(
                now
                if registration_status != RegistrationStatus.DRAFT.value
                else None
            ),
            reviewed_at=(
                now
                if registration_status
                in (
                    RegistrationStatus.APPROVED.value,
                    RegistrationStatus.REJECTED.value,
                )
                else None
            ),
        )
        self.db.add(registration)
        self.db.flush()
        return registration

    @staticmethod
    def authorization_header(user: User) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {create_access_token(user.id)}"
        }

    def test_registration_period_table_matches_drop_deadline_design(self):
        inspector = inspect(self.engine)
        self.assertIn("registration_periods", inspector.get_table_names())
        foreign_keys = list(RegistrationPeriod.__table__.foreign_keys)
        self.assertEqual(len(foreign_keys), 1)
        self.assertEqual(
            foreign_keys[0].column.table.name,
            "semesters",
        )
        constraint_names = {
            item["name"]
            for item in inspector.get_check_constraints(
                "registration_periods"
            )
        }
        self.assertIn(
            "ck_registration_period_credit_range",
            constraint_names,
        )
        self.assertIn(
            "ck_registration_period_time_range",
            constraint_names,
        )

    def test_status_api_returns_history_rejection_reason_and_waitlist(self):
        suffix = uuid4().hex[:8]
        program, advisor = self.make_context(suffix=suffix)
        student = self.make_student(
            suffix=suffix,
            program=program,
            advisor=advisor,
        )
        statuses = [
            RegistrationStatus.DRAFT.value,
            RegistrationStatus.PENDING.value,
            RegistrationStatus.APPROVED.value,
            RegistrationStatus.REJECTED.value,
            RegistrationStatus.DROPPED.value,
        ]
        registrations = []

        for index, registration_status in enumerate(statuses):
            course = self.make_course(suffix=f"{suffix}-{index}")
            self.db.add(course)
            registrations.append(
                self.add_registration(
                    student=student,
                    course=course,
                    registration_status=registration_status,
                    advisor_comment=(
                        "Prerequisite evidence is missing."
                        if registration_status
                        == RegistrationStatus.REJECTED.value
                        else None
                    ),
                )
            )

        waitlist_course = self.make_course(suffix=f"{suffix}-waitlist")
        self.db.add(waitlist_course)
        self.db.flush()
        waitlist = WaitlistEntry(
            student=student,
            section=waitlist_course,
            waitlist_status=WaitlistStatus.ACTIVE.value,
            joined_at=datetime.now(timezone.utc),
        )
        self.db.add(waitlist)
        deadline = datetime.now(timezone.utc).date() + timedelta(days=10)
        self.add_period(drop_deadline=deadline)
        self.db.commit()

        response = self.client.get(
            "/api/registrations",
            headers=self.authorization_header(student.user),
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(
            {item["registration_status"] for item in data["registrations"]},
            set(statuses),
        )
        rejected = next(
            item
            for item in data["registrations"]
            if item["registration_status"] == "rejected"
        )
        approved = next(
            item
            for item in data["registrations"]
            if item["registration_status"] == "approved"
        )
        self.assertEqual(
            rejected["advisor_comment"],
            "Prerequisite evidence is missing.",
        )
        self.assertTrue(approved["drop_eligibility"]["eligible"])
        self.assertEqual(
            approved["drop_eligibility"]["drop_deadline"],
            deadline.isoformat(),
        )
        self.assertEqual(len(data["waitlist_entries"]), 1)
        self.assertEqual(
            data["waitlist_entries"][0]["waitlist_entry_id"],
            str(waitlist.id),
        )
        self.assertEqual(
            data["waitlist_entries"][0]["registration_status"],
            "waitlisted",
        )

    def test_status_filter_separates_registration_and_waitlist_states(self):
        suffix = uuid4().hex[:8]
        program, advisor = self.make_context(suffix=suffix)
        student = self.make_student(
            suffix=suffix,
            program=program,
            advisor=advisor,
        )
        approved_course = self.make_course(suffix=f"{suffix}-approved")
        waitlist_course = self.make_course(suffix=f"{suffix}-waitlist")
        self.db.add_all([approved_course, waitlist_course])
        self.add_registration(student=student, course=approved_course)
        self.db.add(
            WaitlistEntry(
                student=student,
                section=waitlist_course,
                waitlist_status=WaitlistStatus.ACTIVE.value,
            )
        )
        self.db.commit()
        headers = self.authorization_header(student.user)

        approved = self.client.get(
            "/api/registrations?status=approved",
            headers=headers,
        )
        waitlisted = self.client.get(
            "/api/registrations?status=waitlisted",
            headers=headers,
        )

        self.assertEqual(approved.status_code, 200)
        self.assertEqual(len(approved.json()["data"]["registrations"]), 1)
        self.assertEqual(approved.json()["data"]["waitlist_entries"], [])
        self.assertEqual(waitlisted.status_code, 200)
        self.assertEqual(waitlisted.json()["data"]["registrations"], [])
        self.assertEqual(
            len(waitlisted.json()["data"]["waitlist_entries"]),
            1,
        )

    def test_drop_releases_seat_and_creates_history_records(self):
        suffix = uuid4().hex[:8]
        program, advisor = self.make_context(suffix=suffix)
        student = self.make_student(
            suffix=suffix,
            program=program,
            advisor=advisor,
        )
        course = self.make_course(suffix=suffix)
        self.db.add(course)
        registration = self.add_registration(
            student=student,
            course=course,
        )
        deadline = datetime.now(timezone.utc).date() + timedelta(days=5)
        self.add_period(drop_deadline=deadline)
        registration_id = registration.id
        self.db.commit()

        response = self.client.post(
            f"/api/registrations/{registration_id}/drop",
            headers=self.authorization_header(student.user),
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["registration_status"], "dropped")
        self.assertEqual(data["drop_deadline"], deadline.isoformat())
        self.assertEqual(data["course"]["available_seats"], 1)
        self.assertEqual(
            data["waitlist_promotion"]["outcome"],
            "queue_empty",
        )
        self.db.expire_all()
        stored = self.db.get(Registration, registration_id)
        notification = self.db.get(
            Notification,
            UUID(data["notification_id"]),
        )
        audit_log = self.db.get(AuditLog, UUID(data["audit_log_id"]))
        self.assertEqual(stored.registration_status, "dropped")
        self.assertEqual(notification.notification_type, "course_drop")
        self.assertEqual(audit_log.action_type, "student_course_drop")
        details = json.loads(audit_log.action_details)
        self.assertEqual(details["previous_registration_status"], "approved")
        self.assertEqual(details["new_registration_status"], "dropped")

    def test_drop_and_waitlist_promotion_share_one_successful_commit(self):
        suffix = uuid4().hex[:8]
        program, advisor = self.make_context(suffix=suffix)
        enrolled = self.make_student(
            suffix=f"{suffix}-enrolled",
            program=program,
            advisor=advisor,
        )
        waiting = self.make_student(
            suffix=f"{suffix}-waiting",
            program=program,
            advisor=advisor,
        )
        course = self.make_course(suffix=suffix)
        self.db.add(course)
        registration = self.add_registration(
            student=enrolled,
            course=course,
        )
        waitlist = WaitlistEntry(
            student=waiting,
            section=course,
            waitlist_status=WaitlistStatus.ACTIVE.value,
            joined_at=datetime.now(timezone.utc),
        )
        self.db.add(waitlist)
        self.add_period(
            drop_deadline=datetime.now(timezone.utc).date()
            + timedelta(days=5)
        )
        registration_id = registration.id
        waitlist_id = waitlist.id
        self.db.commit()

        response = self.client.post(
            f"/api/registrations/{registration_id}/drop",
            headers=self.authorization_header(enrolled.user),
        )

        self.assertEqual(response.status_code, 200)
        promotion = response.json()["data"]["waitlist_promotion"]
        self.assertTrue(promotion["promoted"])
        self.assertEqual(promotion["outcome"], "promoted")
        self.assertEqual(promotion["waitlist_entry_id"], str(waitlist_id))
        self.assertEqual(
            response.json()["data"]["course"]["available_seats"],
            0,
        )
        self.db.expire_all()
        self.assertEqual(
            self.db.get(Registration, registration_id).registration_status,
            "dropped",
        )
        self.assertEqual(
            self.db.get(WaitlistEntry, waitlist_id).waitlist_status,
            "promoted",
        )
        promoted = self.db.get(
            Registration,
            UUID(promotion["registration_id"]),
        )
        self.assertEqual(promoted.registration_status, "approved")
        self.assertEqual(promoted.student_id, waiting.id)
        self.assertEqual(self.db.query(Notification).count(), 2)
        self.assertEqual(self.db.query(AuditLog).count(), 2)

    def test_drop_is_allowed_through_deadline_date_after_registration_close(self):
        suffix = uuid4().hex[:8]
        program, advisor = self.make_context(suffix=suffix)
        student = self.make_student(
            suffix=suffix,
            program=program,
            advisor=advisor,
        )
        course = self.make_course(suffix=suffix)
        self.db.add(course)
        registration = self.add_registration(student=student, course=course)
        today = datetime.now(timezone.utc).date()
        self.add_period(drop_deadline=today)
        registration_id = registration.id
        self.db.commit()

        response = self.client.post(
            f"/api/registrations/{registration_id}/drop",
            headers=self.authorization_header(student.user),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["data"]["drop_deadline"],
            today.isoformat(),
        )

    def test_passed_deadline_blocks_drop_without_side_effects(self):
        suffix = uuid4().hex[:8]
        program, advisor = self.make_context(suffix=suffix)
        student = self.make_student(
            suffix=suffix,
            program=program,
            advisor=advisor,
        )
        course = self.make_course(suffix=suffix)
        self.db.add(course)
        registration = self.add_registration(student=student, course=course)
        deadline = datetime.now(timezone.utc).date() - timedelta(days=1)
        self.add_period(drop_deadline=deadline)
        registration_id = registration.id
        self.db.commit()

        response = self.client.post(
            f"/api/registrations/{registration_id}/drop",
            headers=self.authorization_header(student.user),
        )

        self.assertEqual(response.status_code, 409)
        error = response.json()["error"]
        self.assertEqual(error["code"], "DROP_DEADLINE_PASSED")
        self.assertEqual(
            error["details"]["drop_deadline"],
            deadline.isoformat(),
        )
        self.db.expire_all()
        self.assertEqual(
            self.db.get(Registration, registration_id).registration_status,
            "approved",
        )
        self.assertEqual(self.db.query(Notification).count(), 0)
        self.assertEqual(self.db.query(AuditLog).count(), 0)

    def test_missing_opened_period_blocks_drop(self):
        suffix = uuid4().hex[:8]
        program, advisor = self.make_context(suffix=suffix)
        student = self.make_student(
            suffix=suffix,
            program=program,
            advisor=advisor,
        )
        course = self.make_course(suffix=suffix)
        self.db.add(course)
        registration = self.add_registration(student=student, course=course)
        registration_id = registration.id
        self.db.commit()

        response = self.client.post(
            f"/api/registrations/{registration_id}/drop",
            headers=self.authorization_header(student.user),
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.json()["error"]["code"],
            "DROP_PERIOD_NOT_CONFIGURED",
        )
        self.db.expire_all()
        self.assertEqual(
            self.db.get(Registration, registration_id).registration_status,
            "approved",
        )

    def test_future_period_is_not_treated_as_open_drop_configuration(self):
        suffix = uuid4().hex[:8]
        program, advisor = self.make_context(suffix=suffix)
        student = self.make_student(
            suffix=suffix,
            program=program,
            advisor=advisor,
        )
        course = self.make_course(suffix=suffix)
        self.db.add(course)
        registration = self.add_registration(student=student, course=course)
        now = datetime.now(timezone.utc)
        self.add_period(
            drop_deadline=now.date() + timedelta(days=30),
            opening_time=now + timedelta(days=1),
            closing_time=now + timedelta(days=20),
        )
        registration_id = registration.id
        self.db.commit()
        headers = self.authorization_header(student.user)

        status_response = self.client.get(
            "/api/registrations?status=approved",
            headers=headers,
        )
        drop_response = self.client.post(
            f"/api/registrations/{registration_id}/drop",
            headers=headers,
        )

        eligibility = status_response.json()["data"]["registrations"][0][
            "drop_eligibility"
        ]
        self.assertFalse(eligibility["eligible"])
        self.assertEqual(
            eligibility["reason"],
            "drop_period_not_configured",
        )
        self.assertEqual(drop_response.status_code, 409)
        self.assertEqual(
            drop_response.json()["error"]["code"],
            "DROP_PERIOD_NOT_CONFIGURED",
        )

    def test_only_approved_owned_registration_can_be_dropped(self):
        suffix = uuid4().hex[:8]
        program, advisor = self.make_context(suffix=suffix)
        owner = self.make_student(
            suffix=f"{suffix}-owner",
            program=program,
            advisor=advisor,
        )
        other = self.make_student(
            suffix=f"{suffix}-other",
            program=program,
            advisor=advisor,
        )
        pending_course = self.make_course(suffix=f"{suffix}-pending")
        foreign_course = self.make_course(suffix=f"{suffix}-foreign")
        self.db.add_all([pending_course, foreign_course])
        pending = self.add_registration(
            student=owner,
            course=pending_course,
            registration_status=RegistrationStatus.PENDING.value,
        )
        foreign = self.add_registration(
            student=other,
            course=foreign_course,
        )
        self.add_period(
            drop_deadline=datetime.now(timezone.utc).date()
            + timedelta(days=5)
        )
        pending_id = pending.id
        foreign_id = foreign.id
        self.db.commit()
        headers = self.authorization_header(owner.user)

        invalid_state = self.client.post(
            f"/api/registrations/{pending_id}/drop",
            headers=headers,
        )
        foreign_response = self.client.post(
            f"/api/registrations/{foreign_id}/drop",
            headers=headers,
        )
        missing = self.client.post(
            f"/api/registrations/{uuid4()}/drop",
            headers=headers,
        )

        self.assertEqual(invalid_state.status_code, 409)
        self.assertEqual(
            invalid_state.json()["error"]["code"],
            "REGISTRATION_NOT_DROPPABLE",
        )
        self.assertEqual(
            invalid_state.json()["error"]["details"][
                "registration_status"
            ],
            "pending",
        )
        self.assertEqual(foreign_response.status_code, 404)
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(
            foreign_response.json()["error"],
            missing.json()["error"],
        )

    def test_promotion_failure_rolls_back_drop_notification_and_audit(self):
        suffix = uuid4().hex[:8]
        program, advisor = self.make_context(suffix=suffix)
        student = self.make_student(
            suffix=suffix,
            program=program,
            advisor=advisor,
        )
        course = self.make_course(suffix=suffix)
        self.db.add(course)
        registration = self.add_registration(student=student, course=course)
        self.add_period(
            drop_deadline=datetime.now(timezone.utc).date()
            + timedelta(days=5)
        )
        registration_id = registration.id
        self.db.commit()

        with patch(
            "app.repositories.course_drop_repository."
            "promote_next_waitlisted_student_in_locked_section",
            side_effect=WaitlistPromotionRepositoryError(
                "sensitive promotion failure"
            ),
        ):
            response = self.client.post(
                f"/api/registrations/{registration_id}/drop",
                headers=self.authorization_header(student.user),
            )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json()["error"]["code"],
            "DATABASE_OPERATION_FAILED",
        )
        self.assertNotIn("sensitive", response.text.lower())
        self.db.expire_all()
        self.assertEqual(
            self.db.get(Registration, registration_id).registration_status,
            "approved",
        )
        self.assertEqual(self.db.query(Notification).count(), 0)
        self.assertEqual(self.db.query(AuditLog).count(), 0)

    def test_status_and_drop_repository_failures_are_safe(self):
        suffix = uuid4().hex[:8]
        program, advisor = self.make_context(suffix=suffix)
        student = self.make_student(
            suffix=suffix,
            program=program,
            advisor=advisor,
        )
        self.db.commit()
        headers = self.authorization_header(student.user)

        with patch(
            "app.api.routes.registrations."
            "list_student_registration_statuses",
            side_effect=RegistrationStatusRepositoryError(
                "sensitive read failure"
            ),
        ):
            status_response = self.client.get(
                "/api/registrations",
                headers=headers,
            )

        with patch(
            "app.api.routes.registrations.drop_approved_registration",
            side_effect=CourseDropRepositoryError(
                "sensitive write failure"
            ),
        ):
            drop_response = self.client.post(
                f"/api/registrations/{uuid4()}/drop",
                headers=headers,
            )

        for response in (status_response, drop_response):
            self.assertEqual(response.status_code, 500)
            self.assertEqual(
                response.json()["error"]["code"],
                "DATABASE_OPERATION_FAILED",
            )
            self.assertNotIn("sensitive", response.text.lower())

    def test_authentication_authorization_profile_and_validation_errors(self):
        suffix = uuid4().hex[:8]
        advisor_user = self.make_user(suffix=suffix, role="advisor")
        student_without_profile = self.make_user(
            suffix=f"{suffix}-missing",
            role="student",
        )
        self.db.add_all([advisor_user, student_without_profile])
        self.db.commit()

        unauthenticated = self.client.get("/api/registrations")
        forbidden = self.client.get(
            "/api/registrations",
            headers=self.authorization_header(advisor_user),
        )
        missing_profile = self.client.get(
            "/api/registrations",
            headers=self.authorization_header(student_without_profile),
        )
        invalid_filter = self.client.get(
            "/api/registrations?status=unknown",
            headers=self.authorization_header(student_without_profile),
        )
        invalid_id = self.client.post(
            "/api/registrations/not-a-uuid/drop",
            headers=self.authorization_header(student_without_profile),
        )

        self.assertEqual(unauthenticated.status_code, 401)
        self.assertEqual(forbidden.status_code, 403)
        self.assertEqual(missing_profile.status_code, 404)
        self.assertEqual(invalid_filter.status_code, 422)
        self.assertEqual(invalid_id.status_code, 422)

    def test_concurrent_drop_changes_the_approval_only_once(self):
        suffix = uuid4().hex[:8]
        program, advisor = self.make_context(suffix=suffix)
        student = self.make_student(
            suffix=suffix,
            program=program,
            advisor=advisor,
        )
        course = self.make_course(suffix=suffix)
        self.db.add(course)
        registration = self.add_registration(student=student, course=course)
        self.add_period(
            drop_deadline=datetime.now(timezone.utc).date()
            + timedelta(days=5)
        )
        registration_id = registration.id
        headers = self.authorization_header(student.user)
        self.db.commit()
        start = threading.Barrier(3)
        outcomes = []
        outcome_lock = threading.Lock()

        def drop():
            start.wait(timeout=5)
            response = self.client.post(
                f"/api/registrations/{registration_id}/drop",
                headers=headers,
            )
            with outcome_lock:
                outcomes.append(response.status_code)

        threads = [threading.Thread(target=drop) for _ in range(2)]

        for thread in threads:
            thread.start()

        start.wait(timeout=5)

        for thread in threads:
            thread.join(timeout=10)
            self.assertFalse(thread.is_alive())

        self.assertEqual(sorted(outcomes), [200, 409])
        self.db.expire_all()
        self.assertEqual(
            self.db.get(Registration, registration_id).registration_status,
            "dropped",
        )
        self.assertEqual(self.db.query(Notification).count(), 1)
        self.assertEqual(self.db.query(AuditLog).count(), 1)

    def test_postgresql_drop_queries_lock_section_before_registration(self):
        registration_id = uuid4()
        student_id = uuid4()

        with Session() as db:
            section_statement = locked_drop_section_query(
                db,
                registration_id=registration_id,
                student_id=student_id,
            ).statement
            registration_statement = locked_owned_registration_query(
                db,
                registration_id=registration_id,
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
        self.assertIn("FOR UPDATE OF courses", section_sql)
        self.assertIn("FOR UPDATE OF registrations", registration_sql)

    def test_openapi_documents_status_and_drop_contracts(self):
        schema = self.app.openapi()
        status_operation = schema["paths"]["/api/registrations"]["get"]
        drop_operation = schema["paths"][
            "/api/registrations/{registration_id}/drop"
        ]["post"]

        for operation in (status_operation, drop_operation):
            self.assertIn("security", operation)
            self.assertIn("200", operation["responses"])
            self.assertIn("404", operation["responses"])
            self.assertIn("422", operation["responses"])

        self.assertIn("409", drop_operation["responses"])
        status_schema = status_operation["responses"]["200"]["content"][
            "application/json"
        ]["schema"]
        drop_schema = drop_operation["responses"]["200"]["content"][
            "application/json"
        ]["schema"]
        self.assertEqual(
            status_schema["$ref"],
            "#/components/schemas/RegistrationStatusOverviewResponse",
        )
        self.assertEqual(
            drop_schema["$ref"],
            "#/components/schemas/CourseDropResponse",
        )


if __name__ == "__main__":
    unittest.main()
