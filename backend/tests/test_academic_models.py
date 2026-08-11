import unittest
from datetime import date
from uuid import UUID

from sqlalchemy import create_engine, event, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import (
    Advisor,
    Department,
    Instructor,
    Program,
    Semester,
    Student,
    User,
)


class AcademicModelsTestCase(unittest.TestCase):
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

    def test_core_tables_and_foreign_keys_match_erd(self):
        inspector = inspect(self.engine)

        expected_tables = {
            "users",
            "departments",
            "programs",
            "students",
            "advisors",
            "instructors",
            "semesters",
        }
        self.assertTrue(
            expected_tables.issubset(set(inspector.get_table_names()))
        )

        expected_foreign_keys = {
            "programs": {"department_id": "departments"},
            "students": {
                "user_id": "users",
                "program_id": "programs",
                "advisor_id": "advisors",
            },
            "advisors": {
                "user_id": "users",
                "department_id": "departments",
            },
            "instructors": {
                "user_id": "users",
                "department_id": "departments",
            },
        }

        for table_name, expected in expected_foreign_keys.items():
            actual = {
                foreign_key["constrained_columns"][0]: foreign_key[
                    "referred_table"
                ]
                for foreign_key in inspector.get_foreign_keys(table_name)
            }
            self.assertEqual(actual, expected)

    def test_core_relationships_and_uuid_ids(self):
        department = Department(
            department_code="CSE",
            department_name="Computer Science and Engineering",
        )
        program = Program(
            department=department,
            program_code="BSC-CSE",
            program_name="BSc in CSE",
            minimum_credit=9,
            maximum_credit=18,
        )
        advisor_user = self.make_user(
            "advisor@example.com",
            "Academic Advisor",
            "advisor",
        )
        advisor = Advisor(
            user=advisor_user,
            department=department,
            employee_number="ADV-001",
        )
        instructor_user = self.make_user(
            "instructor@example.com",
            "Course Instructor",
            "instructor",
        )
        instructor = Instructor(
            user=instructor_user,
            department=department,
            employee_number="INS-001",
        )
        student_user = self.make_user(
            "student@example.com",
            "Student User",
            "student",
        )
        student = Student(
            user=student_user,
            program=program,
            advisor=advisor,
            student_number="STU-001",
            current_trimester=3,
        )

        self.db.add_all([instructor, student])
        self.db.flush()

        for entity in (
            department,
            program,
            advisor_user,
            advisor,
            instructor_user,
            instructor,
            student_user,
            student,
        ):
            self.assertIsInstance(entity.id, UUID)

        self.assertIs(student.user.student, student)
        self.assertIs(student.program, program)
        self.assertIn(student, advisor.students)
        self.assertIn(program, department.programs)
        self.assertIn(advisor, department.advisors)
        self.assertIn(instructor, department.instructors)

    def test_user_defaults_and_unique_email(self):
        first_user = self.make_user(
            "duplicate@example.com",
            "First User",
            "student",
        )
        second_user = self.make_user(
            "duplicate@example.com",
            "Second User",
            "student",
        )

        self.db.add_all([first_user, second_user])

        with self.assertRaises(IntegrityError):
            self.db.flush()

        self.db.rollback()
        active_user = self.make_user(
            "active@example.com",
            "Active User",
            "student",
        )
        self.db.add(active_user)
        self.db.flush()

        self.assertEqual(active_user.account_status, "active")
        self.assertIsNotNone(active_user.created_at)
        self.assertIsNotNone(active_user.updated_at)

    def test_invalid_program_credit_range_is_rejected(self):
        department = Department(
            department_code="EEE",
            department_name="Electrical and Electronic Engineering",
        )
        program = Program(
            department=department,
            program_code="BSC-EEE",
            program_name="BSc in EEE",
            minimum_credit=18,
            maximum_credit=12,
        )

        self.db.add(program)

        with self.assertRaises(IntegrityError):
            self.db.flush()

    def test_invalid_semester_date_range_is_rejected(self):
        semester = Semester(
            semester_name="Fall",
            academic_year=2026,
            start_date=date(2026, 12, 1),
            end_date=date(2026, 9, 1),
        )
        self.db.add(semester)

        with self.assertRaises(IntegrityError):
            self.db.flush()


if __name__ == "__main__":
    unittest.main()
