# Technical Design Document

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React, TypeScript, Vite |
| Backend | FastAPI |
| ORM | SQLAlchemy |
| Local Database | SQLite |
| Production-ready option | PostgreSQL through DATABASE_URL |

## Backend Design

The backend is organized into:

- routes
- repositories
- schemas
- models
- database configuration
- seed data

## API Route

GET /api/courses

The route receives optional query parameters and calls the course repository.

## Repository Design

The repository uses SQLAlchemy queries to retrieve and filter course records.

Supported filters:

- search
- department
- semester
- is_mandatory
- available_only

## Model Design

The SQLAlchemy model layer includes users, departments, programs, students,
advisors, instructors, semesters, and the existing course-catalogue model.
Core user and academic records use UUID primary keys. Relationships connect
user accounts to optional academic profiles, departments to their programs
and staff, programs to students, and advisors to their assigned students.

## Seed Data

Development seed data is inserted when the application starts and the database is empty.

## Local Development

The local database is created automatically from SQLAlchemy models.
