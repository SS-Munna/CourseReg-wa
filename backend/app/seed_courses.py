from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError

from app.dynamodb import get_courses_table
from app.schemas.course import CourseCreate


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


def to_item(course: CourseCreate) -> dict:
    if hasattr(course, "model_dump"):
        return course.model_dump()
    return course.dict()


def get_validated_courses() -> list[dict]:
    return [to_item(CourseCreate(**course)) for course in SAMPLE_COURSES]


def seed_courses() -> int:
    table = get_courses_table()
    courses = get_validated_courses()

    with table.batch_writer(overwrite_by_pkeys=["course_id"]) as batch:
        for course in courses:
            batch.put_item(Item=course)

    return len(courses)


def main() -> None:
    print("CoursePilot DynamoDB seed data")
    print(f"Prepared course records: {len(SAMPLE_COURSES)}")

    try:
        courses = get_validated_courses()

        print("Validated sample course records:")
        for course in courses:
            print(f"- {course['code']}: {course['title']}")

        inserted_count = seed_courses()
        print(f"Seed completed. Inserted/updated {inserted_count} course records.")

    except NoCredentialsError:
        print("AWS credentials were not found.")
        print("Configure AWS credentials locally before running the seed script.")

    except (BotoCoreError, ClientError) as error:
        print("DynamoDB seed operation failed.")
        print(str(error))


if __name__ == "__main__":
    main()