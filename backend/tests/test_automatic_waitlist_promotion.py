import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from uuid import uuid4

from sqlalchemy import create_engine, event
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base
from app.models import (
    Advisor,
    AuditLog,
    CompletedCourse,
    CompletionStatus,
    Course,
    CoursePrerequisite,
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
from app.repositories.prerequisite_repository import (
    PrerequisiteRepositoryError,
)
from app.repositories.waitlist_promotion_repository import (
    PromotionSectionNotFoundError,
    WaitlistPromotionRepositoryError,
    locked_active_waitlist_query,
    locked_promotion_section_query,
    promote_next_waitlisted_student,
)
from app.repositories.waitlist_repository import (
    list_active_waitlist_entries,
)


class AutomaticWaitlistPromotionTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary_directory = tempfile.TemporaryDirectory()
        database_path = (
            Path(cls.temporary_directory.name) / "promotion.sqlite"
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

    @classmethod
    def tearDownClass(cls):
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
        capacity: int = 1,
        maximum_credit: int = 18,
        code: str | None = None,
        day: str = "Sunday",
        start_time: str = "09:00",
        end_time: str = "10:00",
    ) -> tuple[Course, Program, Advisor]:
        department = Department(
            department_code=f"D-{suffix}",
            department_name=f"Department {suffix}",
        )
        program = Program(
            department=department,
            program_code=f"P-{suffix}",
            program_name=f"Program {suffix}",
            minimum_credit=0,
            maximum_credit=maximum_credit,
        )
        advisor = Advisor(
            user=self.make_user(suffix=suffix, role="advisor"),
            department=department,
            employee_number=f"ADV-{suffix}",
        )
        course = self.make_course(
            suffix=suffix,
            capacity=capacity,
            code=code,
            day=day,
            start_time=start_time,
            end_time=end_time,
        )
        self.db.add_all([program, advisor, course])
        self.db.flush()
        return course, program, advisor

    @staticmethod
    def make_course(
        *,
        suffix: str,
        capacity: int = 1,
        code: str | None = None,
        day: str = "Sunday",
        start_time: str = "09:00",
        end_time: str = "10:00",
    ) -> Course:
        return Course(
            course_id=f"promotion-{suffix}",
            code=code or f"CSE {suffix}",
            title=f"Promotion Course {suffix}",
            department="CSE",
            semester="Fall 2026",
            instructor="Dr. Promotion",
            credits=3,
            capacity=capacity,
            available_seats=0,
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

    def make_student(
        self,
        *,
        program: Program,
        advisor: Advisor,
        suffix: str,
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

    def add_waitlist_entry(
        self,
        *,
        student: Student,
        course: Course,
        joined_at: datetime,
    ) -> WaitlistEntry:
        entry = WaitlistEntry(
            student=student,
            section=course,
            waitlist_status=WaitlistStatus.ACTIVE.value,
            joined_at=joined_at,
        )
        self.db.add(entry)
        self.db.flush()
        return entry

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

    def test_promotion_atomically_updates_all_required_records(self):
        suffix = uuid4().hex[:8]
        course, program, advisor = self.make_context(suffix=suffix)
        students = [
            self.make_student(
                program=program,
                advisor=advisor,
                suffix=f"{suffix}-{index}",
            )
            for index in range(2)
        ]
        first_time = datetime(2026, 8, 12, 8, 0, tzinfo=timezone.utc)
        entries = [
            self.add_waitlist_entry(
                student=student,
                course=course,
                joined_at=first_time + timedelta(minutes=index),
            )
            for index, student in enumerate(students)
        ]
        course_id = course.course_id
        self.db.commit()

        result = promote_next_waitlisted_student(
            self.db,
            course_id=course_id,
        )

        self.assertTrue(result.promoted)
        self.assertEqual(result.outcome, "promoted")
        self.assertEqual(result.waitlist_entry_id, entries[0].id)
        self.assertEqual(result.student_id, students[0].id)
        self.assertEqual(result.registration_status, "approved")
        self.assertEqual(result.waitlist_status, "promoted")
        self.assertEqual(result.approved_enrollment, 1)
        self.assertEqual(result.available_seats, 0)
        self.assertEqual(result.expired_waitlist_entry_ids, [])

        self.db.expire_all()
        registration = self.db.get(Registration, result.registration_id)
        promoted_entry = self.db.get(WaitlistEntry, entries[0].id)
        notification = self.db.get(Notification, result.notification_id)
        audit_log = self.db.get(AuditLog, result.audit_log_id)

        self.assertEqual(registration.registration_status, "approved")
        self.assertEqual(registration.student_id, students[0].id)
        self.assertIsNotNone(registration.submitted_at)
        self.assertEqual(promoted_entry.waitlist_status, "promoted")
        self.assertIsNotNone(promoted_entry.promoted_at)
        self.assertEqual(notification.user_id, students[0].user_id)
        self.assertEqual(notification.notification_type, "waitlist_promotion")
        self.assertIn(course.code, notification.message)
        self.assertEqual(
            audit_log.action_type,
            "automatic_waitlist_promotion",
        )
        self.assertEqual(audit_log.entity_id, entries[0].id)
        details = json.loads(audit_log.action_details)
        self.assertEqual(details["registration_id"], str(registration.id))
        self.assertEqual(details["waitlist_status"], "promoted")

        remaining = list_active_waitlist_entries(
            self.db,
            student_id=students[1].id,
        )
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0].queue_position, 1)
        self.assertEqual(remaining[0].total_waiting, 1)

    def test_full_section_does_not_change_the_queue(self):
        suffix = uuid4().hex[:8]
        course, program, advisor = self.make_context(suffix=suffix)
        enrolled = self.make_student(
            program=program,
            advisor=advisor,
            suffix=f"{suffix}-enrolled",
        )
        waiting = self.make_student(
            program=program,
            advisor=advisor,
            suffix=f"{suffix}-waiting",
        )
        self.add_registration(
            student=enrolled,
            course=course,
            registration_status=RegistrationStatus.APPROVED.value,
        )
        entry = self.add_waitlist_entry(
            student=waiting,
            course=course,
            joined_at=datetime.now(timezone.utc),
        )
        self.db.commit()

        result = promote_next_waitlisted_student(
            self.db,
            course_id=course.course_id,
        )

        self.assertFalse(result.promoted)
        self.assertEqual(result.outcome, "section_full")
        self.assertEqual(result.approved_enrollment, 1)
        self.assertEqual(result.available_seats, 0)
        self.db.expire_all()
        self.assertEqual(
            self.db.get(WaitlistEntry, entry.id).waitlist_status,
            "active",
        )
        self.assertEqual(self.db.query(Notification).count(), 0)
        self.assertEqual(self.db.query(AuditLog).count(), 0)

    def test_empty_queue_and_missing_section_are_distinct(self):
        suffix = uuid4().hex[:8]
        course, _, _ = self.make_context(suffix=suffix)
        course_id = course.course_id
        self.db.commit()

        result = promote_next_waitlisted_student(
            self.db,
            course_id=course_id,
        )

        self.assertFalse(result.promoted)
        self.assertEqual(result.outcome, "queue_empty")
        self.assertEqual(result.available_seats, 1)

        with self.assertRaises(PromotionSectionNotFoundError):
            promote_next_waitlisted_student(
                self.db,
                course_id="unknown-course",
            )

    def test_only_one_student_is_promoted_per_available_seat_event(self):
        suffix = uuid4().hex[:8]
        course, program, advisor = self.make_context(
            suffix=suffix,
            capacity=3,
        )
        students = [
            self.make_student(
                program=program,
                advisor=advisor,
                suffix=f"{suffix}-{index}",
            )
            for index in range(2)
        ]

        for index, student in enumerate(students):
            self.add_waitlist_entry(
                student=student,
                course=course,
                joined_at=datetime.now(timezone.utc)
                + timedelta(microseconds=index),
            )

        self.db.commit()

        result = promote_next_waitlisted_student(
            self.db,
            course_id=course.course_id,
        )

        self.assertTrue(result.promoted)
        self.assertEqual(result.approved_enrollment, 1)
        self.assertEqual(result.available_seats, 2)
        self.assertEqual(
            self.db.query(WaitlistEntry)
            .filter(WaitlistEntry.waitlist_status == "active")
            .count(),
            1,
        )

    def test_ineligible_head_expires_and_next_student_is_promoted(self):
        suffix = uuid4().hex[:8]
        course, program, advisor = self.make_context(
            suffix=suffix,
            code="CSE 201",
        )
        prerequisite = self.make_course(
            suffix=f"{suffix}-prerequisite",
            code="CSE 101",
        )
        self.db.add(prerequisite)
        self.db.flush()
        self.db.add(
            CoursePrerequisite(
                course=course,
                prerequisite_course=prerequisite,
                minimum_grade="C",
            )
        )
        first = self.make_student(
            program=program,
            advisor=advisor,
            suffix=f"{suffix}-first",
        )
        second = self.make_student(
            program=program,
            advisor=advisor,
            suffix=f"{suffix}-second",
        )
        self.db.add(
            CompletedCourse(
                student=second,
                course=prerequisite,
                grade="B",
                completion_status=CompletionStatus.COMPLETED.value,
                completed_at=date(2026, 5, 30),
            )
        )
        first_time = datetime(2026, 8, 12, 8, 0, tzinfo=timezone.utc)
        first_entry = self.add_waitlist_entry(
            student=first,
            course=course,
            joined_at=first_time,
        )
        second_entry = self.add_waitlist_entry(
            student=second,
            course=course,
            joined_at=first_time + timedelta(minutes=1),
        )
        self.db.commit()

        result = promote_next_waitlisted_student(
            self.db,
            course_id=course.course_id,
        )

        self.assertEqual(result.waitlist_entry_id, second_entry.id)
        self.assertEqual(
            result.expired_waitlist_entry_ids,
            [first_entry.id],
        )
        self.db.expire_all()
        stored_first = self.db.get(WaitlistEntry, first_entry.id)
        self.assertEqual(stored_first.waitlist_status, "expired")
        self.assertIsNotNone(stored_first.removed_at)

    def test_schedule_conflict_makes_candidate_ineligible(self):
        suffix = uuid4().hex[:8]
        course, program, advisor = self.make_context(
            suffix=suffix,
            day="Monday",
            start_time="09:00",
            end_time="10:30",
        )
        conflict = self.make_course(
            suffix=f"{suffix}-conflict",
            code="CSE 999",
            day="Monday",
            start_time="10:00",
            end_time="11:00",
        )
        self.db.add(conflict)
        student = self.make_student(
            program=program,
            advisor=advisor,
            suffix=f"{suffix}-student",
        )
        self.add_registration(
            student=student,
            course=conflict,
            registration_status=RegistrationStatus.APPROVED.value,
        )
        entry = self.add_waitlist_entry(
            student=student,
            course=course,
            joined_at=datetime.now(timezone.utc),
        )
        self.db.commit()

        result = promote_next_waitlisted_student(
            self.db,
            course_id=course.course_id,
        )

        self.assertFalse(result.promoted)
        self.assertEqual(result.outcome, "no_eligible_student")
        self.assertEqual(result.expired_waitlist_entry_ids, [entry.id])
        self.assertEqual(self.db.query(Registration).count(), 1)
        self.assertEqual(self.db.query(Notification).count(), 0)

    def test_completed_course_and_maximum_credit_are_revalidated(self):
        suffix = uuid4().hex[:8]
        course, program, advisor = self.make_context(
            suffix=suffix,
            maximum_credit=3,
            code="CSE 301",
        )
        historical = self.make_course(
            suffix=f"{suffix}-historical",
            code="  cse   301 ",
        )
        other = self.make_course(
            suffix=f"{suffix}-other",
            code="CSE 401",
        )
        self.db.add_all([historical, other])
        completed_student = self.make_student(
            program=program,
            advisor=advisor,
            suffix=f"{suffix}-completed",
        )
        over_limit_student = self.make_student(
            program=program,
            advisor=advisor,
            suffix=f"{suffix}-limit",
        )
        self.db.add(
            CompletedCourse(
                student=completed_student,
                course=historical,
                grade="A",
                completion_status=CompletionStatus.COMPLETED.value,
                completed_at=date(2026, 5, 30),
            )
        )
        self.add_registration(
            student=over_limit_student,
            course=other,
            registration_status=RegistrationStatus.APPROVED.value,
        )
        first_time = datetime(2026, 8, 12, 8, 0, tzinfo=timezone.utc)
        entries = [
            self.add_waitlist_entry(
                student=student,
                course=course,
                joined_at=first_time + timedelta(minutes=index),
            )
            for index, student in enumerate(
                [completed_student, over_limit_student]
            )
        ]
        self.db.commit()

        result = promote_next_waitlisted_student(
            self.db,
            course_id=course.course_id,
        )

        self.assertFalse(result.promoted)
        self.assertEqual(result.outcome, "no_eligible_student")
        self.assertEqual(
            result.expired_waitlist_entry_ids,
            [entry.id for entry in entries],
        )
        self.assertEqual(self.db.query(Notification).count(), 0)
        self.assertEqual(self.db.query(AuditLog).count(), 0)

    def test_failed_commit_rolls_back_every_promotion_record(self):
        suffix = uuid4().hex[:8]
        course, program, advisor = self.make_context(suffix=suffix)
        student = self.make_student(
            program=program,
            advisor=advisor,
            suffix=f"{suffix}-student",
        )
        entry = self.add_waitlist_entry(
            student=student,
            course=course,
            joined_at=datetime.now(timezone.utc),
        )
        course_id = course.course_id
        entry_id = entry.id
        self.db.commit()

        with patch.object(
            self.db,
            "commit",
            side_effect=RuntimeError("sensitive commit failure"),
        ):
            with self.assertRaises(WaitlistPromotionRepositoryError):
                promote_next_waitlisted_student(
                    self.db,
                    course_id=course_id,
                )

        self.db.expire_all()
        stored = self.db.get(WaitlistEntry, entry_id)
        self.assertEqual(stored.waitlist_status, "active")
        self.assertIsNone(stored.promoted_at)
        self.assertEqual(self.db.query(Registration).count(), 0)
        self.assertEqual(self.db.query(Notification).count(), 0)
        self.assertEqual(self.db.query(AuditLog).count(), 0)

    def test_dependency_failure_is_wrapped_and_queue_is_unchanged(self):
        suffix = uuid4().hex[:8]
        course, program, advisor = self.make_context(suffix=suffix)
        student = self.make_student(
            program=program,
            advisor=advisor,
            suffix=f"{suffix}-student",
        )
        entry = self.add_waitlist_entry(
            student=student,
            course=course,
            joined_at=datetime.now(timezone.utc),
        )
        course_id = course.course_id
        entry_id = entry.id
        self.db.commit()

        with patch(
            "app.repositories.waitlist_promotion_repository."
            "require_prerequisites_met",
            side_effect=PrerequisiteRepositoryError(
                "sensitive database statement"
            ),
        ):
            with self.assertRaises(WaitlistPromotionRepositoryError):
                promote_next_waitlisted_student(
                    self.db,
                    course_id=course_id,
                )

        self.db.expire_all()
        self.assertEqual(
            self.db.get(WaitlistEntry, entry_id).waitlist_status,
            "active",
        )
        self.assertEqual(self.db.query(Registration).count(), 0)

    def test_concurrent_processing_cannot_fill_one_seat_twice(self):
        suffix = uuid4().hex[:8]
        course, program, advisor = self.make_context(suffix=suffix)
        students = [
            self.make_student(
                program=program,
                advisor=advisor,
                suffix=f"{suffix}-{index}",
            )
            for index in range(2)
        ]
        first_time = datetime(2026, 8, 12, 8, 0, tzinfo=timezone.utc)

        for index, student in enumerate(students):
            self.add_waitlist_entry(
                student=student,
                course=course,
                joined_at=first_time + timedelta(minutes=index),
            )

        course_id = course.course_id
        self.db.commit()
        start = threading.Barrier(3)
        result_lock = threading.Lock()
        outcomes = []

        def promote():
            db = self.session_factory()
            try:
                start.wait(timeout=5)
                result = promote_next_waitlisted_student(
                    db,
                    course_id=course_id,
                )
                outcome = result.outcome
            except Exception as error:  # pragma: no cover - diagnostic
                outcome = type(error).__name__
            finally:
                db.close()

            with result_lock:
                outcomes.append(outcome)

        threads = [threading.Thread(target=promote) for _ in range(2)]

        for thread in threads:
            thread.start()

        start.wait(timeout=5)

        for thread in threads:
            thread.join(timeout=10)
            self.assertFalse(thread.is_alive())

        self.assertEqual(sorted(outcomes), ["promoted", "section_full"])
        self.db.expire_all()
        self.assertEqual(
            self.db.query(Registration)
            .filter(Registration.registration_status == "approved")
            .count(),
            1,
        )
        self.assertEqual(
            self.db.query(WaitlistEntry)
            .filter(WaitlistEntry.waitlist_status == "promoted")
            .count(),
            1,
        )
        self.assertEqual(self.db.query(Notification).count(), 1)
        self.assertEqual(self.db.query(AuditLog).count(), 1)

    def test_postgresql_queries_lock_section_then_fifo_entries(self):
        with Session() as db:
            section_statement = locked_promotion_section_query(
                db,
                course_id="promotion-lock",
            ).statement
            queue_statement = locked_active_waitlist_query(
                db,
                section_id=42,
            ).statement

        section_sql = str(
            section_statement.compile(
                dialect=postgresql.dialect(),
                compile_kwargs={"literal_binds": True},
            )
        )
        queue_sql = str(
            queue_statement.compile(
                dialect=postgresql.dialect(),
                compile_kwargs={"literal_binds": True},
            )
        )

        self.assertIn("FOR UPDATE OF courses", section_sql)
        self.assertIn("FOR UPDATE OF waitlist_entries", queue_sql)
        self.assertIn("waitlist_entries.joined_at ASC", queue_sql)
        self.assertIn("waitlist_entries.id ASC", queue_sql)


if __name__ == "__main__":
    unittest.main()
