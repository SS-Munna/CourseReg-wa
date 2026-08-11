# Database Design

## Database Direction

CoursePilot uses a SQLAlchemy relational model layer. SQLite supports local
development and demonstration, while `DATABASE_URL` allows the same model
metadata to target PostgreSQL.

## Core User and Academic Tables

The following ERD entities are implemented with UUID primary keys:

| Table | Purpose | Main relationships |
|---|---|---|
| `users` | Authentication and shared account data | Optional one-to-one student, advisor, or instructor profile |
| `departments` | Academic departments | Has programs, advisors, and instructors |
| `programs` | Degree programs and credit limits | Belongs to a department; has students |
| `students` | Student academic profiles | Belongs to a user, program, and advisor |
| `advisors` | Academic-advisor profiles | Belongs to a user and department; advises students |
| `instructors` | Teaching-staff profiles | Belongs to a user and department |
| `semesters` | Academic terms and date ranges | Referenced by later section and registration models |

## Registration and Activity Tables

| Table | Purpose | Main relationships |
|---|---|---|
| `registrations` | Stores draft, submitted, reviewed, and dropped course requests | Belongs to a student and section offering; optionally reviewed by an advisor |
| `waitlist_entries` | Stores ordered waiting-list membership and outcomes | Belongs to a student and section offering |
| `notifications` | Stores user-facing account messages | Belongs to a user |
| `audit_logs` | Stores immutable-shaped action history | Belongs to the user who performed the action |

## Prerequisite and Academic Record Tables

| Table | Purpose | Main relationships |
|---|---|---|
| `course_prerequisites` | Stores required courses and optional minimum grades | Links a target `courses` row to a required `courses` row |
| `completed_courses` | Stores student course outcomes used for eligibility | Belongs to a student and the completed course offering |

The current denormalized catalogue may contain several offerings with the
same course code. A completed record references the exact historical offering,
while validation compares normalized course codes so that completion of an
older offering satisfies the equivalent current prerequisite.

The existing `courses` table continues to provide the current catalogue API.
Its normalization into ERD course, section, schedule, and room entities is
handled by the corresponding course-model work.

Each current `courses` row includes a semester, section label, instructor,
capacity, and schedule, so it acts as the present section-offering record.
`registrations.section_id` and `waitlist_entries.section_id` therefore reference
the internal `courses.id`. The public catalogue identifier remains
`courses.course_id`.

## Course and Section Integrity

The catalogue table uses named constraints that behave consistently in SQLite
and PostgreSQL:

| Constraint | Rule |
|---|---|
| `uq_courses_course_id` | A public `course_id` identifies only one catalogue row |
| `uq_courses_code_semester_section` | A code/semester/section offering cannot be duplicated |
| `ck_courses_credits_positive` | Credits must be greater than zero |
| `ck_courses_capacity_positive` | Section capacity must be greater than zero |
| `ck_courses_available_seats_nonnegative` | Available seats cannot be negative |
| `ck_courses_available_seats_within_capacity` | Available seats cannot exceed capacity |
| `ck_courses_*_not_blank` | Required course and section labels cannot contain only whitespace |

Section is required because each catalogue row represents a concrete section
offering. Schema validation applies the same positive-number rules and rejects
an available-seat value greater than capacity before a write reaches the
database. Database checks remain authoritative for every write path.

## Course Search Indexes

The catalogue has explicit single-column indexes named
`ix_courses_code`, `ix_courses_title`, `ix_courses_department`, and
`ix_courses_semester`. These support the fields exposed by the catalogue search
and filter API. Actual query plans remain database- and query-pattern-specific.

## Constraint Error Handling

FastAPI has a global SQLAlchemy `IntegrityError` handler. Known SQLite
constraint messages and PostgreSQL diagnostic constraint names are mapped to
stable error codes. Duplicate course IDs or offerings return `409 Conflict`;
invalid values return `422 Unprocessable Content`. Unknown integrity failures
return a generic conflict response, and raw database messages are never sent
to clients.

## Core Constraints

- User email, department code, program code, student number, and employee
  numbers are unique.
- A user can have at most one profile of each academic profile type.
- Program minimum credit cannot be negative, and maximum credit cannot be
  lower than minimum credit.
- A student's current trimester must be positive.
- A semester's academic year must be positive, and its end date cannot precede
  its start date.
- Registration states are limited to `draft`, `pending`, `approved`,
  `rejected`, and `dropped`.
- Waitlist states are limited to `active`, `promoted`, `removed`, and
  `expired`.
- A student cannot have duplicate registration or waitlist records for the
  same section offering.
- A course cannot be its own prerequisite, and the same prerequisite pair
  cannot be stored twice.
- A student cannot have duplicate completed-course records for the same course
  offering.
- Prerequisite minimum grades and completed-course grades are limited to the
  documented letter-grade scale.
- Completion states are limited to `completed`, `failed`, `in_progress`, and
  `withdrawn`.
- Required relationships use non-null foreign keys.

## Registration Query Indexes

- Student and registration status support student status pages.
- Section and registration status support seat and advisor workflows.
- Section, waitlist status, and joining time support deterministic active
  queue order without storing a fragile position number.
- User, read status, and creation time support unread-notification queries.
- Audit actor/entity indexes support chronological activity lookup.

## Live Section Availability

Read APIs calculate current section enrollment by counting registration rows
whose `registration_status` is `approved`. Draft, pending, rejected, and
dropped rows are excluded. Available seats are derived for each request as:

```text
max(section capacity - approved enrollment, 0)
```

The catalogue's `available_only` filter uses this same database-derived count,
so a section becomes full without requiring a separate cached seat update.
The existing `courses.available_seats` column is retained for compatibility
with the current denormalized catalogue schema, but it is not authoritative for
availability reads. Issue #26 adds transactional locking for writes that
allocate the final seat.

## Prerequisite Validation

Normalized rules in `course_prerequisites` are authoritative for minimum-grade
requirements. Existing `courses.prerequisites` JSON codes remain a compatible
completion-only source when a normalized rule for that code does not exist.

Validation retrieves the student's records for all required course codes.
Only records with `completion_status = 'completed'` and a grade other than
`F` count as successful. If several historical offerings share a code, the
best successfully completed grade is used. Letter grades are ordered from
`F` through `A+`; eligibility requires every configured minimum grade to be
met. The repository reports `not_completed` and `minimum_grade_not_met`
separately so clients can identify the exact blocking reason.

Student/status and course indexes support academic-record lookups. A reverse
prerequisite index supports finding courses affected by a required course.
The new tables are additive, so `create_all` can create them in existing
SQLite and PostgreSQL databases without changing or deleting current rows.

## Draft Selection Persistence

A selected course is a `registrations` row whose `registration_status` is
`draft`. Selection reads filter by both the authenticated student's UUID and
the draft state, then join the internal section reference to `courses` for
current catalogue details. Draft rows do not consume an enrolled seat.

The `uq_registration_student_section` constraint prevents a student from
holding two registration records for the same offering. The API checks for an
existing row before insertion for a clear response, while the constraint
remains the race-safe authority if concurrent requests pass that check. Both
SQLite's unique-constraint signature and PostgreSQL's named diagnostic map to
`409 DUPLICATE_SELECTION`.

Removal deletes only a row owned by the authenticated student while it is
still in the draft state. Non-draft records are retained for later status,
review, drop, and audit workflows. This feature reuses existing tables and
constraints, so it requires no production reset or schema migration.

## Authentication Compatibility

JWT subjects contain the authenticated user's UUID as a string. The backend
validates and converts the subject back to a UUID before querying the user.
API responses serialize user IDs as UUID strings.

PostgreSQL deployments created before the UUID model update are upgraded at
application startup. The compatibility migration changes the legacy integer
`users.id` values to deterministic UUID values, renames `name` to
`full_name`, and adds the current account-status and timestamp columns. It
runs in one transaction under an advisory lock and does not delete user rows.
Fresh databases and databases already using UUID identifiers are left intact.

## Data Access

The frontend does not access the database directly. It calls FastAPI routes,
which use repository functions and SQLAlchemy sessions.

## Local Database Lifecycle

SQLAlchemy creates missing tables automatically when the backend starts. It
does not alter an older table in place. Developers with a `coursepilot.db`
created before the UUID or course-constraint updates must preserve or remove
that development-only file and restart the backend. This reset removes local
demo data and is not a production migration strategy. Local database files
remain ignored by Git.
