from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_allowed_origins, settings
from app.dynamodb import get_database_status
from app.api.routes.courses import router as courses_router


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

app.include_router(courses_router)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to the CoursePilot API",
        "docs": "/docs",
        "health": "/health",
        "database_status": "/api/database/status",
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.environment,
    }


@app.get("/api/database/status")
def database_status():
    return get_database_status()