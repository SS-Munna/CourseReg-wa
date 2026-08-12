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

POST /api/registrations/submit

GET /api/registrations

POST /api/registrations/{registration_id}/drop

GET /api/waitlists

POST /api/waitlists

DELETE /api/waitlists/{course_id}

GET /api/advisor/registration-requests

GET /api/advisor/registration-requests/{request_id}

POST /api/advisor/registration-requests/{request_id}/decision

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
same reusable blocking guard used by final submission. Selection creation
also invokes a candidate-specific form of the guard and returns a structured
`409` containing both course/section records and the exact overlapping time.

The protected final-submission route derives the student from the JWT account,
revalidates the current draft load, and changes every valid owned draft to
`pending` in one transaction. It returns the submitted registrations, one
shared submission timestamp, and the successful credit and schedule results.
Specific `409` and `422` responses identify the rule that blocked submission;
unexpected repository failures retain the safe shared `500` contract.

The protected waiting-list routes also derive ownership from the JWT. They
list live queue positions, join only a currently full and eligible section,
and mark only an owned active entry as removed. Clear responses distinguish a
missing section, an available direct-registration seat, an existing
registration, a duplicate or non-active waiting-list record, unmet
prerequisites, schedule conflicts, and safe repository failures.

Automatic promotion is an internal service for seat-releasing workflows, not a
new public route. It returns whether one student was promoted or whether the
section was full, the queue was empty, or no active candidate remained
eligible. The course-drop repository invokes its caller-owned-transaction form
after releasing a seat, so no nested commit can expose a partial drop.

The registration-status route defaults to `status=all` and also accepts
`draft`, `pending`, `approved`, `rejected`, `dropped`, or `waitlisted`. It
returns only the authenticated student's registration history with live course
availability, advisor comments, decision timestamps, deadline eligibility, and
active waiting-list entries when applicable. The drop route accepts an owned
registration UUID, requires the current state to be `approved`, and permits
the configured deadline date inclusively. Missing configuration, a passed
deadline, and an invalid state use distinct safe `409` errors; missing and
foreign IDs use the same `404` response.

Course drop locks the section before the registration, changes the approval to
`dropped`, writes the student notification and audit event, and runs at most
one waiting-list promotion under the same transaction boundary. PostgreSQL row
locks and the shared SQLite mutex serialize competing writes. Any failure
rolls back the drop, queue changes, new promoted registration, notifications,
and audit events together.

The advisor routes require the advisor role and a linked advisor profile. They
scope every query to students assigned to that advisor. The list groups a
student's rows by shared submission time, supports status filters and bounded
pagination, and exposes current and historical decisions. The details route
includes student and course information, credit and prerequisite results,
schedule conflicts, live section availability, and active waiting-list
positions. The decision route approves an entire pending request with locked
capacity checks or rejects the entire request with a mandatory reason. Each
decision also creates one student notification and one audit event.

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

The seat-allocation repository owns the capacity-sensitive transition from
`pending` to `approved`. It locks the target section before recounting approved
rows, then checks capacity, changes status, flushes, and commits while the lock
is still held. Lock order is section first and registration second. Idempotent
approved retries do not consume another seat, and every rejected allocation
rolls back. SQLite tests use an in-process mutex because that dialect omits
`FOR UPDATE`; PostgreSQL uses a row lock across application workers.

The registration-submission repository locks all selected sections in stable
ID order before locking the student's draft registration rows. It checks
normalized duplicates and completed courses, then invokes the existing
prerequisite, credit, and schedule guards and recounts approved enrollment.
Only after every validation succeeds does it apply one UTC timestamp and move
the locked drafts to `pending`. Validation and write failures roll back the
whole transaction. SQLite serializes local submissions with a process mutex;
PostgreSQL uses section-first and registration-second row locks.

The waiting-list repository locks the section before every join or leave,
recounts approved enrollment, and runs prerequisite and schedule guards before
creating or reactivating an entry. It assigns the UTC join time inside the
lock and calculates positions with `row_number()` over active entries ordered
by join time and UUID. Removed and expired rows can rejoin at the back;
promoted rows cannot. Leaves are soft state transitions, so history remains
available while active positions shift without a bulk renumbering write.
SQLite uses a process mutex and PostgreSQL uses `FOR UPDATE OF courses`.

The promotion repository follows the same section-first order, then locks the
active queue by join time and UUID. It rechecks duplicate and completed-course
rules, the program maximum, prerequisites, and schedule conflicts. Ineligible
entries become expired and processing continues in FIFO order. The first
eligible entry receives an approved registration through the shared locked
seat transition; its waitlist status, notification, and audit event are flushed
and committed with that registration. One invocation fills at most one seat,
and every failure rolls the compound transaction back. A shared re-entrant
SQLite mutex now covers submission, waitlist mutation, seat allocation, and
promotion while PostgreSQL uses the corresponding section row lock.

The advisor-review repository groups request rows by student and exact
`submitted_at` value, derives one canonical request UUID, and applies advisor
ownership in every lookup. Detail reads compose the course, prerequisite,
credit, conflict, and waitlist repositories into one review payload. Decisions
lock all request sections in ID order before all request registrations in UUID
order. Approval checks every section before invoking the shared locked-seat
transition; rejection updates every row directly. Reviewer metadata, statuses,
one notification, and one JSON audit record share one commit. A full section,
second decision, or write failure leaves the entire request unchanged. SQLite
uses the shared section mutex and PostgreSQL uses row locks.

Supported filters:

- search
- department
- semester
- is_mandatory
- available_only

## Model Design

The SQLAlchemy model layer includes users, departments, programs, students,
advisors, instructors, semesters, registration periods, registrations, waitlist entries,
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

Safe-seat tests verify final-seat success, full-section rollback, active and
inactive registration-state handling, idempotent retries, missing records,
wrapped database failures, and the structured allocation result. A two-thread
test proves that one final seat produces one approval and one full-section
result. PostgreSQL compilation separately verifies that the section query ends
with `FOR UPDATE OF courses` before enrollment is recounted.

Final-submission tests cover successful draft-to-pending transitions, ownership
isolation, preservation of existing pending and approved rows, both credit
limit directions, prerequisite and schedule revalidation, normalized duplicate
and completed-course checks, live full-section detection, safe errors, and
all-or-nothing rollback. A two-thread test proves that concurrent submissions
transition each draft once, while PostgreSQL compilation verifies deterministic
section and registration `FOR UPDATE` queries.

Waiting-list tests cover join/list/leave behavior, live full-section checks,
first-come ordering, position shifts, rejoining at the back, duplicate and
registration protection, prerequisites, schedule conflicts, ownership and
role isolation, safe errors, and rollback. Two-thread tests prove duplicate
joins create one entry and concurrent students receive distinct positions;
PostgreSQL compilation verifies the section lock and window queue query.

Automatic-promotion tests verify the four-record atomic success path, live
capacity, FIFO selection, position shifts, one-seat processing, prerequisite,
schedule, completed-course, duplicate, and maximum-credit revalidation,
ineligible-entry expiration, empty/full/no-eligible outcomes, missing sections,
safe dependency failures, and complete rollback. A two-thread test proves that
concurrent processing creates exactly one approval, promotion, notification,
and audit event for the final seat; PostgreSQL compilation verifies section and
FIFO entry row locks.

Registration-status and course-drop tests cover all current registration
states, rejection comments, active waiting-list composition, status filters,
ownership isolation, role and profile checks, missing and future period
configuration, inclusive and passed deadlines, safe errors, complete rollback,
and one-time concurrent drop behavior. The successful queue case proves the
drop, notification, audit event, promoted waitlist row, promoted registration,
promotion notification, and promotion audit event commit together. PostgreSQL
compilation verifies section-first and registration-second row locks.

Startup-migration tests verify the legacy PostgreSQL integer-to-UUID path,
the already-current UUID path, fresh-database behavior, safe rejection of an
unknown identifier type, transactional advisory locking, and migration order
before SQLAlchemy table creation. The SQL is also checked to ensure it never
deletes user rows or drops the users table.
