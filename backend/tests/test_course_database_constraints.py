import unittest

from pydantic import ValidationError
from sqlalchemy import create_engine, inspect
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import CreateIndex, CreateTable

from app.models.course import Course
from app.schemas.course import CourseCreate


class CourseDatabaseConstraintsTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:")
        Course.__table__.create(cls.engine)
        cls.session_factory = sessionmaker(bind=cls.engine)

    @classmethod
    def tearDownClass(cls):
        Course.__table__.drop(cls.engine)
        cls.engine.dispose()

    def setUp(self):
        self.db = self.session_factory()

    def tearDown(self):
        self.db.rollback()
        self.db.close()

    @staticmethod
    def make_course(suffix: str, **overrides) -> Course:
        values = {
            "course_id": f"course-{suffix}",
            "code": f"CSE {suffix}",
            "title": f"Course {suffix}",
            "department": "CSE",
            "semester": "Fall 2026",
            "instructor": f"Instructor {suffix}",
            "credits": 3,
            "capacity": 40,
            "available_seats": 10,
            "is_mandatory": False,
            "section": "A",
        }
        values.update(overrides)
        return Course(**values)

    def test_named_constraints_and_search_indexes_are_present(self):
        inspector = inspect(self.engine)
        unique_constraints = {
            constraint["name"]: tuple(constraint["column_names"])
            for constraint in inspector.get_unique_constraints("courses")
        }
        check_constraints = {
            constraint["name"]
            for constraint in inspector.get_check_constraints("courses")
        }
        indexes = {
            index["name"]: tuple(index["column_names"])
            for index in inspector.get_indexes("courses")
        }

        self.assertEqual(
            unique_constraints["uq_courses_course_id"],
            ("course_id",),
        )
        self.assertEqual(
            unique_constraints["uq_courses_code_semester_section"],
            ("code", "semester", "section"),
        )
        self.assertTrue(
            {
                "ck_courses_credits_positive",
                "ck_courses_capacity_positive",
                "ck_courses_available_seats_nonnegative",
                "ck_courses_available_seats_within_capacity",
                "ck_courses_section_not_blank",
            }.issubset(check_constraints)
        )
        self.assertEqual(indexes["ix_courses_code"], ("code",))
        self.assertEqual(indexes["ix_courses_title"], ("title",))
        self.assertEqual(
            indexes["ix_courses_department"],
            ("department",),
        )
        self.assertEqual(
            indexes["ix_courses_semester"],
            ("semester",),
        )

    def test_duplicate_course_id_is_rejected(self):
        first = self.make_course("duplicate-id-first")
        duplicate = self.make_course(
            "duplicate-id-second",
            course_id=first.course_id,
        )
        self.db.add_all([first, duplicate])

        with self.assertRaises(IntegrityError):
            self.db.flush()

    def test_duplicate_course_section_is_rejected(self):
        first = self.make_course("duplicate-section-first")
        duplicate = self.make_course(
            "duplicate-section-second",
            code=first.code,
            semester=first.semester,
            section=first.section,
        )
        self.db.add_all([first, duplicate])

        with self.assertRaises(IntegrityError):
            self.db.flush()

    def test_invalid_numeric_values_are_rejected(self):
        invalid_values = (
            ("zero-credits", {"credits": 0}),
            ("zero-capacity", {"capacity": 0}),
            ("negative-seats", {"available_seats": -1}),
            (
                "seats-over-capacity",
                {"capacity": 20, "available_seats": 21},
            ),
        )

        for suffix, overrides in invalid_values:
            with self.subTest(case=suffix):
                self.db.add(self.make_course(suffix, **overrides))

                with self.assertRaises(IntegrityError):
                    self.db.flush()

                self.db.rollback()

    def test_blank_section_is_rejected(self):
        self.db.add(self.make_course("blank-section", section="   "))

        with self.assertRaises(IntegrityError):
            self.db.flush()

    def test_valid_available_seat_boundaries_are_accepted(self):
        full_section = self.make_course(
            "full-section",
            capacity=20,
            available_seats=0,
        )
        empty_section = self.make_course(
            "empty-section",
            capacity=20,
            available_seats=20,
        )
        self.db.add_all([full_section, empty_section])
        self.db.flush()

        self.assertIsNotNone(full_section.id)
        self.assertIsNotNone(empty_section.id)

    def test_create_schema_rejects_seats_over_capacity(self):
        payload = {
            "course_id": "schema-course",
            "code": "CSE 499",
            "title": "Schema Validation",
            "department": "CSE",
            "semester": "Fall 2026",
            "instructor": "Schema Instructor",
            "credits": 3,
            "capacity": 20,
            "available_seats": 21,
            "is_mandatory": False,
            "section": "A",
        }

        with self.assertRaisesRegex(
            ValidationError,
            "available_seats cannot be greater than capacity",
        ):
            CourseCreate(**payload)

    def test_course_ddl_compiles_for_postgresql(self):
        table_ddl = str(
            CreateTable(Course.__table__).compile(
                dialect=postgresql.dialect()
            )
        )
        index_ddl = {
            index.name: str(
                CreateIndex(index).compile(
                    dialect=postgresql.dialect()
                )
            )
            for index in Course.__table__.indexes
        }

        self.assertIn("uq_courses_course_id", table_ddl)
        self.assertIn("uq_courses_code_semester_section", table_ddl)
        self.assertIn("ck_courses_credits_positive", table_ddl)
        self.assertIn(
            "ck_courses_available_seats_within_capacity",
            table_ddl,
        )
        self.assertIn("ix_courses_code", index_ddl)
        self.assertIn("ix_courses_title", index_ddl)
        self.assertIn("ix_courses_department", index_ddl)
        self.assertIn("ix_courses_semester", index_ddl)


if __name__ == "__main__":
    unittest.main()
