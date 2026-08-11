# API Design

## Overview

The CoursePilot API connects the React frontend with the FastAPI backend and SQLAlchemy database layer.

## Course Catalogue API

GET /api/courses

## Query Parameters

| Parameter | Type | Description |
|---|---|---|
| search | string | Search by course code or title |
| department | string | Filter by department |
| semester | string | Filter by semester |
| is_mandatory | boolean | Filter mandatory or elective courses |
| available_only | boolean | Show only courses with available seats |

## Example Request

GET /api/courses?search=CSE&department=CSE&available_only=true

## Example Response

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

## Status Codes

| Status Code | Meaning |
|---|---|
| 200 | Request successful |
| 409 | A unique database record already exists |
| 422 | Invalid query parameter, course, or section value |
| 500 | Database operation failed |

## Database Constraint Errors

SQLAlchemy integrity violations use a stable `detail` object. Known duplicate
course IDs and duplicate code/semester/section offerings return `409` with
`DUPLICATE_COURSE_ID` or `DUPLICATE_COURSE_SECTION`. Invalid credits, capacity,
available seats, or required text values return `422` with a field-specific
code and message.

Example:

```json
{
  "detail": {
    "code": "INVALID_AVAILABLE_SEATS",
    "message": "Available seats cannot be greater than section capacity."
  }
}
```

Unexpected integrity errors use `DATABASE_CONSTRAINT_VIOLATION` and do not
expose database statements, connection details, or stored values.
