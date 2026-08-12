from datetime import datetime, timedelta, timezone
import json
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
from sqlalchemy.orm import sessionmaker
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.errors import (
    api_http_exception_handler,
    api_unhandled_exception_handler,
    api_validation_exception_handler,
)
from app.api.routes.advisor_reviews import router as advisor_reviews_router
from app.database import Base, get_db
from app.database_errors import database_integrity_error_handler
from app.main import app as coursepilot_app
from app.models import (
    Advisor,
    AuditLog,
    Course,
    Department,
    Notification,
    Program,
    Registration,
    RegistrationStatus,
    Student,
    User,
    WaitlistEntry,
    WaitlistStatus,
)
from app.repositories.advisor_review_repository import (
    AdvisorRequestAlreadyReviewedError,
    AdvisorReviewRepositoryError,
    AdvisorReviewSectionsFullError,
    locked_advisor_request_registrations_query,
    locked_advisor_request_sections_query,
    review_advisor_registration_request,
)
from app.security import create_access_token


class AdvisorReviewApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary_directory = tempfile.TemporaryDirectory()
        database_path = (
            Path(cls.temporary_directory.name) / "advisor-review.sqlite"
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
        cls.app.include_router(advisor_reviews_router)

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

    def make_context(
        self,
        *,
        suffix: str,
        minimum_credit: int = 3,
        maximum_credit: int = 18,
    ) -> tuple[Program, Advisor]:
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
        code: str | None = None,
        credits: int = 3,
        capacity: int = 10,
        day: str = "Sunday",
        start_time: str = "09:00",
        end_time: str = "10:00",
    ) -> Course:
        return Course(
            course_id=f"course-{suffix}",
            code=code or f"CSE {suffix}",
            title=f"Course {suffix}",
            department="CSE",
            semester="Fall 2026",
            instructor="Dr. Advisor",
            credits=credits,
            capacity=capacity,
            available_seats=capacity,
            is_mandatory=False,
            prerequisites=[],
            section="A",
            schedule=[
                {
                    "day": day,
                    "start_time": start_time,
                    "end_time": end_time,
                    "room": f"ROOM-{suffix}",
                }
            ],
        )

    def add_request(
        self,
        *,
        student: Student,
        courses: list[Course],
        submitted_at: datetime | None = None,
        registration_status: str = RegistrationStatus.PENDING.value,
    ) -> list[Registration]:
        request_time = submitted_at or datetime.now(timezone.utc)
        registrations = [
            Registration(
                student=student,
                section=course,
                registration_status=registration_status,
                submitted_at=request_time,
            )
            for course in courses
        ]
        self.db.add_all(registrations)
        self.db.flush()
        return registrations

    @staticmethod
    def request_id(registrations: list[Registration]):
        return min(
            (registration.id for registration in registrations),
            key=str,
        )

    @staticmethod
    def authorization_header(user: User) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {create_access_token(user.id)}"
        }

    def fill_section(
        self,
        *,
        course: Course,
        program: Program,
        advisor: Advisor,
        suffix: str,
    ) -> None:
        for index in range(course.capacity):
            student = self.make_student(
                suffix=f"{suffix}-seat-{index}",
                program=program,
                advisor=advisor,
            )
            self.db.add(
                Registration(
                    student=student,
                    section=course,
                    registration_status=(
                        RegistrationStatus.APPROVED.value
                    ),
                    submitted_at=datetime.now(timezone.utc),
                )
            )
        self.db.flush()

    def test_assigned_advisor_lists_grouped_pending_requests(self):
        suffix = uuid4().hex[:8]
        program, advisor = self.make_context(suffix=suffix)
        first_student = self.make_student(
            suffix=f"{suffix}-first",
            program=program,
            advisor=advisor,
        )
        second_student = self.make_student(
            suffix=f"{suffix}-second",
            program=program,
            advisor=advisor,
        )
        first_courses = [
            self.make_course(suffix=f"{suffix}-one", code="CSE 101"),
            self.make_course(
                suffix=f"{suffix}-two",
                code="CSE 102",
                day="Monday",
            ),
        ]
        second_course = self.make_course(
            suffix=f"{suffix}-three",
            code="CSE 103",
        )
        self.db.add_all([*first_courses, second_course])
        older = datetime.now(timezone.utc) - timedelta(hours=1)
        newer = datetime.now(timezone.utc)
        first_request = self.add_request(
            student=first_student,
            courses=first_courses,
            submitted_at=older,
        )
        self.add_request(
            student=second_student,
            courses=[second_course],
            submitted_at=newer,
        )

        other_program, other_advisor = self.make_context(
            suffix=f"{suffix}-other"
        )
        other_student = self.make_student(
            suffix=f"{suffix}-other",
            program=other_program,
            advisor=other_advisor,
        )
        other_course = self.make_course(
            suffix=f"{suffix}-hidden",
            code="CSE 999",
        )
        self.db.add(other_course)
        self.add_request(student=other_student, courses=[other_course])
        self.db.commit()

        response = self.client.get(
            "/api/advisor/registration-requests?page=1&page_size=1",
            headers=self.authorization_header(advisor.user),
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["pagination"]["total_items"], 2)
        self.assertEqual(payload["pagination"]["total_pages"], 2)
        self.assertEqual(len(payload["data"]), 1)
        self.assertEqual(
            payload["data"][0]["student"]["student_number"],
            second_student.student_number,
        )

        second_page = self.client.get(
            "/api/advisor/registration-requests?page=2&page_size=1",
            headers=self.authorization_header(advisor.user),
        ).json()
        listed = second_page["data"][0]
        self.assertEqual(listed["course_count"], 2)
        self.assertEqual(listed["total_credits"], 6)
        self.assertEqual(
            listed["request_id"],
            str(self.request_id(first_request)),
        )
        self.assertEqual(
            [course["code"] for course in listed["courses"]],
            ["CSE 101", "CSE 102"],
        )

    def test_advisor_inspects_validation_and_waitlist_details(self):
        suffix = uuid4().hex[:8]
        program, advisor = self.make_context(
            suffix=suffix,
            minimum_credit=6,
            maximum_credit=12,
        )
        student = self.make_student(
            suffix=suffix,
            program=program,
            advisor=advisor,
        )
        courses = [
            self.make_course(suffix=f"{suffix}-one", code="CSE 201"),
            self.make_course(
                suffix=f"{suffix}-two",
                code="CSE 202",
                day="Monday",
            ),
        ]
        waitlist_course = self.make_course(
            suffix=f"{suffix}-wait",
            code="CSE 299",
            capacity=1,
        )
        self.db.add_all([*courses, waitlist_course])
        registrations = self.add_request(
            student=student,
            courses=courses,
        )
        self.db.add(
            WaitlistEntry(
                student=student,
                section=waitlist_course,
                waitlist_status=WaitlistStatus.ACTIVE.value,
                joined_at=datetime.now(timezone.utc),
            )
        )
        self.db.commit()

        response = self.client.get(
            "/api/advisor/registration-requests/"
            f"{self.request_id(registrations)}",
            headers=self.authorization_header(advisor.user),
        )

        self.assertEqual(response.status_code, 200)
        details = response.json()["data"]
        self.assertEqual(details["student"]["student_number"], student.student_number)
        self.assertEqual(details["course_count"], 2)
        self.assertEqual(details["total_credits"], 6)
        self.assertTrue(details["credit_validation"]["is_valid"])
        self.assertFalse(details["schedule_validation"]["has_conflicts"])
        self.assertTrue(
            all(
                course["prerequisite_validation"]["eligible"]
                for course in details["courses"]
            )
        )
        self.assertEqual(len(details["waitlist_entries"]), 1)
        self.assertEqual(
            details["waitlist_entries"][0]["course"]["course_id"],
            waitlist_course.course_id,
        )

    def test_unassigned_request_is_not_disclosed_or_mutated(self):
        suffix = uuid4().hex[:8]
        program, assigned_advisor = self.make_context(suffix=suffix)
        _, other_advisor = self.make_context(suffix=f"{suffix}-other")
        student = self.make_student(
            suffix=suffix,
            program=program,
            advisor=assigned_advisor,
        )
        course = self.make_course(suffix=suffix)
        self.db.add(course)
        registrations = self.add_request(student=student, courses=[course])
        request_id = self.request_id(registrations)
        self.db.commit()

        detail_response = self.client.get(
            f"/api/advisor/registration-requests/{request_id}",
            headers=self.authorization_header(other_advisor.user),
        )
        decision_response = self.client.post(
            f"/api/advisor/registration-requests/{request_id}/decision",
            headers=self.authorization_header(other_advisor.user),
            json={"decision": "approved"},
        )

        self.assertEqual(detail_response.status_code, 404)
        self.assertEqual(decision_response.status_code, 404)
        self.assertEqual(
            detail_response.json()["error"]["code"],
            "REGISTRATION_REQUEST_NOT_FOUND",
        )
        self.db.expire_all()
        self.assertEqual(
            self.db.get(Registration, request_id).registration_status,
            RegistrationStatus.PENDING.value,
        )

    def test_approval_updates_whole_request_and_related_records(self):
        suffix = uuid4().hex[:8]
        program, advisor = self.make_context(suffix=suffix)
        student = self.make_student(
            suffix=suffix,
            program=program,
            advisor=advisor,
        )
        courses = [
            self.make_course(suffix=f"{suffix}-one", code="CSE 301"),
            self.make_course(
                suffix=f"{suffix}-two",
                code="CSE 302",
                day="Monday",
            ),
        ]
        self.db.add_all(courses)
        registrations = self.add_request(student=student, courses=courses)
        registration_ids = {registration.id for registration in registrations}
        request_id = self.request_id(registrations)
        advisor_id = advisor.id
        self.db.commit()

        response = self.client.post(
            f"/api/advisor/registration-requests/{request_id}/decision",
            headers=self.authorization_header(advisor.user),
            json={
                "decision": "approved",
                "comment": "  Approved as planned.  ",
            },
        )

        self.assertEqual(response.status_code, 200)
        result = response.json()["data"]
        self.assertEqual(result["request_status"], "approved")
        self.assertEqual(result["advisor_comment"], "Approved as planned.")
        self.assertEqual(
            set(result["registration_ids"]),
            {str(registration_id) for registration_id in registration_ids},
        )
        self.db.expire_all()
        stored = (
            self.db.query(Registration)
            .filter(Registration.id.in_(registration_ids))
            .all()
        )
        self.assertTrue(
            all(
                registration.registration_status == "approved"
                and registration.reviewed_by == advisor_id
                and registration.reviewed_at is not None
                and registration.advisor_comment == "Approved as planned."
                for registration in stored
            )
        )
        self.assertEqual(self.db.query(Notification).count(), 1)
        self.assertEqual(self.db.query(AuditLog).count(), 1)
        audit_details = json.loads(
            self.db.query(AuditLog).one().action_details
        )
        self.assertEqual(audit_details["decision"], "approved")
        self.assertEqual(audit_details["request_id"], str(request_id))

    def test_approval_comment_is_optional_and_blank_becomes_none(self):
        suffix = uuid4().hex[:8]
        program, advisor = self.make_context(suffix=suffix)
        student = self.make_student(
            suffix=suffix,
            program=program,
            advisor=advisor,
        )
        course = self.make_course(suffix=suffix)
        self.db.add(course)
        registrations = self.add_request(student=student, courses=[course])
        request_id = self.request_id(registrations)
        self.db.commit()

        response = self.client.post(
            f"/api/advisor/registration-requests/{request_id}/decision",
            headers=self.authorization_header(advisor.user),
            json={"decision": "approved", "comment": "   "},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["data"]["advisor_comment"])
        self.db.expire_all()
        self.assertIsNone(
            self.db.get(Registration, request_id).advisor_comment
        )

    def test_rejection_requires_a_nonblank_reason(self):
        suffix = uuid4().hex[:8]
        program, advisor = self.make_context(suffix=suffix)
        student = self.make_student(
            suffix=suffix,
            program=program,
            advisor=advisor,
        )
        course = self.make_course(suffix=suffix)
        self.db.add(course)
        registrations = self.add_request(student=student, courses=[course])
        request_id = self.request_id(registrations)
        self.db.commit()

        for payload in (
            {"decision": "rejected"},
            {"decision": "rejected", "comment": None},
            {"decision": "rejected", "comment": "   "},
        ):
            with self.subTest(payload=payload):
                response = self.client.post(
                    "/api/advisor/registration-requests/"
                    f"{request_id}/decision",
                    headers=self.authorization_header(advisor.user),
                    json=payload,
                )
                self.assertEqual(response.status_code, 422)
                self.assertEqual(
                    response.json()["error"]["code"],
                    "REQUEST_VALIDATION_ERROR",
                )

        self.db.expire_all()
        self.assertEqual(
            self.db.get(Registration, request_id).registration_status,
            RegistrationStatus.PENDING.value,
        )

    def test_rejection_updates_whole_request_and_saves_reason(self):
        suffix = uuid4().hex[:8]
        program, advisor = self.make_context(suffix=suffix)
        student = self.make_student(
            suffix=suffix,
            program=program,
            advisor=advisor,
        )
        courses = [
            self.make_course(suffix=f"{suffix}-one", code="CSE 401"),
            self.make_course(
                suffix=f"{suffix}-two",
                code="CSE 402",
                day="Monday",
            ),
        ]
        self.db.add_all(courses)
        registrations = self.add_request(student=student, courses=courses)
        registration_ids = [registration.id for registration in registrations]
        request_id = self.request_id(registrations)
        self.db.commit()

        response = self.client.post(
            f"/api/advisor/registration-requests/{request_id}/decision",
            headers=self.authorization_header(advisor.user),
            json={
                "decision": "rejected",
                "comment": "Prerequisite documentation is incomplete.",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["data"]["request_status"],
            "rejected",
        )
        self.db.expire_all()
        stored = (
            self.db.query(Registration)
            .filter(Registration.id.in_(registration_ids))
            .all()
        )
        self.assertTrue(
            all(
                registration.registration_status == "rejected"
                and registration.advisor_comment
                == "Prerequisite documentation is incomplete."
                for registration in stored
            )
        )
        notification = self.db.query(Notification).one()
        self.assertIn("Reason:", notification.message)
        self.assertEqual(
            self.db.query(AuditLog).one().action_type,
            "advisor_registration_rejected",
        )

    def test_full_section_prevents_partial_approval(self):
        suffix = uuid4().hex[:8]
        program, advisor = self.make_context(suffix=suffix)
        student = self.make_student(
            suffix=suffix,
            program=program,
            advisor=advisor,
        )
        open_course = self.make_course(
            suffix=f"{suffix}-open",
            code="CSE 501",
        )
        full_course = self.make_course(
            suffix=f"{suffix}-full",
            code="CSE 502",
            capacity=1,
            day="Monday",
        )
        self.db.add_all([open_course, full_course])
        registrations = self.add_request(
            student=student,
            courses=[open_course, full_course],
        )
        registration_ids = [registration.id for registration in registrations]
        request_id = self.request_id(registrations)
        self.fill_section(
            course=full_course,
            program=program,
            advisor=advisor,
            suffix=suffix,
        )
        self.db.commit()

        response = self.client.post(
            f"/api/advisor/registration-requests/{request_id}/decision",
            headers=self.authorization_header(advisor.user),
            json={"decision": "approved"},
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"]["code"], "SECTION_FULL")
        self.assertEqual(
            response.json()["error"]["details"]["sections"][0][
                "course_id"
            ],
            full_course.course_id,
        )
        self.db.expire_all()
        statuses = {
            registration.registration_status
            for registration in self.db.query(Registration)
            .filter(Registration.id.in_(registration_ids))
            .all()
        }
        self.assertEqual(statuses, {RegistrationStatus.PENDING.value})
        self.assertEqual(self.db.query(Notification).count(), 0)
        self.assertEqual(self.db.query(AuditLog).count(), 0)

    def test_request_cannot_receive_a_second_decision(self):
        suffix = uuid4().hex[:8]
        program, advisor = self.make_context(suffix=suffix)
        student = self.make_student(
            suffix=suffix,
            program=program,
            advisor=advisor,
        )
        course = self.make_course(suffix=suffix)
        self.db.add(course)
        registrations = self.add_request(student=student, courses=[course])
        request_id = self.request_id(registrations)
        self.db.commit()
        headers = self.authorization_header(advisor.user)

        first = self.client.post(
            f"/api/advisor/registration-requests/{request_id}/decision",
            headers=headers,
            json={"decision": "approved"},
        )
        second = self.client.post(
            f"/api/advisor/registration-requests/{request_id}/decision",
            headers=headers,
            json={
                "decision": "rejected",
                "comment": "A later conflicting decision.",
            },
        )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 409)
        self.assertEqual(
            second.json()["error"]["code"],
            "REGISTRATION_REQUEST_ALREADY_REVIEWED",
        )
        self.assertEqual(
            second.json()["error"]["details"]["request_status"],
            "approved",
        )
        self.assertEqual(self.db.query(Notification).count(), 1)
        self.assertEqual(self.db.query(AuditLog).count(), 1)

    def test_history_filter_returns_completed_decisions(self):
        suffix = uuid4().hex[:8]
        program, advisor = self.make_context(suffix=suffix)
        student = self.make_student(
            suffix=suffix,
            program=program,
            advisor=advisor,
        )
        course = self.make_course(suffix=suffix)
        self.db.add(course)
        registrations = self.add_request(student=student, courses=[course])
        request_id = self.request_id(registrations)
        self.db.commit()
        headers = self.authorization_header(advisor.user)
        self.client.post(
            f"/api/advisor/registration-requests/{request_id}/decision",
            headers=headers,
            json={
                "decision": "rejected",
                "comment": "Please revise the selection.",
            },
        )

        pending = self.client.get(
            "/api/advisor/registration-requests",
            headers=headers,
        ).json()
        history = self.client.get(
            "/api/advisor/registration-requests?status=rejected",
            headers=headers,
        ).json()

        self.assertEqual(pending["pagination"]["total_items"], 0)
        self.assertEqual(history["pagination"]["total_items"], 1)
        self.assertEqual(history["data"][0]["request_status"], "rejected")
        self.assertEqual(
            history["data"][0]["advisor_comment"],
            "Please revise the selection.",
        )

    def test_concurrent_reviews_cannot_allocate_the_same_final_seat(self):
        suffix = uuid4().hex[:8]
        program, advisor = self.make_context(suffix=suffix)
        course = self.make_course(suffix=suffix, capacity=1)
        self.db.add(course)
        students = [
            self.make_student(
                suffix=f"{suffix}-{index}",
                program=program,
                advisor=advisor,
            )
            for index in range(2)
        ]
        requests = [
            self.add_request(
                student=student,
                courses=[course],
                submitted_at=(
                    datetime.now(timezone.utc)
                    + timedelta(microseconds=index)
                ),
            )
            for index, student in enumerate(students)
        ]
        request_ids = [self.request_id(request) for request in requests]
        advisor_id = advisor.id
        actor_user_id = advisor.user_id
        self.db.commit()
        barrier = threading.Barrier(3)
        result_lock = threading.Lock()
        outcomes = []

        def review(request_id):
            db = self.session_factory()
            try:
                thread_advisor = db.get(Advisor, advisor_id)
                barrier.wait(timeout=5)
                try:
                    review_advisor_registration_request(
                        db,
                        advisor=thread_advisor,
                        actor_user_id=actor_user_id,
                        request_id=request_id,
                        decision="approved",
                        comment=None,
                    )
                    outcome = "approved"
                except AdvisorReviewSectionsFullError:
                    outcome = "full"

                with result_lock:
                    outcomes.append(outcome)
            finally:
                db.close()

        threads = [
            threading.Thread(target=review, args=(request_id,))
            for request_id in request_ids
        ]

        for thread in threads:
            thread.start()

        barrier.wait(timeout=5)

        for thread in threads:
            thread.join(timeout=10)
            self.assertFalse(thread.is_alive())

        self.assertEqual(sorted(outcomes), ["approved", "full"])
        self.db.expire_all()
        statuses = sorted(
            registration.registration_status
            for registration in self.db.query(Registration)
            .filter(Registration.id.in_(request_ids))
            .all()
        )
        self.assertEqual(statuses, ["approved", "pending"])
        self.assertEqual(self.db.query(Notification).count(), 1)
        self.assertEqual(self.db.query(AuditLog).count(), 1)

    def test_concurrent_decisions_change_one_request_only_once(self):
        suffix = uuid4().hex[:8]
        program, advisor = self.make_context(suffix=suffix)
        student = self.make_student(
            suffix=suffix,
            program=program,
            advisor=advisor,
        )
        course = self.make_course(suffix=suffix)
        self.db.add(course)
        registrations = self.add_request(student=student, courses=[course])
        request_id = self.request_id(registrations)
        advisor_id = advisor.id
        actor_user_id = advisor.user_id
        self.db.commit()
        barrier = threading.Barrier(3)
        result_lock = threading.Lock()
        outcomes = []

        def decide(decision, comment):
            db = self.session_factory()
            try:
                thread_advisor = db.get(Advisor, advisor_id)
                barrier.wait(timeout=5)
                try:
                    review_advisor_registration_request(
                        db,
                        advisor=thread_advisor,
                        actor_user_id=actor_user_id,
                        request_id=request_id,
                        decision=decision,
                        comment=comment,
                    )
                    outcome = decision
                except AdvisorRequestAlreadyReviewedError:
                    outcome = "already_reviewed"

                with result_lock:
                    outcomes.append(outcome)
            finally:
                db.close()

        threads = [
            threading.Thread(target=decide, args=("approved", None)),
            threading.Thread(
                target=decide,
                args=("rejected", "Concurrent rejection."),
            ),
        ]

        for thread in threads:
            thread.start()

        barrier.wait(timeout=5)

        for thread in threads:
            thread.join(timeout=10)
            self.assertFalse(thread.is_alive())

        self.assertEqual(outcomes.count("already_reviewed"), 1)
        self.assertEqual(len(outcomes), 2)
        winning_status = next(
            outcome
            for outcome in outcomes
            if outcome != "already_reviewed"
        )
        self.db.expire_all()
        stored = self.db.get(Registration, request_id)
        self.assertEqual(stored.registration_status, winning_status)
        self.assertEqual(self.db.query(Notification).count(), 1)
        self.assertEqual(self.db.query(AuditLog).count(), 1)

    def test_failed_commit_rolls_back_the_entire_decision(self):
        suffix = uuid4().hex[:8]
        program, advisor = self.make_context(suffix=suffix)
        student = self.make_student(
            suffix=suffix,
            program=program,
            advisor=advisor,
        )
        course = self.make_course(suffix=suffix)
        self.db.add(course)
        registrations = self.add_request(student=student, courses=[course])
        request_id = self.request_id(registrations)
        advisor_id = advisor.id
        actor_user_id = advisor.user_id
        self.db.commit()

        with patch.object(
            self.db,
            "commit",
            side_effect=RuntimeError("simulated commit failure"),
        ):
            with self.assertRaises(AdvisorReviewRepositoryError):
                review_advisor_registration_request(
                    self.db,
                    advisor=advisor,
                    actor_user_id=actor_user_id,
                    request_id=request_id,
                    decision="approved",
                    comment=None,
                )

        self.db.expire_all()
        registration = self.db.get(Registration, request_id)
        self.assertEqual(registration.registration_status, "pending")
        self.assertIsNone(registration.reviewed_by)
        self.assertIsNone(registration.reviewed_at)
        self.assertEqual(self.db.query(Notification).count(), 0)
        self.assertEqual(self.db.query(AuditLog).count(), 0)
        self.assertEqual(advisor_id, advisor.id)

    def test_authentication_role_profile_and_input_validation(self):
        suffix = uuid4().hex[:8]
        program, advisor = self.make_context(suffix=suffix)
        student = self.make_student(
            suffix=suffix,
            program=program,
            advisor=advisor,
        )
        profileless = self.make_user(
            suffix=f"{suffix}-profileless",
            role="advisor",
        )
        self.db.add(profileless)
        self.db.commit()

        unauthenticated = self.client.get(
            "/api/advisor/registration-requests"
        )
        wrong_role = self.client.get(
            "/api/advisor/registration-requests",
            headers=self.authorization_header(student.user),
        )
        missing_profile = self.client.get(
            "/api/advisor/registration-requests",
            headers=self.authorization_header(profileless),
        )
        invalid_query = self.client.get(
            "/api/advisor/registration-requests?status=draft&page=0",
            headers=self.authorization_header(advisor.user),
        )

        self.assertEqual(unauthenticated.status_code, 401)
        self.assertEqual(wrong_role.status_code, 403)
        self.assertEqual(missing_profile.status_code, 404)
        self.assertEqual(
            missing_profile.json()["error"]["code"],
            "ADVISOR_PROFILE_NOT_FOUND",
        )
        self.assertEqual(invalid_query.status_code, 422)

    def test_repository_errors_are_safe_at_the_http_boundary(self):
        suffix = uuid4().hex[:8]
        _, advisor = self.make_context(suffix=suffix)
        self.db.commit()

        with patch(
            "app.api.routes.advisor_reviews."
            "list_advisor_registration_requests",
            side_effect=AdvisorReviewRepositoryError(
                "sensitive database host and SQL statement"
            ),
        ):
            response = self.client.get(
                "/api/advisor/registration-requests",
                headers=self.authorization_header(advisor.user),
            )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json()["error"]["code"],
            "DATABASE_OPERATION_FAILED",
        )
        self.assertNotIn("database host", response.text.lower())

    def test_postgresql_queries_lock_sections_before_registrations(self):
        suffix = uuid4().hex[:8]
        program, advisor = self.make_context(suffix=suffix)
        student = self.make_student(
            suffix=suffix,
            program=program,
            advisor=advisor,
        )
        submitted_at = datetime.now(timezone.utc)
        section_sql = str(
            locked_advisor_request_sections_query(
                self.db,
                student_id=student.id,
                submitted_at=submitted_at,
            ).statement.compile(
                dialect=postgresql.dialect(),
                compile_kwargs={"literal_binds": True},
            )
        ).lower()
        registration_sql = str(
            locked_advisor_request_registrations_query(
                self.db,
                student_id=student.id,
                submitted_at=submitted_at,
            ).statement.compile(
                dialect=postgresql.dialect(),
                compile_kwargs={"literal_binds": True},
            )
        ).lower()

        self.assertIn("for update of courses", section_sql)
        self.assertIn("order by courses.id", section_sql)
        self.assertIn("for update of registrations", registration_sql)
        self.assertIn("order by registrations.id", registration_sql)

    def test_openapi_documents_advisor_security_and_contracts(self):
        schema = coursepilot_app.openapi()
        list_operation = schema["paths"][
            "/api/advisor/registration-requests"
        ]["get"]
        decision_operation = schema["paths"][
            "/api/advisor/registration-requests/{request_id}/decision"
        ]["post"]

        self.assertEqual(
            list_operation["security"],
            [{"HTTPBearer": []}],
        )
        self.assertIn("200", list_operation["responses"])
        self.assertIn("401", list_operation["responses"])
        self.assertIn("403", decision_operation["responses"])
        self.assertIn("409", decision_operation["responses"])
        self.assertIn("422", decision_operation["responses"])


if __name__ == "__main__":
    unittest.main()
