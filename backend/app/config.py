import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "CoursePilot API")
    environment: str = os.getenv("ENVIRONMENT", "development")
    allowed_origins: str = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173",
    )
    database_url: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./coursepilot.db",
    )
    jwt_secret_key: str = os.getenv(
        "JWT_SECRET_KEY",
        "development-only-change-this-secret",
    )
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_expire_minutes: int = int(
        os.getenv("JWT_EXPIRE_MINUTES", "30")
    )


settings = Settings()


def get_allowed_origins() -> list[str]:
    return [
        origin.strip()
        for origin in settings.allowed_origins.split(",")
    ]
