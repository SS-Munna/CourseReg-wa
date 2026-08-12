from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.errors import (
    api_http_exception_handler,
    api_unhandled_exception_handler,
    api_validation_exception_handler,
)
from app.api.routes.advisor_reviews import router as advisor_reviews_router
from app.api.routes.auth import router as auth_router
from app.api.routes.courses import router as courses_router
from app.api.routes.registrations import router as registrations_router
from app.api.routes.selections import router as selections_router
from app.api.routes.waitlists import router as waitlists_router
from app.config import get_allowed_origins, settings
from app.database import (
    SessionLocal,
    get_database_status,
    init_database,
)
from app.database_errors import database_integrity_error_handler
from app.schemas.common import SuccessResponse
from app.seed_data import seed_database


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Base FastAPI backend service for CoursePilot.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(
    IntegrityError,
    database_integrity_error_handler,
)
app.add_exception_handler(
    StarletteHTTPException,
    api_http_exception_handler,
)
app.add_exception_handler(
    RequestValidationError,
    api_validation_exception_handler,
)
app.add_exception_handler(
    Exception,
    api_unhandled_exception_handler,
)

app.include_router(auth_router)
app.include_router(courses_router)
app.include_router(selections_router)
app.include_router(registrations_router)
app.include_router(waitlists_router)
app.include_router(advisor_reviews_router)


@app.on_event("startup")
def startup_event():
    init_database()
    db = SessionLocal()

    try:
        seed_database(db)
    finally:
        db.close()


@app.get("/", response_model=SuccessResponse[dict[str, str]])
def read_root():
    return SuccessResponse(
        data={
            "message": "Welcome to the CoursePilot API",
            "docs": "/docs",
            "health": "/health",
            "database_status": "/api/database/status",
        }
    )


@app.get("/health", response_model=SuccessResponse[dict[str, str]])
def health_check():
    return SuccessResponse(
        data={
            "status": "ok",
            "service": settings.app_name,
            "environment": settings.environment,
        }
    )


@app.get(
    "/api/database/status",
    response_model=SuccessResponse[dict[str, str]],
)
def database_status():
    return SuccessResponse(data=get_database_status())
