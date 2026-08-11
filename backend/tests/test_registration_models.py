import unittest
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import create_engine, event, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.database import Base
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


class RegistrationModelsTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:")

        @event.listens_for(cls.engine, "connect")
        def enable_foreign_keys(dbapi_connection, _):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        Base.metadata.create_all(cls.engine)
        cls.session_factory = sessionmaker(bind=cls.engine)

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(cls.engine)
        cls.engine.dispose()

    def setUp(self):
        self.db = self.session_factory()

    def tearDown(self):
        self.db.rollback()
        self.db.close()

    @staticmethod
    def make_user(email: str, full_name: str, role: str) -> User:
        return User(
            email=email,
            password_hash="test-password-hash",
            full_name=full_name,
            role=role,
        )

    def make_academic_context(self, suffix: str):
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
        advisor_user = self.make_user(
            f"advisor-{suffix}@example.com",
            f"Advisor {suffix}",
            "advisor",
        )
        advisor = Advisor(
            user=advisor_user,
            department=department,
            employee_number=f"ADV-{suffix}",
        )
        student_user = self.make_user(
            f"student-{suffix}@example.com",
            f"Student {suffix}",
            "student",
        )
        student = Student(
            user=student_user,
            program=program,
            advisor=advisor,
            student_number=f"STU-{suffix}",
            current_trimester=3,
        )
        section = Course(
            course_id=f"course-{suffix}",
            code=f"CSE {suffix}",
            title=f"Course {suffix}",
            department="CSE",
            semester="Fall 2026",
            instructor=f"Instructor {suffix}",
            credits=3,
            capacity=40,
            available_seats=10,
            is_mandatory=False,
            section="A",
        )

        self.db.add_all([student, section])
        self.db.flush()

        return student, advisor, section, student_user, advisor_user

    def test_tables_foreign_keys_and_uniqueness_match_erd(self):
        inspector = inspect(self.engine)
        expected_tables = {
            "registrations",
            "waitlist_entries",
            "notifications",
            "audit_logs",
        }
        self.assertTrue(
            expected_tables.issubset(set(inspector.get_table_names()))
        )

        expected_foreign_keys = {
            "registrations": {
                "student_id": "students",
                "section_id": "courses",
                "reviewed_by": "advisors",
            },
            "waitlist_entries": {
                "student_id": "students",
                "section_id": "courses",
            },
            "notifications": {"user_id": "users"},
            "audit_logs": {"user_id": "users"},
        }

        for table_name, expected in expected_foreign_keys.items():
            actual = {
                foreign_key["constrained_columns"][0]: foreign_key[
                    "referred_table"
                ]
                for foreign_key in inspector.get_foreign_keys(table_name)
            }
            self.assertEqual(actual, expected)

        registration_constraints = {
            tuple(constraint["column_names"])
            for constraint in inspector.get_unique_constraints(
                "registrations"
            )
        }
        waitlist_constraints = {
            tuple(constraint["column_names"])
            for constraint in inspector.get_unique_constraints(
                "waitlist_entries"
            )
        }
        self.assertIn(
            ("student_id", "section_id"),
            registration_constraints,
        )
        self.assertIn(
            ("student_id", "section_id"),
            waitlist_constraints,
        )

    def test_records_can_be_stored_and_queried_by_state(self):
        (
            student,
            advisor,
            section,
            student_user,
            advisor_user,
        ) = self.make_academic_context("query")
        now = datetime.now(timezone.utc)
        registration = Registration(
            student=student,
            section=section,
            reviewer=advisor,
            registration_status=RegistrationStatus.APPROVED.value,
            advisor_comment="Approved",
            submitted_at=now,
            reviewed_at=now,
        )
        waitlist_entry = WaitlistEntry(
            student=student,
            section=section,
            waitlist_status=WaitlistStatus.ACTIVE.value,
        )
        self.db.add_all([registration, waitlist_entry])
        self.db.flush()

        notification = Notification(
            user=student_user,
            notification_type="registration-approved",
            title="Registration approved",
            message="Your registration has been approved.",
        )
        audit_log = AuditLog(
            user=advisor_user,
            action_type="registration-approved",
            entity_type="registration",
            entity_id=registration.id,
            action_details="Approved during model test.",
        )
        self.db.add_all([notification, audit_log])
        self.db.flush()

        stored_registration = (
            self.db.query(Registration)
            .filter_by(
                student_id=student.id,
                registration_status=RegistrationStatus.APPROVED.value,
            )
            .one()
        )
        active_waitlist = (
            self.db.query(WaitlistEntry)
            .filter_by(
                section_id=section.id,
                waitlist_status=WaitlistStatus.ACTIVE.value,
            )
            .order_by(WaitlistEntry.joined_at)
            .one()
        )
        unread_notification = (
            self.db.query(Notification)
            .filter_by(user_id=student_user.id, is_read=False)
            .one()
        )
        stored_audit_log = (
            self.db.query(AuditLog)
            .filter_by(
                entity_type="registration",
                entity_id=registration.id,
            )
            .one()
        )

        self.assertIs(stored_registration, registration)
        self.assertIs(active_waitlist, waitlist_entry)
        self.assertIs(unread_notification, notification)
        self.assertIs(stored_audit_log, audit_log)
        self.assertIn(registration, student.registrations)
        self.assertIn(registration, advisor.reviewed_registrations)
        self.assertIn(waitlist_entry, section.waitlist_entries)
        self.assertIn(notification, student_user.notifications)
        self.assertIn(audit_log, advisor_user.audit_logs)

    def test_defaults_and_uuid_ids_are_populated(self):
        student, _, section, student_user, advisor_user = (
            self.make_academic_context("defaults")
        )
        registration = Registration(
            student=student,
            section=section,
        )
        waitlist_entry = WaitlistEntry(
            student=student,
            section=section,
        )
        notification = Notification(
            user=student_user,
            notification_type="registration-submitted",
            title="Registration submitted",
            message="Your registration was submitted.",
        )
        audit_log = AuditLog(
            user=advisor_user,
            action_type="student-profile-viewed",
            entity_type="student",
            entity_id=student.id,
        )
        self.db.add_all(
            [registration, waitlist_entry, notification, audit_log]
        )
        self.db.flush()

        for record in (
            registration,
            waitlist_entry,
            notification,
            audit_log,
        ):
            self.assertIsInstance(record.id, UUID)

        self.assertEqual(
            registration.registration_status,
            RegistrationStatus.DRAFT.value,
        )
        self.assertEqual(
            waitlist_entry.waitlist_status,
            WaitlistStatus.ACTIVE.value,
        )
        self.assertFalse(notification.is_read)
        self.assertIsNotNone(registration.updated_at)
        self.assertIsNotNone(waitlist_entry.joined_at)
        self.assertIsNotNone(notification.created_at)
        self.assertIsNotNone(audit_log.created_at)

    def test_duplicate_student_registration_is_rejected(self):
        student, _, section, _, _ = self.make_academic_context(
            "duplicate-registration"
        )
        self.db.add(
            Registration(student=student, section=section)
        )
        self.db.flush()
        self.db.add(
            Registration(student=student, section=section)
        )

        with self.assertRaises(IntegrityError):
            self.db.flush()

    def test_duplicate_waitlist_entry_is_rejected(self):
        student, _, section, _, _ = self.make_academic_context(
            "duplicate-waitlist"
        )
        self.db.add(
            WaitlistEntry(student=student, section=section)
        )
        self.db.flush()
        self.db.add(
            WaitlistEntry(student=student, section=section)
        )

        with self.assertRaises(IntegrityError):
            self.db.flush()

    def test_invalid_registration_status_is_rejected(self):
        student, _, section, _, _ = self.make_academic_context(
            "invalid-registration"
        )
        self.db.add(
            Registration(
                student=student,
                section=section,
                registration_status="queued",
            )
        )

        with self.assertRaises(IntegrityError):
            self.db.flush()

    def test_invalid_waitlist_status_is_rejected(self):
        student, _, section, _, _ = self.make_academic_context(
            "invalid-waitlist"
        )
        self.db.add(
            WaitlistEntry(
                student=student,
                section=section,
                waitlist_status="waiting",
            )
        )

        with self.assertRaises(IntegrityError):
            self.db.flush()


if __name__ == "__main__":
    unittest.main()
