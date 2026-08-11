from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings
from app.schema_migrations import run_startup_schema_migrations

connect_args = {}

if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(settings.database_url, connect_args=connect_args)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def init_database() -> None:
    import app.models  # noqa: F401

    run_startup_schema_migrations(engine)
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_database_status() -> dict:
    return {
        "status": "connected",
        "database": "SQLAlchemy relational database",
    }
