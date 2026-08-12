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
availability reads.

## Transactional Seat Allocation

Only a `pending` registration can receive a new seat. Allocation uses one
database transaction with this order:

1. Join the registration to its section and lock the `courses` row.
2. Lock and refresh the registration row.
3. Recount approved registrations for the locked section.
4. Reject when approved enrollment is already at capacity.
5. Otherwise change the pending row to `approved`, flush, and commit.

PostgreSQL emits `FOR UPDATE OF courses` for the first step. Concurrent
allocators for one section therefore serialize on the same row; a waiting
transaction recounts after the first commit and cannot reuse the final seat.
Every allocator follows section-then-registration lock order to avoid inverted
lock ordering. SQLite omits row-lock syntax, so the local/test path holds an
in-process transaction mutex through commit.

An approved retry is idempotent and reports the current derived enrollment
without adding another seat. Draft, rejected, and dropped rows are invalid
allocation states. A full-section error leaves the candidate pending. The
allocator continues to derive capacity from `courses.capacity` and approved
registration rows; it does not depend on the compatibility
`courses.available_seats` value.

This feature reuses the existing course and registration tables and indexes.
It adds no table, column, startup migration, or production reset.

## Final Registration Submission Transaction

Final submission is an atomic state transition on the authenticated student's
current draft registrations. The transaction follows this order:

1. Select the student's draft sections by internal course ID and lock the
   `courses` rows in deterministic order.
2. Select and lock the matching `registrations` rows by registration UUID.
3. Re-read the active registration set and reject normalized duplicate course
   codes or previously completed non-failing courses.
4. Revalidate prerequisites, the program credit range, and all active schedule
   pairs through the existing repository guards.
5. Recount approved enrollment for every locked section and reject any section
   already at capacity.
6. Apply one UTC `submitted_at` value, change every locked draft to `pending`,
   flush, and commit.

Any validation or repository failure rolls back the transaction, so no subset
of the draft load can become pending. Existing pending and approved records
may participate in credit, duplicate, and schedule validation but are never
rewritten by submission. The derived seat count ignores the compatibility
`courses.available_seats` value and counts only approved registrations.

PostgreSQL compiles the first two reads as `FOR UPDATE OF courses` and
`FOR UPDATE OF registrations`. Section-first lock ordering matches the safe
seat allocator and prevents an approval transaction from changing capacity
while a submission is performing its final seat check. SQLite omits row locks,
so local and test submissions hold an in-process mutex through commit.
Concurrent retries therefore submit each draft at most once; a later request
finds no draft rows and returns the no-drafts result.

Submission reuses the existing `registrations.submitted_at` and
`registration_status` columns, course data, completed-course records, program
limits, and current indexes. It adds no table, column, migration, or database
reset.

## Waiting-List Queue Transactions

An active queue is derived from `waitlist_entries` rather than maintained as a
stored position. A window query partitions active entries by `section_id` and
orders each partition by `joined_at` followed by the entry UUID. It returns
both `row_number()` as the current one-based position and `count()` as the
active queue size. Marking one row `removed` therefore shifts later positions
on the next read without updating unrelated records.

Join and leave transactions follow a section-first lock order:

1. Resolve the public course ID and lock the matching `courses` row.
2. Recount approved registrations while that section lock is held.
3. On join, require a full section, reject any registration for the same
   student and section, lock the existing waitlist row if present, and run the
   prerequisite and schedule guards.
4. Insert a new active row or reactivate a removed/expired row with a strictly
   later UTC join time; promoted rows cannot rejoin.
5. On leave, lock the owned row, require `active`, set `removed` and
   `removed_at`, then commit.

PostgreSQL uses `FOR UPDATE OF courses`, which serializes changes to one
section across workers. The `uq_waitlist_student_section` constraint remains
the final authority against duplicate rows. SQLite local and test writes use
an in-process transaction mutex because SQLite ignores row-lock syntax. Both
SQLite and PostgreSQL duplicate signatures map to
`409 DUPLICATE_WAITLIST_ENTRY` without exposing database details.

The workflow reuses the existing waitlist table, status values, unique
constraint, and queue index. It introduces no schema migration or reset.

## Automatic Waiting-List Promotion Transaction

A seat-releasing workflow calls one promotion operation for the affected
section. The transaction follows this order:

1. Lock the `courses` row and recount approved registrations.
2. Stop without mutation if the section is full; otherwise lock active
   `waitlist_entries` in `joined_at`, UUID order.
3. Revalidate each candidate's duplicate and completed-course state, program
   maximum, prerequisites, and schedule. Mark an ineligible row `expired` and
   continue to the next FIFO row.
4. Insert a `pending` registration for the first eligible student and apply the
   shared capacity-safe transition to `approved` inside the existing lock.
5. Mark the waiting-list row `promoted`, insert one `notifications` row, insert
   one `audit_logs` row, flush all records, and commit once.

The audit entity is the promoted waitlist UUID and the related registration ID
is stored in safe JSON details. The notification belongs to the affected
student's user account. Queue positions remain derived, so expiring or
promoting entries shifts later positions without renumbering rows.

PostgreSQL uses `FOR UPDATE OF courses` followed by
`FOR UPDATE OF waitlist_entries`. Same-section workers therefore serialize and
recount enrollment before choosing a candidate. SQLite uses one shared
re-entrant in-process mutex across section-sensitive repositories. Any error
rolls back the registration, waitlist transition, notification, audit event,
and preceding expirations together. Existing tables, status values, columns,
constraints, and indexes support this workflow without a migration or reset.

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

## Credit Load Calculation

Credit totals are derived rather than stored. The calculation joins the
authenticated student's `registrations` rows to `courses` and sums
`courses.credits` for `draft`, `pending`, and `approved` states. `rejected`
and `dropped` rows are excluded. The applicable inclusive range comes from
the student's related `programs.minimum_credit` and
`programs.maximum_credit` values.

The API reports the current total, range, shortfall or excess, and validation
state. A reusable guard rejects a final-load check outside the range. Draft
additions remain editable even when they temporarily exceed the maximum; the
guard is authoritative at the final-validation boundary. No new column or
table is required, so existing SQLite and PostgreSQL deployments need no
schema migration or reset.

## Schedule-Conflict Detection

Schedule conflicts are derived from the JSON meeting entries stored on the
current denormalized `courses` offering rows. The query joins the authenticated
student's registrations to those offerings and includes only `draft`,
`pending`, and `approved` states. `rejected` and `dropped` rows do not
participate.

Two meetings conflict only when they belong to the same normalized semester,
their normalized days match, and both strict interval rules are true:

```text
new_start < existing_end
new_end > existing_start
```

This permits adjacent classes whose boundary times are equal. Each meeting in
a multi-day schedule is compared, and the result records both courses,
sections, registration states and complete meeting ranges together with the
exact overlapping interval. Candidate checks run before draft insertion. A
second reusable guard checks all active pairs for final submission.

Conflict validation is computed rather than stored, so no table, column,
production migration, or database reset is required. Schedule times are parsed
as 24-hour `HH:MM`; malformed stored schedule data fails through the safe
repository-error contract instead of being returned to clients.

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
