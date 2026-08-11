# CoursePilot

CoursePilot is a student course registration and course catalogue web application.

The current implemented feature is the student course catalogue with search and filtering. Students can view available courses, search by course code or title, filter by department and semester, check live section availability calculated from approved registrations, and validate prerequisite completion and minimum grades.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, TypeScript, Vite |
| Backend | FastAPI, Python |
| Database Layer | SQLAlchemy relational database |
| Local Demo Database | SQLite |
| Future Database Option | PostgreSQL through DATABASE_URL |

## Current Feature Flow

React Course Catalogue Page -> frontend API service -> FastAPI endpoint -> SQLAlchemy repository -> courses table -> JSON response -> React course cards

## Main API Endpoints

GET /api/courses

GET /api/courses/{course_id}/availability

GET /api/courses/{course_id}/prerequisite-validation

Optional query parameters:

- search
- department
- semester
- is_mandatory
- available_only

Example:

GET /api/courses?search=CSE&department=CSE&available_only=true

## Backend Local Setup

From the backend folder:

    .\.venv\Scripts\python.exe -m pip install -r requirements.txt
    .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload

Open:

- http://127.0.0.1:8000/health
- http://127.0.0.1:8000/api/database/status
- http://127.0.0.1:8000/api/courses
- http://127.0.0.1:8000/api/courses/cse-101/availability
- http://127.0.0.1:8000/api/courses/cse-201/prerequisite-validation
- http://127.0.0.1:8000/docs

## Frontend Local Setup

From the frontend folder:

    npm install
    npm run dev

Open:

- http://localhost:5173

## Database

The backend uses SQLAlchemy for database access. For local development, the app uses a SQLite database file. The database tables are created automatically when the backend starts, and development seed data is inserted if the tables are empty.

The same SQLAlchemy structure can later connect to PostgreSQL by changing DATABASE_URL.

## Current Backend Structure

- backend/app/database.py
- backend/app/models/completed_course.py
- backend/app/models/course.py
- backend/app/models/course_prerequisite.py
- backend/app/models/user.py
- backend/app/schemas/course.py
- backend/app/repositories/course_repository.py
- backend/app/repositories/prerequisite_repository.py
- backend/app/api/routes/courses.py
- backend/app/seed_data.py
- backend/app/main.py

## Current Frontend Structure

- frontend/src/pages/CourseCatalogPage/
- frontend/src/components/CourseCard/
- frontend/src/components/CourseFilters/
- frontend/src/components/CourseStats/
- frontend/src/services/courseApi.ts
- frontend/src/types/course.ts

## Notes

Local database files are ignored by Git and should not be committed.
