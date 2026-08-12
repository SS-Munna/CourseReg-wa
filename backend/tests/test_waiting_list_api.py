from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from uuid import UUID, uuid4

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
from app.api.routes.waitlists import router as waitlists_router
from app.database import Base, get_db
from app.database_errors import database_integrity_error_handler
from app.main import app as coursepilot_app
from app.models import (
    Advisor,
    Course,
    CoursePrerequisite,
    Department,
    Program,
    Registration,
    RegistrationStatus,
    Student,
    User,
    WaitlistEntry,
    WaitlistStatus,
)
from app.repositories.waitlist_repository import (
    DuplicateWaitlistEntryError,
    WaitlistRepositoryError,
    active_waitlist_entry_query,
    join_waitlist,
    leave_waitlist,
    locked_waitlist_section_query,
)
from app.security import create_access_token


class WaitingListApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary_directory = tempfile.TemporaryDirectory()
        database_path = (
            Path(cls.temporary_directory.name) / "waitlists.sqlite"
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
        cls.app.include_router(waitlists_router)

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
        code: str | None = None,
        capacity: int = 1,
        available_seats: int | None = None,
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
            instructor="Dr. Waitlist",
            credits=3,
            capacity=capacity,
            available_seats=(
                capacity
                if available_seats is None
                else available_seats
            ),
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
        self.db.flush()
        return registration

    def fill_section(
        self,
        *,
        course: Course,
        suffix: str,
        count: int | None = None,
    ) -> None:
        for index in range(course.capacity if count is None else count):
            student = self.make_student(
                suffix=f"{suffix}-seat-{index}"
            )
            self.add_registration(
                student=student,
                course=course,
                registration_status=RegistrationStatus.APPROVED.value,
            )

    def add_waitlist_entry(
        self,
        *,
        student: Student,
        course: Course,
        joined_at: datetime,
        waitlist_status: str = WaitlistStatus.ACTIVE.value,
        removed_at: datetime | None = None,
    ) -> WaitlistEntry:
        entry = WaitlistEntry(
            student=student,
            section=course,
            waitlist_status=waitlist_status,
            joined_at=joined_at,
            removed_at=removed_at,
        )
        self.db.add(entry)
        self.db.flush()
        return entry

    def test_student_can_join_list_and_leave_a_full_section(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(suffix=f"{suffix}-owner")
        course = self.make_course(
            suffix=suffix,
            available_seats=1,
        )
        self.db.add(course)
        self.db.flush()
        self.fill_section(course=course, suffix=suffix)
        self.db.commit()
        headers = self.authorization_header(student.user)

        created = self.client.post(
            "/api/waitlists",
            json={"course_id": f"  {course.course_id}  "},
            headers=headers,
        )

        self.assertEqual(created.status_code, 201)
        created_data = created.json()["data"]
        self.assertEqual(created_data["waitlist_status"], "active")
        self.assertEqual(created_data["queue_position"], 1)
        self.assertEqual(created_data["total_waiting"], 1)
        self.assertEqual(created_data["course"]["available_seats"], 0)
        self.assertEqual(
            created_data["course"]["course_id"],
            course.course_id,
        )

        listed = self.client.get("/api/waitlists", headers=headers)

        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.json()["data"], [created_data])

        removed = self.client.delete(
            f"/api/waitlists/{course.course_id}",
            headers=headers,
        )

        self.assertEqual(removed.status_code, 200)
        removed_data = removed.json()["data"]
        self.assertEqual(
            removed_data["waitlist_entry_id"],
            created_data["waitlist_entry_id"],
        )
        self.assertEqual(removed_data["waitlist_status"], "removed")
        self.assertEqual(removed_data["previous_queue_position"], 1)
        self.assertEqual(removed_data["remaining_waiting"], 0)
        self.assertEqual(
            self.client.get(
                "/api/waitlists",
                headers=headers,
            ).json()["data"],
            [],
        )

        self.db.expire_all()
        stored = self.db.get(
            WaitlistEntry,
            UUID(created_data["waitlist_entry_id"]),
        )
        self.assertEqual(stored.waitlist_status, "removed")
        self.assertIsNotNone(stored.removed_at)

    def test_positions_follow_join_time_and_shift_after_leave(self):
        suffix = uuid4().hex[:8]
        students = [
            self.make_student(suffix=f"{suffix}-{index}")
            for index in range(3)
        ]
        course = self.make_course(suffix=suffix)
        self.db.add(course)
        self.db.flush()
        self.fill_section(course=course, suffix=suffix)
        first_time = datetime(2026, 8, 12, 8, 0, tzinfo=timezone.utc)

        for index, student in enumerate(students):
            self.add_waitlist_entry(
                student=student,
                course=course,
                joined_at=first_time + timedelta(minutes=index),
            )

        self.db.commit()

        for expected_position, student in enumerate(students, start=1):
            response = self.client.get(
                "/api/waitlists",
                headers=self.authorization_header(student.user),
            )
            entry = response.json()["data"][0]
            self.assertEqual(entry["queue_position"], expected_position)
            self.assertEqual(entry["total_waiting"], 3)

        removed = self.client.delete(
            f"/api/waitlists/{course.course_id}",
            headers=self.authorization_header(students[1].user),
        )
        shifted = self.client.get(
            "/api/waitlists",
            headers=self.authorization_header(students[2].user),
        )

        self.assertEqual(removed.json()["data"]["remaining_waiting"], 2)
        self.assertEqual(
            shifted.json()["data"][0]["queue_position"],
            2,
        )
        self.assertEqual(shifted.json()["data"][0]["total_waiting"], 2)

    def test_removed_entry_can_rejoin_at_the_end_of_the_queue(self):
        suffix = uuid4().hex[:8]
        returning = self.make_student(suffix=f"{suffix}-returning")
        waiting = self.make_student(suffix=f"{suffix}-waiting")
        course = self.make_course(suffix=suffix)
        self.db.add(course)
        self.db.flush()
        self.fill_section(course=course, suffix=suffix)
        old_time = datetime(2026, 8, 11, 8, 0, tzinfo=timezone.utc)
        removed = self.add_waitlist_entry(
            student=returning,
            course=course,
            joined_at=old_time,
            waitlist_status=WaitlistStatus.REMOVED.value,
            removed_at=old_time + timedelta(hours=1),
        )
        removed_id = removed.id
        self.add_waitlist_entry(
            student=waiting,
            course=course,
            joined_at=old_time + timedelta(days=1),
        )
        self.db.commit()

        response = self.client.post(
            "/api/waitlists",
            json={"course_id": course.course_id},
            headers=self.authorization_header(returning.user),
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()["data"]
        self.assertEqual(data["waitlist_entry_id"], str(removed_id))
        self.assertEqual(data["queue_position"], 2)
        self.assertEqual(data["total_waiting"], 2)
        self.db.expire_all()
        stored = self.db.get(WaitlistEntry, removed_id)
        self.assertEqual(stored.waitlist_status, "active")
        self.assertIsNone(stored.removed_at)

    def test_duplicate_active_entry_is_rejected_with_position(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(suffix=f"{suffix}-owner")
        course = self.make_course(suffix=suffix)
        self.db.add(course)
        self.db.flush()
        self.fill_section(course=course, suffix=suffix)
        self.add_waitlist_entry(
            student=student,
            course=course,
            joined_at=datetime.now(timezone.utc),
        )
        self.db.commit()

        response = self.client.post(
            "/api/waitlists",
            json={"course_id": course.course_id},
            headers=self.authorization_header(student.user),
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.json()["error"],
            {
                "code": "DUPLICATE_WAITLIST_ENTRY",
                "message": (
                    "This course section is already on your waiting list."
                ),
                "details": {
                    "waitlist_status": "active",
                    "queue_position": 1,
                },
            },
        )
        self.assertEqual(self.db.query(WaitlistEntry).count(), 1)

    def test_promoted_entry_cannot_be_rejoined(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(suffix=f"{suffix}-owner")
        course = self.make_course(suffix=suffix)
        self.db.add(course)
        self.db.flush()
        self.fill_section(course=course, suffix=suffix)
        self.add_waitlist_entry(
            student=student,
            course=course,
            joined_at=datetime.now(timezone.utc),
            waitlist_status=WaitlistStatus.PROMOTED.value,
        )
        self.db.commit()

        response = self.client.post(
            "/api/waitlists",
            json={"course_id": course.course_id},
            headers=self.authorization_header(student.user),
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.json()["error"]["code"],
            "WAITLIST_ENTRY_NOT_JOINABLE",
        )

    def test_live_approved_count_must_show_a_full_section(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(suffix=f"{suffix}-owner")
        course = self.make_course(
            suffix=suffix,
            capacity=2,
            available_seats=0,
        )
        self.db.add(course)
        self.db.flush()
        self.fill_section(course=course, suffix=suffix, count=1)
        self.db.commit()

        response = self.client.post(
            "/api/waitlists",
            json={"course_id": course.course_id},
            headers=self.authorization_header(student.user),
        )

        self.assertEqual(response.status_code, 409)
        error = response.json()["error"]
        self.assertEqual(error["code"], "SECTION_NOT_FULL")
        self.assertEqual(error["details"]["available_seats"], 1)
        self.assertFalse(error["details"]["is_full"])
        self.assertEqual(self.db.query(WaitlistEntry).count(), 0)

    def test_existing_registration_blocks_waitlist_join(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(suffix=f"{suffix}-owner")
        course = self.make_course(suffix=suffix)
        self.db.add(course)
        self.db.flush()
        self.fill_section(course=course, suffix=suffix)
        self.add_registration(
            student=student,
            course=course,
            registration_status=RegistrationStatus.DRAFT.value,
        )
        self.db.commit()

        response = self.client.post(
            "/api/waitlists",
            json={"course_id": course.course_id},
            headers=self.authorization_header(student.user),
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.json()["error"],
            {
                "code": "DUPLICATE_REGISTRATION",
                "message": (
                    "This course section is already selected or registered."
                ),
                "details": {"registration_status": "draft"},
            },
        )
        self.assertEqual(self.db.query(WaitlistEntry).count(), 0)

    def test_prerequisites_are_revalidated_before_join(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(suffix=f"{suffix}-owner")
        prerequisite = self.make_course(
            suffix=f"{suffix}-prerequisite",
            code="CSE 101",
        )
        course = self.make_course(
            suffix=suffix,
            code="CSE 201",
        )
        self.db.add_all([prerequisite, course])
        self.db.flush()
        self.db.add(
            CoursePrerequisite(
                course=course,
                prerequisite_course=prerequisite,
                minimum_grade="C",
            )
        )
        self.fill_section(course=course, suffix=suffix)
        self.db.commit()

        response = self.client.post(
            "/api/waitlists",
            json={"course_id": course.course_id},
            headers=self.authorization_header(student.user),
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json()["error"]["code"],
            "PREREQUISITES_NOT_MET",
        )
        self.assertEqual(self.db.query(WaitlistEntry).count(), 0)

    def test_schedule_conflict_is_revalidated_before_join(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(suffix=f"{suffix}-owner")
        existing = self.make_course(
            suffix=f"{suffix}-existing",
            code="CSE 301",
            start_time="09:00",
            end_time="10:30",
        )
        course = self.make_course(
            suffix=suffix,
            code="CSE 302",
            start_time="10:00",
            end_time="11:00",
        )
        self.db.add_all([existing, course])
        self.db.flush()
        self.add_registration(
            student=student,
            course=existing,
            registration_status=RegistrationStatus.APPROVED.value,
        )
        self.fill_section(course=course, suffix=suffix)
        self.db.commit()

        response = self.client.post(
            "/api/waitlists",
            json={"course_id": course.course_id},
            headers=self.authorization_header(student.user),
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.json()["error"]["code"],
            "SCHEDULE_CONFLICT",
        )
        self.assertEqual(self.db.query(WaitlistEntry).count(), 0)

    def test_missing_foreign_and_inactive_entries_are_not_left(self):
        suffix = uuid4().hex[:8]
        owner = self.make_student(suffix=f"{suffix}-owner")
        other = self.make_student(suffix=f"{suffix}-other")
        course = self.make_course(suffix=suffix)
        self.db.add(course)
        self.db.flush()
        entry = self.add_waitlist_entry(
            student=owner,
            course=course,
            joined_at=datetime.now(timezone.utc),
        )
        self.db.commit()

        missing = self.client.delete(
            "/api/waitlists/unknown-course",
            headers=self.authorization_header(owner.user),
        )
        foreign = self.client.delete(
            f"/api/waitlists/{course.course_id}",
            headers=self.authorization_header(other.user),
        )

        self.assertEqual(missing.status_code, 404)
        self.assertEqual(foreign.status_code, 404)
        self.assertEqual(
            foreign.json()["error"]["code"],
            "WAITLIST_ENTRY_NOT_FOUND",
        )

        entry.waitlist_status = WaitlistStatus.REMOVED.value
        entry.removed_at = datetime.now(timezone.utc)
        self.db.commit()
        inactive = self.client.delete(
            f"/api/waitlists/{course.course_id}",
            headers=self.authorization_header(owner.user),
        )

        self.assertEqual(inactive.status_code, 409)
        self.assertEqual(
            inactive.json()["error"],
            {
                "code": "WAITLIST_ENTRY_NOT_ACTIVE",
                "message": (
                    "Only an active waiting-list entry can be left."
                ),
                "details": {"waitlist_status": "removed"},
            },
        )

    def test_authentication_role_profile_and_request_validation(self):
        suffix = uuid4().hex[:8]
        advisor = self.make_user(suffix=suffix, role="advisor")
        no_profile = self.make_user(
            suffix=f"{suffix}-missing",
            role="student",
        )
        self.db.add_all([advisor, no_profile])
        self.db.commit()

        unauthenticated = self.client.get("/api/waitlists")
        forbidden = self.client.get(
            "/api/waitlists",
            headers=self.authorization_header(advisor),
        )
        missing_profile = self.client.get(
            "/api/waitlists",
            headers=self.authorization_header(no_profile),
        )
        invalid_body = self.client.post(
            "/api/waitlists",
            json={"course_id": "   "},
            headers=self.authorization_header(no_profile),
        )

        self.assertEqual(unauthenticated.status_code, 401)
        self.assertEqual(forbidden.status_code, 403)
        self.assertEqual(missing_profile.status_code, 404)
        self.assertEqual(
            missing_profile.json()["error"]["code"],
            "STUDENT_PROFILE_NOT_FOUND",
        )
        self.assertEqual(invalid_body.status_code, 422)
        self.assertEqual(
            invalid_body.json()["error"]["code"],
            "REQUEST_VALIDATION_ERROR",
        )

    def test_repository_failures_return_safe_api_errors(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(suffix=f"{suffix}-owner")
        self.db.commit()
        headers = self.authorization_header(student.user)

        cases = (
            (
                "app.api.routes.waitlists.list_active_waitlist_entries",
                "get",
                "/api/waitlists",
                None,
            ),
            (
                "app.api.routes.waitlists.join_waitlist",
                "post",
                "/api/waitlists",
                {"course_id": "course-sensitive"},
            ),
            (
                "app.api.routes.waitlists.leave_waitlist",
                "delete",
                "/api/waitlists/course-sensitive",
                None,
            ),
        )

        for target, method, path, payload in cases:
            with self.subTest(method=method):
                with patch(
                    target,
                    side_effect=WaitlistRepositoryError(
                        "sensitive database host and statement"
                    ),
                ):
                    response = self.client.request(
                        method,
                        path,
                        json=payload,
                        headers=headers,
                    )

                self.assertEqual(response.status_code, 500)
                self.assertEqual(
                    response.json()["error"]["code"],
                    "DATABASE_OPERATION_FAILED",
                )
                self.assertNotIn("sensitive", response.text.lower())

    def test_join_and_leave_failures_roll_back_state(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(suffix=f"{suffix}-owner")
        course = self.make_course(suffix=suffix)
        self.db.add(course)
        self.db.flush()
        self.fill_section(course=course, suffix=suffix)
        student_id = student.id
        course_id = course.course_id
        self.db.commit()

        with patch.object(
            self.db,
            "flush",
            side_effect=RuntimeError("sensitive join failure"),
        ):
            with self.assertRaises(WaitlistRepositoryError):
                join_waitlist(
                    self.db,
                    student_id=student_id,
                    course_id=course_id,
                )

        self.assertEqual(self.db.query(WaitlistEntry).count(), 0)
        entry = self.add_waitlist_entry(
            student=student,
            course=course,
            joined_at=datetime.now(timezone.utc),
        )
        entry_id = entry.id
        self.db.commit()

        with patch.object(
            self.db,
            "flush",
            side_effect=RuntimeError("sensitive leave failure"),
        ):
            with self.assertRaises(WaitlistRepositoryError):
                leave_waitlist(
                    self.db,
                    student_id=student_id,
                    course_id=course_id,
                )

        self.db.expire_all()
        stored = self.db.get(WaitlistEntry, entry_id)
        self.assertEqual(stored.waitlist_status, "active")
        self.assertIsNone(stored.removed_at)

    def test_concurrent_duplicate_joins_create_exactly_one_entry(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(suffix=f"{suffix}-owner")
        course = self.make_course(suffix=suffix)
        self.db.add(course)
        self.db.flush()
        self.fill_section(course=course, suffix=suffix)
        student_id = student.id
        course_id = course.course_id
        self.db.commit()
        start = threading.Barrier(3)
        result_lock = threading.Lock()
        outcomes = []

        def join():
            db = self.session_factory()
            try:
                start.wait(timeout=5)
                result = join_waitlist(
                    db,
                    student_id=student_id,
                    course_id=course_id,
                )
                outcome = ("joined", result.queue_position)
            except DuplicateWaitlistEntryError:
                outcome = ("duplicate", None)
            except Exception as error:  # pragma: no cover - diagnostic
                outcome = (type(error).__name__, None)
            finally:
                db.close()

            with result_lock:
                outcomes.append(outcome)

        threads = [threading.Thread(target=join) for _ in range(2)]

        for thread in threads:
            thread.start()

        start.wait(timeout=5)

        for thread in threads:
            thread.join(timeout=10)
            self.assertFalse(thread.is_alive())

        self.assertEqual(
            sorted(outcome[0] for outcome in outcomes),
            ["duplicate", "joined"],
        )
        self.db.expire_all()
        self.assertEqual(self.db.query(WaitlistEntry).count(), 1)

    def test_concurrent_students_receive_distinct_queue_positions(self):
        suffix = uuid4().hex[:8]
        students = [
            self.make_student(suffix=f"{suffix}-{index}")
            for index in range(2)
        ]
        course = self.make_course(suffix=suffix)
        self.db.add(course)
        self.db.flush()
        self.fill_section(course=course, suffix=suffix)
        student_ids = [student.id for student in students]
        course_id = course.course_id
        self.db.commit()
        start = threading.Barrier(3)
        result_lock = threading.Lock()
        positions = []

        def join(student_id):
            db = self.session_factory()
            try:
                start.wait(timeout=5)
                result = join_waitlist(
                    db,
                    student_id=student_id,
                    course_id=course_id,
                )
                position = result.queue_position
            finally:
                db.close()

            with result_lock:
                positions.append(position)

        threads = [
            threading.Thread(target=join, args=(student_id,))
            for student_id in student_ids
        ]

        for thread in threads:
            thread.start()

        start.wait(timeout=5)

        for thread in threads:
            thread.join(timeout=10)
            self.assertFalse(thread.is_alive())

        self.assertEqual(sorted(positions), [1, 2])

    def test_postgresql_lock_queue_and_openapi_contract(self):
        student_id = uuid4()

        with Session() as db:
            lock_statement = locked_waitlist_section_query(
                db,
                course_id="course-lock",
            ).statement
            queue_statement = active_waitlist_entry_query(
                db,
                student_id=student_id,
            ).statement

        lock_sql = str(
            lock_statement.compile(
                dialect=postgresql.dialect(),
                compile_kwargs={"literal_binds": True},
            )
        )
        queue_sql = str(
            queue_statement.compile(
                dialect=postgresql.dialect(),
                compile_kwargs={"literal_binds": True},
            )
        ).lower()

        self.assertIn("FOR UPDATE OF courses", lock_sql)
        self.assertIn("row_number() over", queue_sql)
        self.assertIn("count(waitlist_entries.id) over", queue_sql)
        self.assertIn("waitlist_entries.joined_at asc", queue_sql)

        openapi = coursepilot_app.openapi()
        collection = openapi["paths"]["/api/waitlists"]
        item = openapi["paths"]["/api/waitlists/{course_id}"]
        self.assertTrue(collection["get"]["security"])
        self.assertTrue(collection["post"]["security"])
        self.assertTrue(item["delete"]["security"])
        self.assertTrue(
            collection["post"]["responses"]["201"]["content"]
            ["application/json"]["schema"]["$ref"].endswith(
                "/WaitlistEntryResponse"
            )
        )


if __name__ == "__main__":
    unittest.main()
