# CoursePilot Backend

This backend provides REST API endpoints for the CoursePilot frontend.

The backend is built with FastAPI and uses SQLAlchemy for relational database access. For local development and demonstration, it uses SQLite. The same structure can connect to PostgreSQL through `DATABASE_URL`.

## Setup

From the `backend` folder:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Environment Configuration

Create a `.env` file based on `.env.example`:

```text
APP_NAME=CoursePilot API
ENVIRONMENT=development
ALLOWED_ORIGINS=http://localhost:5173

DATABASE_URL=sqlite:///./coursepilot.db

JWT_SECRET_KEY=replace-with-a-long-random-secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30
```

`JWT_SECRET_KEY` must be replaced with a strong, private value outside local development. Never commit a real JWT secret to GitHub.

## Run Backend

From the `backend` folder:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

## Useful URLs

- http://127.0.0.1:8000/
- http://127.0.0.1:8000/health
- http://127.0.0.1:8000/api/database/status
- http://127.0.0.1:8000/api/courses
- http://127.0.0.1:8000/api/courses/cse-201/prerequisite-validation
- http://127.0.0.1:8000/api/auth/register
- http://127.0.0.1:8000/api/auth/login
- http://127.0.0.1:8000/api/auth/me
- http://127.0.0.1:8000/docs

## Shared API response contract

All JSON application endpoints use a common response envelope. Successful
responses contain `success: true` and a `data` value:

```json
{
  "success": true,
  "data": {
    "status": "ready"
  }
}
```

Errors contain `success: false` and an `error` object with a stable code and
safe message:

```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Not Found"
  }
}
```

Request-validation errors also provide a `details` list with the affected
field, message, and validation type. Paginated endpoints add `pagination`
with `page`, `page_size`, `total_items`, and `total_pages`. The reusable
schemas live in `app/schemas/common.py`, and centralized exception handlers
live in `app/api/errors.py`.

## Database

The backend creates local database tables automatically on startup.

Important files:

- `app/database.py`
- `app/models/advisor.py`
- `app/models/audit_log.py`
- `app/models/completed_course.py`
- `app/models/course.py`
- `app/models/course_prerequisite.py`
- `app/models/department.py`
- `app/models/instructor.py`
- `app/models/notification.py`
- `app/models/program.py`
- `app/models/registration.py`
- `app/models/semester.py`
- `app/models/student.py`
- `app/models/user.py`
- `app/models/waitlist_entry.py`
- `app/seed_data.py`

The core user and academic entities use UUID primary keys. If a local
`coursepilot.db` was created before the UUID model update, stop the backend,
delete that development-only database file, and restart the backend so
SQLAlchemy can create the current schema. This reset removes local demo data
and must not be used as a production migration strategy.

For PostgreSQL, startup runs an idempotent compatibility migration before
`create_all`. It upgrades a legacy integer `users.id` to UUID, preserves the
existing user rows and names, and adds the account-status and timestamp
columns required by the current user model. The migration is transactional
and protected by a PostgreSQL advisory lock, so a failure rolls back instead
of leaving a partially converted table. Existing JWTs with integer subjects
must be replaced by signing in again after this migration.

## Authentication API

CoursePilot uses signed, expiring JWT access tokens. Each token contains the user ID, issue time, and expiration time. The default expiry period is 30 minutes.

Old `demo-token-*` values are no longer accepted.

### Register

```text
POST /api/auth/register
```

Example request:

```json
{
  "name": "New Student",
  "email": "student@example.com",
  "password": "SecurePass123!"
}
```

Successful registration returns HTTP `201` with a signed JWT and the registered user:

```json
{
  "success": true,
  "data": {
    "token": "<signed-jwt-access-token>",
    "user": {
      "id": "73f37649-8365-4b9d-a92e-584ebaabd0c7",
      "name": "New Student",
      "email": "student@example.com",
      "role": "student"
    }
  }
}
```

Registration returns HTTP `409` when the email already exists.

### Login

```text
POST /api/auth/login
```

Example request:

```json
{
  "email": "student@example.com",
  "password": "SecurePass123!"
}
```

Successful login returns HTTP `200` with a signed JWT and the authenticated user. Invalid credentials return HTTP `401`.

### Get Current User

```text
GET /api/auth/me
```

This is a protected endpoint. Send the JWT using the Bearer authentication scheme:

```text
Authorization: Bearer <signed-jwt-access-token>
```

A valid token returns the current user. Missing, malformed, tampered, expired, and old `demo-token-*` values return HTTP `401 Unauthorized`.

Refresh tokens are outside the current authentication scope.

## Course API

```text
GET /api/courses
```

Optional filters:

- `search`
- `department`
- `semester`
- `is_mandatory`
- `available_only`

Section availability details use the public catalogue identifier:

```text
GET /api/courses/{course_id}/availability
```

The response includes the section label, instructor, schedule entries and
their rooms, capacity, approved enrollment, calculated available seats, and
an `is_full` flag. Both this endpoint and the course catalogue calculate
availability from current registration rows:

```text
available_seats = max(capacity - approved registrations, 0)
```

Draft, pending, rejected, and dropped registrations do not consume an
enrolled seat. A missing public `course_id` returns `404 SECTION_NOT_FOUND`.
The stored `courses.available_seats` value remains for schema compatibility,
but read APIs do not treat it as the authoritative live count.

Prerequisite eligibility is available to authenticated students at:

```text
GET /api/courses/{course_id}/prerequisite-validation
Authorization: Bearer <signed-jwt-access-token>
```

The response lists every prerequisite, its optional minimum grade, the
student's best successfully completed grade, and any unmet requirement. A
student is eligible only when all requirements are satisfied. Completed
records from an older offering with the same normalized course code qualify;
`failed`, `in_progress`, `withdrawn`, and `F` records do not. Existing JSON
prerequisite lists remain supported and represent completion-only rules when
no normalized minimum grade is configured.

## Course data integrity

Each current `courses` row represents one course section in one semester.
The database enforces the following rules in both SQLite and PostgreSQL:

- `course_id` is unique.
- The combination of `code`, `semester`, and `section` is unique.
- Required course and section text fields cannot be blank.
- Credits and capacity must be greater than zero.
- Available seats must be between zero and capacity, inclusive.

Explicit indexes support catalogue searches and filters on course code, title,
department, and semester. Database constraint violations are translated into
safe API responses. Duplicate records return `409 Conflict`; invalid numeric
or required-field values return `422 Unprocessable Content`. Raw database
messages are not returned to clients.

For example, a duplicate course ID produces:

```json
{
  "success": false,
  "error": {
    "code": "DUPLICATE_COURSE_ID",
    "message": "A course with this course ID already exists."
  }
}
```

SQLAlchemy's `create_all` creates missing tables but does not add constraints
or indexes to an existing table. After pulling this schema update, preserve or
remove an older development-only `coursepilot.db` file and restart the backend.
Never use a local database reset as a production migration strategy.


## Role-based access control

The backend recognizes four roles:

- `student`
- `advisor`
- `department-admin`
- `system-admin`

Public registration always creates a student account; users cannot select a privileged role during registration.

JWTs identify users but do not store authorization decisions. For every protected request, the backend reloads the user from the database and checks the account’s current role.

Authorization utilities are provided in `app/authorization.py`:

- `get_current_user` authenticates the request.
- `require_roles(...)` restricts an endpoint to selected roles.
- `ensure_owner_or_roles(...)` allows access through resource ownership or an explicitly permitted administrative role.

Authentication failures return `401 Unauthorized`. Authenticated users lacking the required role or ownership receive `403 Forbidden`. Ownership must be verified by the resource route; having the advisor role alone does not grant access to every student.

## Core academic models

The SQLAlchemy model layer includes the ERD-defined core entities:

- users
- departments
- programs
- students
- advisors
- instructors
- semesters

Users have optional one-to-one student, advisor, and instructor profiles. A
department contains programs and employs advisors and instructors. Each
student belongs to one program and is assigned to one advisor. Unique email,
student-number, employee-number, department-code, and program-code constraints
are enforced by the database. Program credit ranges, positive trimester/year
values, and semester date ranges also have database-level checks.

## Registration and activity models

The persistence layer includes registrations, waitlist entries, notifications,
and audit logs. Registration states are limited to `draft`, `pending`,
`approved`, `rejected`, and `dropped`. Waitlist states are limited to `active`,
`promoted`, `removed`, and `expired`.

A student can have only one registration and one waitlist entry for the same
section offering. Active waitlist queues can be ordered by `joined_at`, so a
stored queue-position value cannot become stale. Composite indexes support
student status lookups, section status lookups, queue ordering, unread
notifications, and audit-history queries.

The current catalogue stores each semester/section offering in one `courses`
row, including its section label, instructor, capacity, and schedule. Therefore
the registration models' `section_id` foreign key points to the internal
`courses.id`. Public APIs continue to identify catalogue records with
`course_id`.

This issue establishes persistence only. Creating notifications and audit-log
records automatically when registration actions occur is handled by the
notification and audit-logging feature.

## Prerequisite and completed-course models

`course_prerequisites` stores a target course, its required course, and an
optional minimum letter grade. `completed_courses` stores a student's course
offering, grade, completion state, and completion date. Duplicate rules,
self-references, unsupported grades or states, and duplicate student/course
records are rejected by named database constraints.

The reusable `require_prerequisites_met` guard raises before selection
persistence when requirements are unmet. Issue #23 can call this guard while
adding draft-course management, keeping the eligibility rule authoritative in
one backend path.
