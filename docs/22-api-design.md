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

Known duplicate course IDs and duplicate code/semester/section offerings
return `409` with `DUPLICATE_COURSE_ID` or
`DUPLICATE_COURSE_SECTION`. Invalid credits, capacity, available seats, or
required text values return `422` with a field-specific code and message.

Unexpected integrity errors use `DATABASE_CONSTRAINT_VIOLATION`. Repository
failures use `DATABASE_OPERATION_FAILED`. Neither response exposes raw
database information.
