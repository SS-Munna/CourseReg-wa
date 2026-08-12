from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.models.course import Course
from app.models.registration_period import RegistrationPeriod
from app.models.semester import Semester
from app.models.user import User
from app.security import hash_password


SAMPLE_COURSES = [
    {
        "course_id": "cse-101",
        "code": "CSE 101",
        "title": "Introduction to Computer Science",
        "department": "CSE",
        "semester": "Fall 2026",
        "instructor": "Dr. Rahman",
        "credits": 3,
        "capacity": 40,
        "available_seats": 12,
        "is_mandatory": True,
        "level": "Undergraduate",
        "description": "Introductory programming and computing concepts.",
        "prerequisites": [],
        "section": "A",
        "schedule": [
            {
                "day": "Sunday",
                "start_time": "10:00",
                "end_time": "11:30",
                "room": "CSE-201",
            }
        ],
    },
    {
        "course_id": "cse-201",
        "code": "CSE 201",
        "title": "Data Structures",
        "department": "CSE",
        "semester": "Fall 2026",
        "instructor": "Dr. Ahmed",
        "credits": 3,
        "capacity": 35,
        "available_seats": 8,
        "is_mandatory": True,
        "level": "Undergraduate",
        "description": "Linear and nonlinear data structures.",
        "prerequisites": ["CSE 101"],
        "section": "A",
        "schedule": [
            {
                "day": "Monday",
                "start_time": "09:00",
                "end_time": "10:30",
                "room": "CSE-301",
            }
        ],
    },
    {
        "course_id": "cse-301",
        "code": "CSE 301",
        "title": "Database Systems",
        "department": "CSE",
        "semester": "Fall 2026",
        "instructor": "Dr. Hasan",
        "credits": 3,
        "capacity": 40,
        "available_seats": 15,
        "is_mandatory": True,
        "level": "Undergraduate",
        "description": "Database design, SQL concepts, and data management.",
        "prerequisites": ["CSE 201"],
        "section": "A",
        "schedule": [
            {
                "day": "Tuesday",
                "start_time": "11:00",
                "end_time": "12:30",
                "room": "CSE-401",
            }
        ],
    },
    {
        "course_id": "eee-205",
        "code": "EEE 205",
        "title": "Circuit Analysis",
        "department": "EEE",
        "semester": "Fall 2026",
        "instructor": "Dr. Karim",
        "credits": 3,
        "capacity": 30,
        "available_seats": 5,
        "is_mandatory": True,
        "level": "Undergraduate",
        "description": "Fundamentals of electrical circuit analysis.",
        "prerequisites": [],
        "section": "B",
        "schedule": [
            {
                "day": "Wednesday",
                "start_time": "10:00",
                "end_time": "11:30",
                "room": "EEE-202",
            }
        ],
    },
    {
        "course_id": "mat-101",
        "code": "MAT 101",
        "title": "Calculus I",
        "department": "Mathematics",
        "semester": "Fall 2026",
        "instructor": "Dr. Chowdhury",
        "credits": 3,
        "capacity": 45,
        "available_seats": 20,
        "is_mandatory": True,
        "level": "Undergraduate",
        "description": "Limits, derivatives, and introductory integration.",
        "prerequisites": [],
        "section": "A",
        "schedule": [
            {
                "day": "Thursday",
                "start_time": "08:30",
                "end_time": "10:00",
                "room": "MAT-101",
            }
        ],
    },
    {
        "course_id": "phy-101",
        "code": "PHY 101",
        "title": "Physics I",
        "department": "Physics",
        "semester": "Fall 2026",
        "instructor": "Dr. Islam",
        "credits": 3,
        "capacity": 40,
        "available_seats": 0,
        "is_mandatory": True,
        "level": "Undergraduate",
        "description": "Mechanics, motion, force, energy, and waves.",
        "prerequisites": [],
        "section": "C",
        "schedule": [
            {
                "day": "Sunday",
                "start_time": "13:00",
                "end_time": "14:30",
                "room": "PHY-105",
            }
        ],
    },
    {
        "course_id": "cse-401",
        "code": "CSE 401",
        "title": "Artificial Intelligence",
        "department": "CSE",
        "semester": "Spring 2027",
        "instructor": "Dr. Sultana",
        "credits": 3,
        "capacity": 35,
        "available_seats": 18,
        "is_mandatory": False,
        "level": "Undergraduate",
        "description": "Search, reasoning, machine learning, and intelligent systems.",
        "prerequisites": ["CSE 201"],
        "section": "A",
        "schedule": [
            {
                "day": "Monday",
                "start_time": "14:00",
                "end_time": "15:30",
                "room": "CSE-501",
            }
        ],
    },
]


DEMO_USERS = []


SAMPLE_REGISTRATION_PERIODS = [
    {
        "semester_name": "Fall",
        "academic_year": 2026,
        "semester_start": date(2026, 8, 1),
        "semester_end": date(2026, 12, 20),
        "semester_status": "active",
        "opening_time": datetime(2026, 8, 1, tzinfo=timezone.utc),
        "closing_time": datetime(2026, 9, 15, 23, 59, tzinfo=timezone.utc),
        "drop_deadline": date(2026, 10, 15),
        "minimum_credit": 9,
        "maximum_credit": 18,
        "status": "open",
    },
    {
        "semester_name": "Spring",
        "academic_year": 2027,
        "semester_start": date(2027, 1, 10),
        "semester_end": date(2027, 5, 20),
        "semester_status": "upcoming",
        "opening_time": datetime(2026, 12, 1, tzinfo=timezone.utc),
        "closing_time": datetime(2027, 1, 8, 23, 59, tzinfo=timezone.utc),
        "drop_deadline": date(2027, 2, 5),
        "minimum_credit": 9,
        "maximum_credit": 18,
        "status": "scheduled",
    },
]


def _seed_bootstrap_system_admin(db: Session) -> None:
    email = settings.bootstrap_system_admin_email.strip().lower()
    password = settings.bootstrap_system_admin_password

    if not email and not password:
        return

    if not email or not password:
        raise RuntimeError(
            "Both BOOTSTRAP_SYSTEM_ADMIN_EMAIL and "
            "BOOTSTRAP_SYSTEM_ADMIN_PASSWORD are required together."
        )

    if len(password) < 12:
        raise RuntimeError(
            "BOOTSTRAP_SYSTEM_ADMIN_PASSWORD must contain at least "
            "12 characters."
        )

    existing_user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if existing_user is not None:
        return

    db.add(
        User(
            full_name=(
                settings.bootstrap_system_admin_name.strip()
                or "System Administrator"
            ),
            email=email,
            password_hash=hash_password(password),
            role="system-admin",
            account_status="active",
        )
    )


def _seed_registration_periods(db: Session) -> None:
    semesters_by_label = {
        (semester.semester_name.casefold(), semester.academic_year): semester
        for semester in db.query(Semester).all()
    }
    existing_period_labels = {
        (
            period.semester.semester_name.casefold(),
            period.semester.academic_year,
        )
        for period in db.query(RegistrationPeriod).all()
    }

    for period_data in SAMPLE_REGISTRATION_PERIODS:
        label = (
            period_data["semester_name"].casefold(),
            period_data["academic_year"],
        )

        if label in existing_period_labels:
            continue

        semester = semesters_by_label.get(label)

        if semester is None:
            semester = Semester(
                semester_name=period_data["semester_name"],
                academic_year=period_data["academic_year"],
                start_date=period_data["semester_start"],
                end_date=period_data["semester_end"],
                status=period_data["semester_status"],
            )
            semesters_by_label[label] = semester

        db.add(
            RegistrationPeriod(
                semester=semester,
                opening_time=period_data["opening_time"],
                closing_time=period_data["closing_time"],
                drop_deadline=period_data["drop_deadline"],
                minimum_credit=period_data["minimum_credit"],
                maximum_credit=period_data["maximum_credit"],
                status=period_data["status"],
            )
        )
        existing_period_labels.add(label)


def seed_database(db: Session) -> None:
    _seed_bootstrap_system_admin(db)

    if db.query(Course).count() == 0:
        for course_data in SAMPLE_COURSES:
            db.add(Course(**course_data))

    if db.query(User).count() == 0:
        for user_data in DEMO_USERS:
            db.add(User(**user_data))

    _seed_registration_periods(db)

    db.commit()
