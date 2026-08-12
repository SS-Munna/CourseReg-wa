import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from sqlalchemy import create_engine, event
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base
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
from app.repositories.seat_allocation_repository import (
    RegistrationNotFoundError,
    RegistrationNotPendingError,
    SeatAllocationRepositoryError,
    SectionFullError,
    allocate_registration_seat,
    locked_section_for_registration_query,
)


class SafeSeatAllocationTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary_directory = tempfile.TemporaryDirectory()
        database_path = (
            Path(cls.temporary_directory.name) / "seat-allocation.sqlite"
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
        capacity: int,
    ) -> tuple[Course, Program, Advisor]:
        suffix = uuid4().hex[:8]
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
        course = Course(
            course_id=f"allocation-{suffix}",
            code=f"CSE {suffix}",
            title="Safe Allocation",
            department="CSE",
            semester="Fall 2026",
            instructor="Dr. Capacity",
            credits=3,
            capacity=capacity,
            available_seats=capacity,
            is_mandatory=False,
            prerequisites=[],
            section="A",
            schedule=[],
        )
        self.db.add_all([advisor, program, course])
        self.db.flush()
        return course, program, advisor

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

    def add_registration(
        self,
        *,
        course: Course,
        program: Program,
        advisor: Advisor,
        registration_status: str,
        suffix: str,
    ) -> Registration:
        student = self.make_student(
            program=program,
            advisor=advisor,
            suffix=suffix,
        )
        registration = Registration(
            student=student,
            section=course,
            registration_status=registration_status,
        )
        self.db.add(registration)
        self.db.flush()
        return registration

    def test_pending_registration_allocates_the_final_seat(self):
        course, program, advisor = self.make_context(capacity=2)
        self.add_registration(
            course=course,
            program=program,
            advisor=advisor,
            registration_status=RegistrationStatus.APPROVED.value,
            suffix="existing",
        )
        pending = self.add_registration(
            course=course,
            program=program,
            advisor=advisor,
            registration_status=RegistrationStatus.PENDING.value,
            suffix="pending",
        )
        pending_id = pending.id
        self.db.commit()

        result = allocate_registration_seat(
            self.db,
            registration_id=pending_id,
        )

        self.assertTrue(result.newly_allocated)
        self.assertEqual(result.registration_status, "approved")
        self.assertEqual(result.approved_enrollment, 2)
        self.assertEqual(result.capacity, 2)
        self.assertEqual(result.available_seats, 0)
        self.assertEqual(result.course_id, course.course_id)
        self.db.expire_all()
        stored = self.db.get(Registration, pending_id)
        self.assertEqual(stored.registration_status, "approved")

    def test_second_request_cannot_allocate_the_same_final_seat(self):
        course, program, advisor = self.make_context(capacity=1)
        first = self.add_registration(
            course=course,
            program=program,
            advisor=advisor,
            registration_status=RegistrationStatus.PENDING.value,
            suffix="first",
        )
        second = self.add_registration(
            course=course,
            program=program,
            advisor=advisor,
            registration_status=RegistrationStatus.PENDING.value,
            suffix="second",
        )
        first_id = first.id
        second_id = second.id
        self.db.commit()

        first_result = allocate_registration_seat(
            self.db,
            registration_id=first_id,
        )

        with self.assertRaises(SectionFullError) as context:
            allocate_registration_seat(
                self.db,
                registration_id=second_id,
            )

        self.assertEqual(first_result.available_seats, 0)
        self.assertEqual(context.exception.capacity, 1)
        self.assertEqual(context.exception.approved_enrollment, 1)
        self.db.expire_all()
        statuses = {
            registration.id: registration.registration_status
            for registration in self.db.query(Registration).all()
        }
        self.assertEqual(statuses[first_id], "approved")
        self.assertEqual(statuses[second_id], "pending")

    def test_concurrent_requests_cannot_allocate_the_same_final_seat(self):
        course, program, advisor = self.make_context(capacity=1)
        registrations = [
            self.add_registration(
                course=course,
                program=program,
                advisor=advisor,
                registration_status=RegistrationStatus.PENDING.value,
                suffix=f"concurrent-{index}",
            )
            for index in range(2)
        ]
        registration_ids = [registration.id for registration in registrations]
        self.db.commit()
        start = threading.Barrier(3)
        outcome_lock = threading.Lock()
        outcomes = []

        def allocate(registration_id):
            db = self.session_factory()
            try:
                start.wait(timeout=5)
                result = allocate_registration_seat(
                    db,
                    registration_id=registration_id,
                )
                outcome = ("approved", result.registration_id)
            except SectionFullError:
                outcome = ("full", registration_id)
            except Exception as error:  # pragma: no cover - diagnostic
                outcome = (type(error).__name__, registration_id)
            finally:
                db.close()

            with outcome_lock:
                outcomes.append(outcome)

        threads = [
            threading.Thread(target=allocate, args=(registration_id,))
            for registration_id in registration_ids
        ]

        for thread in threads:
            thread.start()

        start.wait(timeout=5)

        for thread in threads:
            thread.join(timeout=10)
            self.assertFalse(thread.is_alive())

        self.assertEqual(
            sorted(outcome[0] for outcome in outcomes),
            ["approved", "full"],
        )
        self.db.expire_all()
        stored_statuses = sorted(
            registration.registration_status
            for registration in self.db.query(Registration).all()
        )
        self.assertEqual(stored_statuses, ["approved", "pending"])

    def test_only_approved_rows_consume_capacity(self):
        course, program, advisor = self.make_context(capacity=1)

        for index, registration_status in enumerate(
            (
                RegistrationStatus.DRAFT.value,
                RegistrationStatus.REJECTED.value,
                RegistrationStatus.DROPPED.value,
            )
        ):
            self.add_registration(
                course=course,
                program=program,
                advisor=advisor,
                registration_status=registration_status,
                suffix=f"inactive-{index}",
            )

        pending = self.add_registration(
            course=course,
            program=program,
            advisor=advisor,
            registration_status=RegistrationStatus.PENDING.value,
            suffix="eligible",
        )
        pending_id = pending.id
        self.db.commit()

        result = allocate_registration_seat(
            self.db,
            registration_id=pending_id,
        )

        self.assertEqual(result.approved_enrollment, 1)
        self.assertEqual(result.available_seats, 0)

    def test_approved_retry_is_idempotent(self):
        course, program, advisor = self.make_context(capacity=1)
        approved = self.add_registration(
            course=course,
            program=program,
            advisor=advisor,
            registration_status=RegistrationStatus.APPROVED.value,
            suffix="approved",
        )
        approved_id = approved.id
        self.db.commit()

        result = allocate_registration_seat(
            self.db,
            registration_id=approved_id,
        )

        self.assertFalse(result.newly_allocated)
        self.assertEqual(result.approved_enrollment, 1)
        self.assertEqual(
            self.db.query(Registration)
            .filter(
                Registration.registration_status
                == RegistrationStatus.APPROVED.value
            )
            .count(),
            1,
        )

    def test_non_pending_registration_is_rejected_without_mutation(self):
        course, program, advisor = self.make_context(capacity=3)
        registrations = {}

        for registration_status in (
            RegistrationStatus.DRAFT.value,
            RegistrationStatus.REJECTED.value,
            RegistrationStatus.DROPPED.value,
        ):
            registration = self.add_registration(
                course=course,
                program=program,
                advisor=advisor,
                registration_status=registration_status,
                suffix=registration_status,
            )
            registrations[registration_status] = registration.id

        self.db.commit()

        for registration_status, registration_id in registrations.items():
            with self.subTest(registration_status=registration_status):
                with self.assertRaises(
                    RegistrationNotPendingError
                ) as context:
                    allocate_registration_seat(
                        self.db,
                        registration_id=registration_id,
                    )

                self.assertEqual(
                    context.exception.registration_status,
                    registration_status,
                )
                self.db.expire_all()
                self.assertEqual(
                    self.db.get(
                        Registration,
                        registration_id,
                    ).registration_status,
                    registration_status,
                )

    def test_missing_registration_is_reported(self):
        with self.assertRaises(RegistrationNotFoundError):
            allocate_registration_seat(
                self.db,
                registration_id=uuid4(),
            )

    def test_unexpected_failure_rolls_back_and_is_wrapped(self):
        course, program, advisor = self.make_context(capacity=1)
        pending = self.add_registration(
            course=course,
            program=program,
            advisor=advisor,
            registration_status=RegistrationStatus.PENDING.value,
            suffix="rollback",
        )
        pending_id = pending.id
        self.db.commit()

        with patch.object(
            self.db,
            "flush",
            side_effect=RuntimeError("sensitive database details"),
        ):
            with self.assertRaises(
                SeatAllocationRepositoryError
            ) as context:
                allocate_registration_seat(
                    self.db,
                    registration_id=pending_id,
                )

        self.assertIn("sensitive database details", str(context.exception))
        self.db.expire_all()
        self.assertEqual(
            self.db.get(Registration, pending_id).registration_status,
            RegistrationStatus.PENDING.value,
        )

    def test_section_lock_query_compiles_for_postgresql(self):
        registration_id = uuid4()

        with Session() as db:
            statement = locked_section_for_registration_query(
                db,
                registration_id=registration_id,
            ).statement

        sql = str(
            statement.compile(
                dialect=postgresql.dialect(),
                compile_kwargs={"literal_binds": True},
            )
        )

        self.assertIn("JOIN registrations", sql)
        self.assertIn("registrations.id", sql)
        self.assertIn("FOR UPDATE OF courses", sql)


if __name__ == "__main__":
    unittest.main()
