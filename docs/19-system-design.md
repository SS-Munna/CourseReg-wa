# System Design

## Architecture

CoursePilot uses a layered web architecture.

React frontend -> API service -> FastAPI routes -> repository layer -> SQLAlchemy models -> relational database

## Frontend Layer

The frontend is built with React, TypeScript, and Vite. The course catalogue UI is organized into pages, components, services, context, and shared types.

Important frontend files:

- frontend/src/pages/CourseCatalogPage/
- frontend/src/components/CourseCard/
- frontend/src/components/CourseFilters/
- frontend/src/components/CourseStats/
- frontend/src/services/courseApi.ts
- frontend/src/types/course.ts

## Backend Layer

The backend is built with FastAPI. API routes receive HTTP requests and call repository functions.

Important backend files:

- backend/app/main.py
- backend/app/api/routes/courses.py
- backend/app/repositories/course_repository.py
- backend/app/schemas/course.py
- backend/app/models/course.py
- backend/app/database.py
- backend/app/seed_data.py

## Database Layer

The database layer uses SQLAlchemy. SQLite is used for local development. PostgreSQL can be used later by changing DATABASE_URL.

## Course Catalogue Flow

Student opens course catalogue -> React calls fetchCourses() -> GET /api/courses -> FastAPI course route receives request -> repository builds SQLAlchemy query -> database returns course records -> backend returns JSON -> React updates state -> course cards are rendered

## Main Endpoint

GET /api/courses

Query parameters:

- search
- department
- semester
- is_mandatory
- available_only

## Error Handling

The API returns normal course data for successful requests. If the database operation fails, the backend returns a database operation error with status code 500.
