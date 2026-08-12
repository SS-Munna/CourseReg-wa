from datetime import date
import unittest

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Course, RegistrationPeriod, Semester
from app.seed_data import SAMPLE_COURSES, seed_database


class SeedDataTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
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

    def setUp(self):
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)
        self.db = self.session_factory()

    def tearDown(self):
        self.db.rollback()
        self.db.close()

    def test_seed_creates_catalogue_and_demo_registration_periods_once(self):
        seed_database(self.db)
        seed_database(self.db)

        periods = self.db.query(RegistrationPeriod).all()

        self.assertEqual(self.db.query(Course).count(), len(SAMPLE_COURSES))
        self.assertEqual(self.db.query(Semester).count(), 2)
        self.assertEqual(len(periods), 2)
        self.assertEqual(
            {
                (
                    period.semester.semester_name,
                    period.semester.academic_year,
                )
                for period in periods
            },
            {("Fall", 2026), ("Spring", 2027)},
        )

    def test_seed_reuses_an_existing_matching_semester(self):
        existing_semester = Semester(
            semester_name="Fall",
            academic_year=2026,
            start_date=date(2026, 8, 1),
            end_date=date(2026, 12, 20),
            status="active",
        )
        self.db.add(existing_semester)
        self.db.commit()
        existing_id = existing_semester.id

        seed_database(self.db)

        fall_period = (
            self.db.query(RegistrationPeriod)
            .join(Semester)
            .filter(
                Semester.semester_name == "Fall",
                Semester.academic_year == 2026,
            )
            .one()
        )

        self.assertEqual(fall_period.semester_id, existing_id)
        self.assertEqual(self.db.query(Semester).count(), 2)


if __name__ == "__main__":
    unittest.main()
