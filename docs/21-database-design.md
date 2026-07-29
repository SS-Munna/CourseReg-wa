# Database Design

## Database Direction

CoursePilot uses a SQLAlchemy-based relational database layer.

For local development and demonstration, the backend uses SQLite. The same structure is PostgreSQL-ready through DATABASE_URL.

## Tables

### courses

The courses table stores course catalogue records.

Important columns:

- id
- course_id
- code
- title
- department
- semester
- instructor
- credits
- capacity
- available_seats
- is_mandatory
- level
- description
- prerequisites
- section
- schedule

### users

The users table stores demo student login information for the planned login feature.

Important columns:

- id
- name
- email
- password
- role

## Data Access

The backend does not access the database directly from the frontend. The frontend calls FastAPI endpoints, and the backend uses repository functions with SQLAlchemy.

## Current Course Query

The course catalogue endpoint reads records from the courses table and applies optional filters.

GET /api/courses

## Local Database File

The local SQLite database file is used only for development and is ignored by Git.
