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
- shared response and exception handling
- models
- database configuration
- seed data

## API Response Design

Shared Pydantic schemas define success, error, request-validation, and
paginated responses. Application HTTP exceptions, request validation errors,
database integrity errors, and unexpected exceptions are translated through
centralized handlers. The handlers preserve required response headers while
preventing internal database and server details from reaching clients.

Successful authentication responses use the same `success` and `data`
envelope as the course catalogue and status endpoints. The frontend reads the
updated authentication envelope without changing session behavior.

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

The catalogue table rejects duplicate public course IDs and duplicate
code/semester/section offerings. Named checks enforce non-blank required
fields, positive credits and capacity, and an available-seat range from zero
through capacity. Explicit indexes cover course code, title, department, and
semester. FastAPI translates known integrity violations into safe `409` or
`422` responses without exposing raw database details.

## Seed Data

Development seed data is inserted when the application starts and the database is empty.

## Local Development

The local database is created automatically from SQLAlchemy models.

## Model Verification

The unit suite verifies table creation, foreign keys, relationships, UUIDs,
defaults, timestamps, valid-state queries, state check constraints, and
student/section uniqueness. These tests run against SQLite while using the
same SQLAlchemy metadata intended for PostgreSQL.

Course-integrity tests additionally inspect named constraints and indexes,
exercise invalid records against SQLite, compile the course table and indexes
with the PostgreSQL dialect, validate Pydantic seat rules, and verify API error
translation for both SQLite messages and PostgreSQL constraint names.

API-contract tests verify success envelopes, pagination calculations, invalid
pagination values, HTTP status and header preservation, field-level request
validation details, safe database failures, safe unexpected failures, and the
shared schemas published through OpenAPI.
