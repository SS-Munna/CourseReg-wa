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
advisors, instructors, semesters, registrations, waitlist entries,
notifications, audit logs, and the existing course-catalogue model. Core user,
academic, registration, and activity records use UUID primary keys.
Relationships connect user accounts to optional academic profiles,
departments to their programs and staff, programs to students, advisors to
their assigned students and reviewed registrations, and students to their
registration and waitlist records.

Registration and waitlist state values are constrained by the database.
Student/section uniqueness prevents duplicate records. Composite indexes
support status queries, ordered active waitlists, unread notifications, and
audit-history lookups.

## Seed Data

Development seed data is inserted when the application starts and the database is empty.

## Local Development

The local database is created automatically from SQLAlchemy models.

## Model Verification

The unit suite verifies table creation, foreign keys, relationships, UUIDs,
defaults, timestamps, valid-state queries, state check constraints, and
student/section uniqueness. These tests run against SQLite while using the
same SQLAlchemy metadata intended for PostgreSQL.
