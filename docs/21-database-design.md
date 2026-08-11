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

The existing `courses` table continues to provide the current catalogue API.
Its normalization into ERD course, section, schedule, and room entities is
handled by the corresponding course-model work.

Each current `courses` row includes a semester, section label, instructor,
capacity, and schedule, so it acts as the present section-offering record.
`registrations.section_id` and `waitlist_entries.section_id` therefore reference
the internal `courses.id`. The public catalogue identifier remains
`courses.course_id`.

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
- Required relationships use non-null foreign keys.

## Registration Query Indexes

- Student and registration status support student status pages.
- Section and registration status support seat and advisor workflows.
- Section, waitlist status, and joining time support deterministic active
  queue order without storing a fragile position number.
- User, read status, and creation time support unread-notification queries.
- Audit actor/entity indexes support chronological activity lookup.

## Authentication Compatibility

JWT subjects contain the authenticated user's UUID as a string. The backend
validates and converts the subject back to a UUID before querying the user.
API responses serialize user IDs as UUID strings.

## Data Access

The frontend does not access the database directly. It calls FastAPI routes,
which use repository functions and SQLAlchemy sessions.

## Local Database Lifecycle

SQLAlchemy creates missing tables automatically when the backend starts. It
does not alter an older table in place. Developers with a `coursepilot.db`
created before the UUID schema must remove that development-only file and
restart the backend. This reset removes local demo data and is not a production
migration strategy. Local database files remain ignored by Git.
