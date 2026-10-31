import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


DEVELOPMENT_JWT_SECRET = "development-only-change-this-secret"
EXAMPLE_JWT_SECRET = "replace-with-a-long-random-secret"


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
        DEVELOPMENT_JWT_SECRET,
    )
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_expire_minutes: int = int(
        os.getenv("JWT_EXPIRE_MINUTES", "30")
    )
    bootstrap_system_admin_name: str = os.getenv(
        "BOOTSTRAP_SYSTEM_ADMIN_NAME",
        "System Administrator",
    )
    bootstrap_system_admin_email: str = os.getenv(
        "BOOTSTRAP_SYSTEM_ADMIN_EMAIL",
        "",
    )
    bootstrap_system_admin_password: str = os.getenv(
        "BOOTSTRAP_SYSTEM_ADMIN_PASSWORD",
        "",
    )

    def __post_init__(self) -> None:
        secret = self.jwt_secret_key.strip()
        if self.environment.strip().lower() != "development" and (
            not secret
            or secret in {DEVELOPMENT_JWT_SECRET, EXAMPLE_JWT_SECRET}
        ):
            raise ValueError(
                "JWT_SECRET_KEY must be set to a private value outside development."
            )


settings = Settings()


def get_allowed_origins() -> list[str]:
    return [
        origin.strip()
        for origin in settings.allowed_origins.split(",")
    ]
