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
- http://127.0.0.1:8000/api/auth/register
- http://127.0.0.1:8000/api/auth/login
- http://127.0.0.1:8000/api/auth/me
- http://127.0.0.1:8000/docs

## Database

The backend creates local database tables automatically on startup.

Important files:

- `app/database.py`
- `app/models/advisor.py`
- `app/models/course.py`
- `app/models/department.py`
- `app/models/instructor.py`
- `app/models/program.py`
- `app/models/semester.py`
- `app/models/student.py`
- `app/models/user.py`
- `app/seed_data.py`

The core user and academic entities use UUID primary keys. If a local
`coursepilot.db` was created before the UUID model update, stop the backend,
delete that development-only database file, and restart the backend so
SQLAlchemy can create the current schema. This reset removes local demo data
and must not be used as a production migration strategy.

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
  "token": "<signed-jwt-access-token>",
  "user": {
    "id": "73f37649-8365-4b9d-a92e-584ebaabd0c7",
    "name": "New Student",
    "email": "student@example.com",
    "role": "student"
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
