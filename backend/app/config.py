import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "CoursePilot API")
    environment: str = os.getenv("ENVIRONMENT", "development")
    allowed_origins: str = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")

    aws_region: str = os.getenv("AWS_REGION", "us-east-1")
    dynamodb_courses_table: str = os.getenv(
        "DYNAMODB_COURSES_TABLE",
        "CoursePilotCourses",
    )


settings = Settings()


def get_allowed_origins() -> list[str]:
    return [origin.strip() for origin in settings.allowed_origins.split(",")]