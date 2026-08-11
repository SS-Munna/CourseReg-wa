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

## API Routes

GET /api/courses

The route receives optional query parameters and calls the course repository.

GET /api/courses/{course_id}/availability

The availability route returns the selected offering's instructor, schedule,
rooms, capacity, approved enrollment, calculated available seats, and full
state. Unknown public course identifiers return the shared `404` error shape.

GET /api/courses/{course_id}/prerequisite-validation

The protected student route loads normalized prerequisite rules and completed
course records. It returns eligibility plus every satisfied or missing rule,
including minimum and earned grades. Missing student profiles and courses use
shared `404` errors; authentication and authorization use `401` and `403`.

GET /api/selections

POST /api/selections

GET /api/selections/credit-validation

POST /api/selections/credit-validation

GET /api/selections/schedule-conflict-validation

POST /api/selections/schedule-conflict-validation

DELETE /api/selections/{course_id}

The protected selection routes derive the student profile from the JWT user,
list only draft registrations, add an eligible section, and delete only an
owned draft. They return stable errors for missing profiles or sections,
duplicate records, unmet prerequisites, non-draft removal attempts, and safe
repository failures.

Selection list and mutation responses include the current credit calculation.
The credit-validation read route reports the active total and configured
program range. Its validation action uses the same reusable guard that final
submission will call, returning a structured `422` when the total is below or
above the inclusive limits without changing any registration status.

The schedule-conflict read route reports every overlap across the student's
draft, pending, and approved registrations. Its validation action applies the
same reusable blocking guard intended for final submission. Selection creation
also invokes a candidate-specific form of the guard and returns a structured
`409` containing both course/section records and the exact overlapping time.

## Repository Design

The course repository uses SQLAlchemy queries to retrieve and filter course
records. It uses a correlated count of approved registration rows for each
section, so catalogue and detail responses do not rely on a cached seat
number.

The prerequisite repository merges normalized `course_prerequisites` rows
with existing JSON prerequisite codes, then matches completed records by
normalized course code. This allows a successful historical offering to
satisfy a current rule. It selects the student's best completed grade and
returns a structured reason for each unmet rule. A reusable guard raises
`PrerequisitesNotMetError` before a caller persists an invalid selection.

The selection repository joins draft registrations to current course data and
uses the same approved-enrollment expression as the catalogue. Creation
checks for an existing student/section row, invokes the prerequisite guard,
and commits one draft transaction. The database unique constraint resolves
concurrent duplicate attempts. Removal scopes its lookup to the authenticated
student and refuses every non-draft state.

The credit repository sums course credits for the authenticated student's
draft, pending, and approved registrations. It excludes rejected and dropped
records, loads the minimum and maximum from the student's program, and returns
a structured below-minimum, within-range, or above-maximum result. Selection
mutations calculate that result inside their transaction so a response cannot
report a failed total after persisting an otherwise successful mutation.

The schedule-conflict repository loads the authenticated student's active
registrations and compares every meeting pair in the same normalized semester.
Day matching is case- and whitespace-insensitive. Strict interval comparison
allows adjacent meetings while detecting partial, contained, and exact
overlaps. The repository returns every conflict in deterministic course order
and exposes reusable candidate-selection and final-load guards.

Supported filters:

- search
- department
- semester
- is_mandatory
- available_only

## Model Design

The SQLAlchemy model layer includes users, departments, programs, students,
advisors, instructors, semesters, registrations, waitlist entries,
notifications, audit logs, course prerequisites, completed courses, and the
existing course-catalogue model. Core user, academic, registration, activity,
prerequisite, and completed-course records use UUID primary keys.
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

Prerequisite relationships cannot duplicate or reference the same course on
both sides. Completed-course records are unique per student and course
offering. Supported letter grades and completion states are constrained in
both SQLite and PostgreSQL.

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

Section-availability tests create registrations in every supported state and
verify that only approved records count toward enrollment. They also verify
immediate recalculation after the final seat is approved, dynamic
`available_only` filtering, schedule and room output, the shared not-found
response, safe repository failures, and the OpenAPI response schema.

Prerequisite tests inspect tables, foreign keys, relationships, named
constraints, UUIDs, indexes, and PostgreSQL DDL. API tests cover no-rule
eligibility, missing courses, insufficient minimum grades, historical
offerings, ignored in-progress records, legacy JSON rules, student-only
authorization, safe database failures, OpenAPI schemas, PostgreSQL query
compilation, and the blocking selection guard.

Selected-course tests exercise create/list/delete behavior, dynamic seat
output, ownership isolation, non-draft protection, student-only access,
missing profiles and sections, invalid request bodies, unmet prerequisite
rollback, duplicate prevention, safe database failures, shared constraint
translation, OpenAPI schemas, and PostgreSQL query compilation.

Credit-validation tests verify recalculation after both add and remove,
inclusive minimum and maximum boundaries, flexible over-limit drafts, clear
blocking responses, student isolation, active-state inclusion, rejected and
dropped exclusion, protected-route behavior, safe repository failures, the
reusable final-load guard, OpenAPI schemas, and PostgreSQL query compilation.

Schedule-conflict tests verify detailed blocking errors, all active and
inactive registration states, exact non-overlapping boundaries, normalized
semester/day matching, multiple weekly meetings, conflict-free validation,
all-conflict reporting, student isolation, malformed stored-data safety,
mutation rollback, reusable final validation, OpenAPI schemas, and PostgreSQL
query compilation.

Startup-migration tests verify the legacy PostgreSQL integer-to-UUID path,
the already-current UUID path, fresh-database behavior, safe rejection of an
unknown identifier type, transactional advisory locking, and migration order
before SQLAlchemy table creation. The SQL is also checked to ensure it never
deletes user rows or drops the users table.
