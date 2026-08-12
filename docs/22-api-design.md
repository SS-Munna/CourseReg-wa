# API Design

## Overview

The CoursePilot API connects the React frontend with the FastAPI backend and
SQLAlchemy database layer. JSON application endpoints use the shared response
contract below. FastAPI's OpenAPI and documentation endpoints retain their
framework-defined formats.

## Shared Response Contract

### Successful response

Every successful response contains `success: true` and a `data` value. The
value may be an object, a list, or a scalar appropriate to the endpoint.

```json
{
  "success": true,
  "data": {
    "status": "ready"
  }
}
```

Authentication results follow the same structure:

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

### Error response

Every error contains `success: false` and an `error` object. Clients should
use `error.code` for program logic and `error.message` for a user-facing
explanation. The optional `details` value supplies safe structured context.

```json
{
  "success": false,
  "error": {
    "code": "DUPLICATE_COURSE_ID",
    "message": "A course with this course ID already exists."
  }
}
```

Unhandled server and database errors never include statements, connection
details, credentials, or stored values.

### Request validation error

Invalid body, path, and query values return HTTP `422`. Each issue identifies
its request field, validation message, and machine-readable validation type.

```json
{
  "success": false,
  "error": {
    "code": "REQUEST_VALIDATION_ERROR",
    "message": "The request contains invalid values.",
    "details": [
      {
        "field": "body.password",
        "message": "String should have at least 6 characters",
        "type": "string_too_short"
      }
    ]
  }
}
```

### Paginated response

Endpoints that paginate collections use the shared `pagination` object.
`total_pages` is zero when `total_items` is zero.

```json
{
  "success": true,
  "data": [],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 0,
    "total_pages": 0
  }
}
```

| Field | Rule |
|---|---|
| `page` | One-based page number; minimum `1` |
| `page_size` | Requested items per page; minimum `1` |
| `total_items` | Number of matching records; minimum `0` |
| `total_pages` | Ceiling of `total_items / page_size` |

## Course Catalogue API

```text
GET /api/courses
```

### Query Parameters

| Parameter | Type | Description |
|---|---|---|
| `search` | string | Search by course code or title |
| `department` | string | Filter by department |
| `semester` | string | Filter by semester |
| `is_mandatory` | boolean | Filter mandatory or elective courses |
| `available_only` | boolean | Show only courses with available seats |

Example request:

```text
GET /api/courses?search=CSE&department=CSE&available_only=true
```

Example response:

```json
{
  "success": true,
  "data": [
    {
      "course_id": "cse-101",
      "code": "CSE 101",
      "title": "Introduction to Computer Science",
      "department": "CSE",
      "semester": "Fall 2026",
      "instructor": "Dr. Rahman",
      "credits": 3,
      "capacity": 40,
      "available_seats": 12,
      "is_mandatory": true,
      "level": "Undergraduate",
      "description": "Introductory programming and computing concepts.",
      "prerequisites": [],
      "section": "A",
      "schedule": []
    }
  ]
}
```

Catalogue `available_seats` values and `available_only` filtering are derived
from the current number of approved registrations, not from a cached seat
value.

## Section Availability API

```text
GET /api/courses/{course_id}/availability
```

`course_id` is the public identifier of the current denormalized course-section
offering. Schedule entries carry their own room because a section may meet in
different rooms on different days.

Example response:

```json
{
  "success": true,
  "data": {
    "course_id": "cse-101",
    "code": "CSE 101",
    "title": "Introduction to Computer Science",
    "department": "CSE",
    "semester": "Fall 2026",
    "instructor": "Dr. Rahman",
    "credits": 3,
    "capacity": 40,
    "available_seats": 12,
    "is_mandatory": true,
    "level": "Undergraduate",
    "description": "Introductory programming and computing concepts.",
    "prerequisites": [],
    "section": "A",
    "schedule": [
      {
        "day": "Sunday",
        "start_time": "10:00",
        "end_time": "11:30",
        "room": "CSE-201"
      }
    ],
    "enrollment": 28,
    "is_full": false
  }
}
```

Availability follows the ERD rule: capacity minus the number of approved
registrations, clamped at zero. Other registration states do not consume a
seat. The endpoint recalculates on every request. Unknown identifiers return
`404 SECTION_NOT_FOUND`; repository failures use the shared safe `500`
response.

## Prerequisite Validation API

```text
GET /api/courses/{course_id}/prerequisite-validation
Authorization: Bearer <signed-jwt-access-token>
```

The endpoint is limited to authenticated student accounts and uses the
student profile linked to the JWT user. It does not accept another student's
identifier. The result remains a successful eligibility response when a rule
is unmet so the client can render all reasons before selection.

Example response:

```json
{
  "success": true,
  "data": {
    "course_id": "cse-301",
    "code": "CSE 301",
    "eligible": false,
    "requirements": [
      {
        "course_id": "cse-201",
        "code": "CSE 201",
        "title": "Data Structures",
        "minimum_grade": "B",
        "earned_grade": "C+",
        "satisfied": false,
        "reason": "minimum_grade_not_met"
      }
    ],
    "missing_prerequisites": [
      {
        "course_id": "cse-201",
        "code": "CSE 201",
        "title": "Data Structures",
        "minimum_grade": "B",
        "earned_grade": "C+",
        "satisfied": false,
        "reason": "minimum_grade_not_met"
      }
    ]
  }
}
```

`reason` is either `not_completed` or `minimum_grade_not_met`. A course with
no requirements returns `eligible: true` and empty lists. The repository also
provides a blocking guard for selection writes; it raises before persistence
when `eligible` is false. Missing tokens return `401`, non-student roles return
`403`, missing student profiles or course IDs return `404`, invalid path
values return `422`, and database failures return a safe `500` response.

## Draft Selection API

```text
GET /api/selections
POST /api/selections
GET /api/selections/credit-validation
POST /api/selections/credit-validation
GET /api/selections/schedule-conflict-validation
POST /api/selections/schedule-conflict-validation
DELETE /api/selections/{course_id}
Authorization: Bearer <signed-jwt-access-token>
```

These routes are limited to student accounts and always derive the student
profile from the authenticated user. A client cannot list or mutate another
student's selections by supplying an identifier.

Example create request:

```json
{
  "course_id": "cse-201"
}
```

Example `201 Created` response:

```json
{
  "success": true,
  "data": {
    "registration_id": "3eca41e7-45bc-498a-8d29-58428aa6355c",
    "registration_status": "draft",
    "course": {
      "course_id": "cse-201",
      "code": "CSE 201",
      "title": "Data Structures",
      "department": "CSE",
      "semester": "Fall 2026",
      "instructor": "Dr. Ahmed",
      "credits": 3,
      "capacity": 35,
      "available_seats": 8,
      "is_mandatory": true,
      "level": "Undergraduate",
      "description": "Linear and nonlinear data structures.",
      "prerequisites": ["CSE 101"],
      "section": "A",
      "schedule": []
    }
  }
}
```

Creation calls the prerequisite and schedule-conflict guards before inserting.
An unmet rule returns `422 PREREQUISITES_NOT_MET` with the same structured
eligibility data as the validation endpoint. An overlap returns
`409 SCHEDULE_CONFLICT` with both course and time details. Either result leaves
the transaction without a new registration. An unknown public course ID
returns `404 SECTION_NOT_FOUND`.

Repeated selection is blocked by an application lookup and the database's
student/section unique constraint. Both paths return
`409 DUPLICATE_SELECTION`. `GET` returns only current draft records. `DELETE`
returns the removed registration and public course identifiers; a missing or
foreign draft returns `404 DRAFT_SELECTION_NOT_FOUND`, and a matching
non-draft registration returns `409 SELECTION_NOT_DRAFT`.

Current available seats in selection responses are calculated from approved
registrations. Draft records do not reduce the seat count. Each selection
list, create, and remove response also includes the current
`credit_validation` object so clients can update the displayed credit total
from the same response.

## Credit Validation API

`GET /api/selections/credit-validation` returns the authenticated student's
current active credit load and program limits:

```json
{
  "success": true,
  "data": {
    "selected_credits": 12,
    "minimum_credit": 9,
    "maximum_credit": 18,
    "validation_status": "within_range",
    "is_valid": true,
    "minimum_shortfall": 0,
    "maximum_excess": 0,
    "message": "The selected credit load is within the allowed range."
  }
}
```

Draft, pending, and approved registrations count; rejected and dropped rows
do not. The total and limits are database-derived on every request.

`POST /api/selections/credit-validation` runs the reusable final-load guard
without submitting or changing any registration. A valid inclusive range
returns the same `200` response. Below-minimum and above-maximum loads return
`422 CREDIT_LOAD_BELOW_MINIMUM` or `422 CREDIT_LOAD_ABOVE_MAXIMUM`; `details`
contains the complete calculation, including the current total and exact
shortfall or excess. The final registration transaction in Issue #27 will
call this same guard before moving draft records to pending.

## Schedule-Conflict Validation API

```text
GET /api/selections/schedule-conflict-validation
POST /api/selections/schedule-conflict-validation
Authorization: Bearer <signed-jwt-access-token>
```

`GET` returns all current overlaps without changing registration data. A
conflict-free response is:

```json
{
  "success": true,
  "data": {
    "has_conflicts": false,
    "conflict_count": 0,
    "conflicts": [],
    "message": "No schedule conflicts were found."
  }
}
```

`POST` invokes the reusable blocking guard intended for final submission. It
returns the same `200` response when conflict-free. A conflict returns
`409 SCHEDULE_CONFLICT` with safe structured details:

```json
{
  "success": false,
  "error": {
    "code": "SCHEDULE_CONFLICT",
    "message": "Schedule conflict detected. CSE 305, Section B overlaps with CSE 301, Section A on Sunday from 11:00 to 11:30. Remove one course or choose another section.",
    "details": {
      "has_conflicts": true,
      "conflict_count": 1,
      "conflicts": [
        {
          "selected_course": {
            "course_id": "cse-305-b",
            "code": "CSE 305",
            "title": "Database Laboratory",
            "section": "B",
            "registration_status": "draft",
            "start_time": "11:00",
            "end_time": "12:15"
          },
          "conflicting_course": {
            "course_id": "cse-301-a",
            "code": "CSE 301",
            "title": "Database Systems",
            "section": "A",
            "registration_status": "approved",
            "start_time": "10:00",
            "end_time": "11:30"
          },
          "day": "Sunday",
          "overlap_start_time": "11:00",
          "overlap_end_time": "11:30",
          "message": "Schedule conflict detected. CSE 305, Section B overlaps with CSE 301, Section A on Sunday from 11:00 to 11:30. Remove one course or choose another section."
        }
      ],
      "message": "1 schedule conflict was found."
    }
  }
}
```

Candidate selection compares against the authenticated student's `draft`,
`pending`, and `approved` registrations. `rejected` and `dropped` records are
ignored. Only offerings in the same normalized semester can conflict. Days are
matched case-insensitively after whitespace normalization, and every weekly
meeting is checked. The strict overlap rule permits adjacent meetings whose
boundary times are equal. Stored times must use 24-hour `HH:MM` format;
malformed stored values return a safe `500 DATABASE_OPERATION_FAILED`.

## Seat Allocation Service Contract

Issue #26 adds no public route. It provides the repository operation that
future advisor approval and waiting-list promotion routes must call instead of
writing `registration_status = 'approved'` directly.

The operation accepts a registration UUID and, on success, returns:

- Registration, student, public course, code, and section identifiers.
- The final `approved` state.
- Whether this call newly allocated the seat or was an idempotent retry.
- Section capacity, approved enrollment, and remaining seats.

Only `pending` records can receive a new seat. Missing registrations,
non-pending states, full sections, and repository failures are distinct typed
errors so later routes can map them to stable safe API responses. The full
error includes only safe capacity values; raw database errors must continue to
use `DATABASE_OPERATION_FAILED` at the HTTP boundary.

PostgreSQL locks the section row and recounts approved enrollment in the same
transaction before changing status. A concurrent request for the same final
seat waits, then observes the committed approval and receives the full-section
result. SQLite local/test transactions use a process mutex because SQLite does
not implement `SELECT ... FOR UPDATE`.

## Status Codes

| Status Code | Meaning |
|---|---|
| `200` | Request successful |
| `201` | Resource created successfully |
| `400` | Request cannot be processed |
| `401` | Authentication is required or invalid |
| `403` | Authenticated user lacks permission |
| `404` | Resource or route not found |
| `409` | Request conflicts with an existing record |
| `422` | Request or stored value violates validation rules |
| `500` | Unexpected server or database operation failure |

## Database Constraint Errors

Known duplicate course IDs, code/semester/section offerings, and student
section selections return `409` with `DUPLICATE_COURSE_ID`,
`DUPLICATE_COURSE_SECTION`, or `DUPLICATE_SELECTION`. Invalid credits,
capacity, available seats, or required text values return `422` with a
field-specific code and message.

Unexpected integrity errors use `DATABASE_CONSTRAINT_VIOLATION`. Repository
failures use `DATABASE_OPERATION_FAILED`. Neither response exposes raw
database information.
