import unittest
from datetime import date
from uuid import UUID, uuid4

from sqlalchemy import create_engine, event, inspect
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import CreateIndex, CreateTable

from app.database import Base
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


class PrerequisiteModelsTestCase(unittest.TestCase):
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
    def make_course(*, suffix: str, code: str) -> Course:
        return Course(
            course_id=f"course-{suffix}",
            code=code,
            title=f"Course {suffix}",
            department="CSE",
            semester=f"Semester {suffix}",
            instructor="Dr. Academic Records",
            credits=3,
            capacity=30,
            available_seats=30,
            is_mandatory=True,
            section="A",
        )

    @staticmethod
    def make_student(*, suffix: str) -> Student:
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
            user=User(
                email=f"advisor-{suffix}@example.com",
                password_hash="test-password-hash",
                full_name="Academic Advisor",
                role="advisor",
            ),
            department=department,
            employee_number=f"ADV-{suffix}",
        )

        return Student(
            user=User(
                email=f"student-{suffix}@example.com",
                password_hash="test-password-hash",
                full_name="Student User",
                role="student",
            ),
            program=program,
            advisor=advisor,
            student_number=f"STU-{suffix}",
            current_trimester=3,
        )

    def test_tables_relationships_and_constraints_match_erd(self):
        inspector = inspect(self.engine)
        self.assertIn(
            "course_prerequisites",
            inspector.get_table_names(),
        )
        self.assertIn("completed_courses", inspector.get_table_names())

        prerequisite_foreign_keys = {
            foreign_key["constrained_columns"][0]: foreign_key[
                "referred_table"
            ]
            for foreign_key in inspector.get_foreign_keys(
                "course_prerequisites"
            )
        }
        completed_course_foreign_keys = {
            foreign_key["constrained_columns"][0]: foreign_key[
                "referred_table"
            ]
            for foreign_key in inspector.get_foreign_keys(
                "completed_courses"
            )
        }

        self.assertEqual(
            prerequisite_foreign_keys,
            {
                "course_id": "courses",
                "prerequisite_course_id": "courses",
            },
        )
        self.assertEqual(
            completed_course_foreign_keys,
            {
                "student_id": "students",
                "course_id": "courses",
            },
        )

        prerequisite = self.make_course(
            suffix=uuid4().hex[:8],
            code="CSE 201",
        )
        target = self.make_course(
            suffix=uuid4().hex[:8],
            code="CSE 301",
        )
        student = self.make_student(suffix=uuid4().hex[:8])
        rule = CoursePrerequisite(
            course=target,
            prerequisite_course=prerequisite,
            minimum_grade="B",
        )
        completed = CompletedCourse(
            student=student,
            course=prerequisite,
            grade="B+",
            completed_at=date(2026, 5, 1),
        )
        self.db.add_all([rule, completed])
        self.db.flush()

        self.assertIsInstance(rule.id, UUID)
        self.assertIsInstance(completed.id, UUID)
        self.assertEqual(
            completed.completion_status,
            CompletionStatus.COMPLETED.value,
        )
        self.assertIn(rule, target.prerequisite_rules)
        self.assertIn(rule, prerequisite.required_for_rules)
        self.assertIn(completed, student.completed_courses)
        self.assertIn(completed, prerequisite.completed_course_records)

    def test_invalid_and_duplicate_records_are_rejected(self):
        suffix = uuid4().hex[:8]
        student = self.make_student(suffix=suffix)
        prerequisite = self.make_course(
            suffix=f"{suffix}-required",
            code="CSE 101",
        )
        target = self.make_course(
            suffix=f"{suffix}-target",
            code="CSE 201",
        )
        self.db.add_all([student, prerequisite, target])
        self.db.flush()

        self.db.add(
            CoursePrerequisite(
                course=target,
                prerequisite_course=target,
                minimum_grade="C",
            )
        )

        with self.assertRaises(IntegrityError):
            self.db.flush()

        self.db.rollback()
        self.db.add(
            CompletedCourse(
                student=student,
                course=prerequisite,
                grade="Z",
                completed_at=date(2026, 5, 1),
            )
        )

        with self.assertRaises(IntegrityError):
            self.db.flush()

    def test_tables_and_indexes_compile_for_postgresql(self):
        dialect = postgresql.dialect()

        for table in (
            CoursePrerequisite.__table__,
            CompletedCourse.__table__,
        ):
            table_sql = str(CreateTable(table).compile(dialect=dialect))
            self.assertIn("UUID", table_sql)
            self.assertIn("FOREIGN KEY", table_sql)

            for index in table.indexes:
                index_sql = str(CreateIndex(index).compile(dialect=dialect))
                self.assertIn("CREATE INDEX", index_sql)


if __name__ == "__main__":
    unittest.main()
