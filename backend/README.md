# CoursePilot Backend

This backend provides REST API endpoints for the CoursePilot frontend.

The backend is built with FastAPI and uses SQLAlchemy for relational database access. For local development and demonstration, it uses SQLite. The same structure can later connect to PostgreSQL through DATABASE_URL.

## Setup

From the backend folder:

    .\.venv\Scripts\python.exe -m pip install -r requirements.txt

## Environment Example

APP_NAME=CoursePilot API
ENVIRONMENT=development
ALLOWED_ORIGINS=http://localhost:5173
DATABASE_URL=sqlite:///./coursepilot.db

## Run Backend

    .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload

## Useful URLs

- http://127.0.0.1:8000/
- http://127.0.0.1:8000/health
- http://127.0.0.1:8000/api/database/status
- http://127.0.0.1:8000/api/courses
- http://127.0.0.1:8000/docs

## Database

The backend creates local database tables automatically on startup.

Important files:

- app/database.py
- app/models/course.py
- app/models/user.py
- app/seed_data.py

## Course API

GET /api/courses

Optional filters:

- search
- department
- semester
- is_mandatory
- available_only
