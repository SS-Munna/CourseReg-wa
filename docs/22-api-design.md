# CoursePilot REST API Design

## 1. Introduction

This document defines the proposed REST API design for CoursePilot.

The API connects the React frontend with the FastAPI backend and PostgreSQL database.

It supports:

* Authentication and authorization
* Course browsing and searching
* Course-section management
* Registration validation
* Final registration submission
* Waiting-list management
* Advisor approval and rejection
* Student schedule retrieval
* Notifications
* Department administration
* User and role administration

---

# 2. API Technology

| Item                 | Technology             |
| -------------------- | ---------------------- |
| Backend Framework    | FastAPI                |
| Programming Language | Python                 |
| API Style            | REST                   |
| Data Format          | JSON                   |
| Authentication       | JSON Web Token         |
| Request Validation   | Pydantic               |
| Database Access      | SQLAlchemy             |
| Database             | PostgreSQL             |
| API Documentation    | OpenAPI and Swagger UI |

---

# 3. Base URL

The development API base URL may be:

```text
http://localhost:8000/api/v1
```

A deployed API may use:

```text
https://api.coursepilot.example.com/api/v1
```

All endpoints in this document are written relative to:

```text
/api/v1
```

---

# 4. General API Principles

The CoursePilot API should follow these principles:

1. Use nouns for resource URLs.
2. Use standard HTTP methods.
3. Use JSON request and response bodies.
4. Use standard HTTP status codes.
5. Require authentication for protected endpoints.
6. Enforce role permissions in the backend.
7. Validate all incoming data.
8. Return consistent success and error responses.
9. Use pagination for large result sets.
10. Use transactions for registration and seat-allocation operations.
11. Avoid exposing internal database or server information.
12. Version the API using `/api/v1`.

---

# 5. HTTP Methods

| Method   | Purpose                                |
| -------- | -------------------------------------- |
| `GET`    | Retrieve one or more resources         |
| `POST`   | Create a resource or perform an action |
| `PUT`    | Replace an existing resource           |
| `PATCH`  | Partially update a resource            |
| `DELETE` | Remove or deactivate a resource        |

---

# 6. Authentication

## 6.1 Authorization Header

Protected requests must include:

```http
Authorization: Bearer <access_token>
```

## 6.2 Token Information

A JWT access token may contain:

```json
{
  "sub": "47bb4682-cb1e-4207-9686-71fa7bafcb50",
  "role": "STUDENT",
  "exp": 1781726400
}
```

## 6.3 Authentication Rules

The backend must verify:

* Token signature
* Token expiration
* User existence
* Account status
* Required role
* Resource ownership

---

# 7. Standard Success Response

A normal single-resource response may use:

```json
{
  "success": true,
  "data": {
    "id": "resource-uuid"
  }
}
```

A list response may use:

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

---

# 8. Standard Error Response

```json
{
  "success": false,
  "error": {
    "code": "SCHEDULE_CONFLICT",
    "message": "The selected section conflicts with an existing course.",
    "details": {
      "selected_course": "CSE 301",
      "conflicting_course": "CSE 305",
      "day": "Sunday",
      "start_time": "10:00:00",
      "end_time": "11:30:00"
    }
  }
}
```

---

# 9. HTTP Status Codes

| Status Code                 | Meaning                                     |
| --------------------------- | ------------------------------------------- |
| `200 OK`                    | Request completed successfully              |
| `201 Created`               | Resource created successfully               |
| `204 No Content`            | Operation completed without a response body |
| `400 Bad Request`           | Invalid request format                      |
| `401 Unauthorized`          | Authentication failed or token is missing   |
| `403 Forbidden`             | User does not have permission               |
| `404 Not Found`             | Requested resource does not exist           |
| `409 Conflict`              | Resource or business-rule conflict          |
| `422 Unprocessable Entity`  | Input or business validation failed         |
| `429 Too Many Requests`     | Request limit exceeded                      |
| `500 Internal Server Error` | Unexpected server error                     |
| `503 Service Unavailable`   | Service temporarily unavailable             |

---

# 10. Pagination and Filtering

List endpoints should support pagination.

Example:

```http
GET /courses?page=1&page_size=20
```

Common pagination parameters:

| Parameter    | Type    | Description                |
| ------------ | ------- | -------------------------- |
| `page`       | Integer | Requested page number      |
| `page_size`  | Integer | Number of records per page |
| `sort_by`    | String  | Field used for sorting     |
| `sort_order` | String  | `asc` or `desc`            |

The maximum page size should be limited to prevent very large responses.

---

# 11. API Endpoint Summary

| Resource Group       | Base Path               |
| -------------------- | ----------------------- |
| Authentication       | `/auth`                 |
| Current User         | `/users/me`             |
| Users                | `/users`                |
| Students             | `/students`             |
| Courses              | `/courses`              |
| Sections             | `/sections`             |
| Registrations        | `/registrations`        |
| Waiting Lists        | `/waitlists`            |
| Advisor Functions    | `/advisor`              |
| Student Schedule     | `/schedules`            |
| Notifications        | `/notifications`        |
| Registration Periods | `/registration-periods` |
| Departments          | `/departments`          |
| Programs             | `/programs`             |
| Rooms                | `/rooms`                |
| Audit Logs           | `/audit-logs`           |

---

# 12. Authentication Endpoints

## 12.1 Login

```http
POST /auth/login
```

### Access

Public

### Request

```json
{
  "email": "student@example.com",
  "password": "user-password"
}
```

### Successful Response

```json
{
  "success": true,
  "data": {
    "access_token": "jwt-token",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "id": "user-uuid",
      "email": "student@example.com",
      "full_name": "Arafat Hossain",
      "role": "STUDENT"
    }
  }
}
```

### Possible Errors

* `INVALID_CREDENTIALS`
* `ACCOUNT_INACTIVE`
* `ACCOUNT_SUSPENDED`

### Related Requirements

* FR-001
* FR-002
* FR-004
* FR-005

---

## 12.2 Logout

```http
POST /auth/logout
```

### Access

Authenticated users

### Response

```json
{
  "success": true,
  "message": "Logged out successfully."
}
```

### Related Requirement

* FR-003

---

## 12.3 Get Current User

```http
GET /users/me
```

### Access

Authenticated users

### Response

```json
{
  "success": true,
  "data": {
    "id": "user-uuid",
    "email": "student@example.com",
    "full_name": "Arafat Hossain",
    "role": "STUDENT",
    "account_status": "ACTIVE"
  }
}
```

---

# 13. Course Endpoints

## 13.1 List Courses

```http
GET /courses
```

### Access

Authenticated users

### Query Parameters

| Parameter             | Example           | Description                 |
| --------------------- | ----------------- | --------------------------- |
| `search`              | `data structures` | Searches code or title      |
| `department_id`       | UUID              | Filters by department       |
| `semester_id`         | UUID              | Filters available sections  |
| `course_level`        | `300`             | Filters by course level     |
| `is_mandatory`        | `true`            | Filters mandatory courses   |
| `has_available_seats` | `true`            | Filters sections with seats |
| `page`                | `1`               | Page number                 |
| `page_size`           | `20`              | Records per page            |

### Response

```json
{
  "success": true,
  "data": [
    {
      "id": "course-uuid",
      "course_code": "CSE 301",
      "course_title": "Database Systems",
      "credit_value": 3.0,
      "is_mandatory": true,
      "department": {
        "id": "department-uuid",
        "department_code": "CSE"
      }
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 1,
    "total_pages": 1
  }
}
```

### Related Requirements

* FR-009
* FR-010
* FR-011
* FR-013

---

## 13.2 Get Course Details

```http
GET /courses/{course_id}
```

### Access

Authenticated users

### Response

```json
{
  "success": true,
  "data": {
    "id": "course-uuid",
    "course_code": "CSE 301",
    "course_title": "Database Systems",
    "course_description": "Introduction to database design and management.",
    "credit_value": 3.0,
    "course_level": 300,
    "course_type": "THEORY",
    "is_mandatory": true,
    "prerequisites": [
      {
        "course_id": "prerequisite-uuid",
        "course_code": "CSE 201",
        "course_title": "Data Structures",
        "minimum_grade": "C"
      }
    ]
  }
}
```

### Related Requirements

* FR-012
* FR-025

---

## 13.3 Create Course

```http
POST /courses
```

### Access

Department administrator or system administrator

### Request

```json
{
  "department_id": "department-uuid",
  "course_code": "CSE 301",
  "course_title": "Database Systems",
  "course_description": "Introduction to database systems.",
  "credit_value": 3.0,
  "course_level": 300,
  "course_type": "THEORY",
  "is_mandatory": true
}
```

### Response

`201 Created`

### Related Requirements

* FR-071
* FR-080

---

## 13.4 Update Course

```http
PATCH /courses/{course_id}
```

### Access

Department administrator or system administrator

### Related Requirement

* FR-072

---

## 13.5 Configure Course Prerequisites

```http
PUT /courses/{course_id}/prerequisites
```

### Access

Department administrator or system administrator

### Request

```json
{
  "prerequisites": [
    {
      "prerequisite_course_id": "course-uuid",
      "minimum_grade": "C"
    }
  ]
}
```

### Related Requirement

* FR-079

---

# 14. Course Section Endpoints

## 14.1 List Course Sections

```http
GET /sections
```

### Query Parameters

* `course_id`
* `semester_id`
* `instructor_id`
* `section_status`
* `has_available_seats`
* `page`
* `page_size`

### Response

```json
{
  "success": true,
  "data": [
    {
      "id": "section-uuid",
      "section_number": "A",
      "course": {
        "course_code": "CSE 301",
        "course_title": "Database Systems",
        "credit_value": 3.0
      },
      "instructor": {
        "id": "instructor-uuid",
        "full_name": "Dr. Rahman"
      },
      "seat_capacity": 40,
      "approved_count": 35,
      "available_seats": 5,
      "schedules": [
        {
          "day_of_week": "SUNDAY",
          "start_time": "10:00:00",
          "end_time": "11:30:00",
          "room": "Room 401"
        }
      ]
    }
  ]
}
```

### Related Requirements

* FR-009
* FR-012
* FR-014
* FR-015

---

## 14.2 Get Section Details

```http
GET /sections/{section_id}
```

### Access

Authenticated users

### Related Requirements

* FR-012
* FR-014
* FR-018

---

## 14.3 Create Course Section

```http
POST /sections
```

### Access

Department administrator or system administrator

### Request

```json
{
  "course_id": "course-uuid",
  "semester_id": "semester-uuid",
  "instructor_id": "instructor-uuid",
  "section_number": "A",
  "seat_capacity": 40,
  "section_status": "OPEN",
  "schedules": [
    {
      "room_id": "room-uuid",
      "day_of_week": "SUNDAY",
      "start_time": "10:00:00",
      "end_time": "11:30:00"
    }
  ]
}
```

### Related Requirements

* FR-073
* FR-075
* FR-076
* FR-077
* FR-078

---

## 14.4 Update Course Section

```http
PATCH /sections/{section_id}
```

### Access

Department administrator or system administrator

### Related Requirements

* FR-074
* FR-075
* FR-076
* FR-077
* FR-078
* FR-083

---

## 14.5 View Section Enrollment

```http
GET /sections/{section_id}/enrollment
```

### Access

Department administrator, academic advisor, or system administrator

### Response

```json
{
  "success": true,
  "data": {
    "section_id": "section-uuid",
    "seat_capacity": 40,
    "approved_count": 40,
    "pending_count": 3,
    "available_seats": 0,
    "waitlist_count": 8
  }
}
```

### Related Requirements

* FR-082
* FR-084

---

# 15. Student Course-Selection Endpoints

## 15.1 View Selected Courses

```http
GET /registrations/selections
```

### Access

Student

### Response

```json
{
  "success": true,
  "data": {
    "selected_courses": [
      {
        "registration_id": "registration-uuid",
        "section_id": "section-uuid",
        "course_code": "CSE 301",
        "section_number": "A",
        "credit_value": 3.0,
        "registration_status": "DRAFT"
      }
    ],
    "selected_credits": 3.0,
    "minimum_credit": 9.0,
    "maximum_credit": 18.0
  }
}
```

### Related Requirements

* FR-020
* FR-029
* FR-030
* FR-031

---

## 15.2 Select Course Section

```http
POST /registrations/selections
```

### Access

Student

### Request

```json
{
  "section_id": "section-uuid"
}
```

### Backend Validation

The backend checks:

* Registration period
* Duplicate selection
* Previously completed course
* Prerequisites
* Schedule conflict
* Section status
* Seat availability

### Successful Response

```json
{
  "success": true,
  "data": {
    "registration_id": "registration-uuid",
    "registration_status": "DRAFT",
    "selected_credits": 12.0
  }
}
```

### Possible Errors

* `REGISTRATION_CLOSED`
* `DUPLICATE_REGISTRATION`
* `COURSE_ALREADY_COMPLETED`
* `MISSING_PREREQUISITE`
* `SCHEDULE_CONFLICT`
* `SECTION_FULL`

### Related Requirements

* FR-019
* FR-022
* FR-023
* FR-026
* FR-027
* FR-035
* FR-038

---

## 15.3 Remove Selected Course

```http
DELETE /registrations/selections/{registration_id}
```

### Access

Student and owner of the registration

### Response

`204 No Content`

### Related Requirement

* FR-021

---

## 15.4 Validate Registration Selection

```http
POST /registrations/validate
```

### Access

Student

### Request

```json
{
  "section_ids": [
    "section-uuid-1",
    "section-uuid-2"
  ]
}
```

### Response

```json
{
  "success": true,
  "data": {
    "valid": false,
    "selected_credits": 6.0,
    "minimum_credit": 9.0,
    "maximum_credit": 18.0,
    "errors": [
      {
        "code": "MINIMUM_CREDIT_NOT_MET",
        "message": "At least 9 credits are required."
      }
    ]
  }
}
```

### Related Requirements

* FR-025 to FR-040

---

# 16. Final Registration Endpoints

## 16.1 View Registration Summary

```http
GET /registrations/summary
```

### Access

Student

### Response

The response should include:

* Selected courses
* Total selected credits
* Minimum and maximum credits
* Prerequisite results
* Conflict results
* Seat status
* Registration-period status

### Related Requirement

* FR-051

---

## 16.2 Submit Final Registration

```http
POST /registrations/submit
```

### Access

Student

### Request

```json
{
  "confirm": true
}
```

### Processing

The backend must:

1. Begin a database transaction.
2. Lock relevant section records.
3. Recheck the registration period.
4. Recheck prerequisites.
5. Recheck credit limits.
6. Recheck schedule conflicts.
7. Recheck duplicate and completed courses.
8. Recheck seat availability.
9. Change valid records to `PENDING`.
10. Create notification and audit records.
11. Commit the transaction.

### Successful Response

```json
{
  "success": true,
  "data": {
    "status": "PENDING",
    "submitted_at": "2026-06-18T09:30:00Z",
    "message": "Registration submitted for advisor review."
  }
}
```

### Possible Errors

* `REGISTRATION_CLOSED`
* `MISSING_PREREQUISITE`
* `SCHEDULE_CONFLICT`
* `MINIMUM_CREDIT_NOT_MET`
* `MAXIMUM_CREDIT_EXCEEDED`
* `SECTION_FULL`
* `DUPLICATE_REGISTRATION`

### Related Requirements

* FR-052 to FR-057
* FR-097 to FR-100

---

## 16.3 View Registration Status

```http
GET /registrations
```

### Access

Student

### Query Parameters

* `semester_id`
* `status`

### Related Requirements

* FR-058
* FR-059
* FR-060

---

## 16.4 Drop Approved Course

```http
POST /registrations/{registration_id}/drop
```

### Access

Student and registration owner

### Processing

The system must:

* Confirm Approved status
* Confirm the drop deadline has not passed
* Change status to Dropped
* Release the seat
* Process the waiting list
* Notify the student
* Record the action

### Related Requirement

* FR-061

---

# 17. Waiting-List Endpoints

## 17.1 Join Waiting List

```http
POST /sections/{section_id}/waitlist
```

### Access

Student

### Backend Validation

* Section is full
* Registration period is open
* Student is not already registered
* Student is not already waitlisted
* Prerequisites are complete
* No schedule conflict exists

### Successful Response

```json
{
  "success": true,
  "data": {
    "waitlist_entry_id": "waitlist-uuid",
    "section_id": "section-uuid",
    "waitlist_status": "ACTIVE",
    "queue_position": 4,
    "joined_at": "2026-06-18T09:40:00Z"
  }
}
```

### Related Requirements

* FR-041
* FR-042
* FR-043
* FR-044
* FR-046

---

## 17.2 View Student Waiting Lists

```http
GET /waitlists/me
```

### Access

Student

### Response

```json
{
  "success": true,
  "data": [
    {
      "id": "waitlist-uuid",
      "course_code": "CSE 401",
      "course_title": "Artificial Intelligence",
      "section_number": "A",
      "queue_position": 4,
      "total_waiting": 12,
      "waitlist_status": "ACTIVE",
      "joined_at": "2026-06-18T09:40:00Z"
    }
  ]
}
```

### Related Requirements

* FR-044
* FR-045

---

## 17.3 Leave Waiting List

```http
DELETE /waitlists/{waitlist_entry_id}
```

### Access

Student and waitlist-entry owner

### Response

`204 No Content`

### Related Requirements

* FR-047
* FR-048

---

## 17.4 View Section Waiting List

```http
GET /sections/{section_id}/waitlist
```

### Access

Department administrator, academic advisor, or system administrator

### Response

```json
{
  "success": true,
  "data": [
    {
      "student_id": "student-uuid",
      "student_number": "2026-001",
      "student_name": "Arafat Hossain",
      "queue_position": 1,
      "waitlist_status": "ACTIVE",
      "joined_at": "2026-06-18T08:30:00Z"
    }
  ]
}
```

### Related Requirement

* FR-084

---

## 17.5 Process Waiting List

```http
POST /sections/{section_id}/waitlist/process
```

### Access

Department administrator or system administrator

This endpoint may also be called internally after:

* Course drop
* Capacity increase
* Registration rejection
* Seat cancellation

### Related Requirements

* FR-049
* FR-050

---

# 18. Advisor Endpoints

## 18.1 View Pending Requests

```http
GET /advisor/requests
```

### Access

Academic advisor

### Query Parameters

* `status`
* `student_id`
* `semester_id`
* `page`
* `page_size`

### Related Requirements

* FR-063
* FR-064

---

## 18.2 View Registration Request Details

```http
GET /advisor/requests/{registration_id}
```

### Access

Assigned academic advisor

### Response

```json
{
  "success": true,
  "data": {
    "registration_id": "registration-uuid",
    "student": {
      "id": "student-uuid",
      "student_number": "2026-001",
      "full_name": "Arafat Hossain"
    },
    "course": {
      "course_code": "CSE 301",
      "course_title": "Database Systems",
      "section_number": "A"
    },
    "total_selected_credits": 12.0,
    "prerequisite_result": "PASSED",
    "conflict_result": "NO_CONFLICT",
    "registration_status": "PENDING"
  }
}
```

### Related Requirement

* FR-065

---

## 18.3 Approve Registration

```http
POST /advisor/requests/{registration_id}/approve
```

### Access

Assigned academic advisor

### Request

```json
{
  "comment": "Approved based on the student's study plan."
}
```

### Response

```json
{
  "success": true,
  "data": {
    "registration_id": "registration-uuid",
    "registration_status": "APPROVED",
    "reviewed_at": "2026-06-18T10:15:00Z"
  }
}
```

### Related Requirements

* FR-066
* FR-069
* FR-070

---

## 18.4 Reject Registration

```http
POST /advisor/requests/{registration_id}/reject
```

### Access

Assigned academic advisor

### Request

```json
{
  "reason": "The selected credit load is not suitable for the student's current academic standing."
}
```

The rejection reason is required.

### Related Requirements

* FR-067
* FR-068
* FR-069
* FR-070

---

# 19. Student Schedule Endpoints

## 19.1 View Approved Schedule

```http
GET /schedules/me
```

### Access

Student

### Query Parameters

* `semester_id`
* `view=list`
* `view=weekly`

### Response

```json
{
  "success": true,
  "data": {
    "semester": {
      "id": "semester-uuid",
      "name": "Summer 2026"
    },
    "total_credits": 12.0,
    "courses": [
      {
        "course_code": "CSE 301",
        "course_title": "Database Systems",
        "section_number": "A",
        "instructor": "Dr. Rahman",
        "credit_value": 3.0,
        "registration_status": "APPROVED",
        "schedules": [
          {
            "day_of_week": "SUNDAY",
            "start_time": "10:00:00",
            "end_time": "11:30:00",
            "room": "Room 401"
          }
        ]
      }
    ]
  }
}
```

### Related Requirements

* FR-085
* FR-086
* FR-087
* FR-088

---

# 20. Notification Endpoints

## 20.1 List Notifications

```http
GET /notifications
```

### Access

Authenticated users

### Query Parameters

* `is_read`
* `page`
* `page_size`

### Related Requirements

* FR-089
* FR-090
* FR-091

---

## 20.2 Mark Notification as Read

```http
PATCH /notifications/{notification_id}/read
```

### Access

Notification owner

### Response

```json
{
  "success": true,
  "data": {
    "id": "notification-uuid",
    "is_read": true,
    "read_at": "2026-06-18T10:30:00Z"
  }
}
```

---

## 20.3 Mark All Notifications as Read

```http
PATCH /notifications/read-all
```

### Access

Authenticated users

---

# 21. Registration-Period Endpoints

## 21.1 View Active Registration Period

```http
GET /registration-periods/active
```

### Access

Authenticated users

### Response

```json
{
  "success": true,
  "data": {
    "id": "registration-period-uuid",
    "semester_id": "semester-uuid",
    "opening_time": "2026-06-10T08:00:00Z",
    "closing_time": "2026-06-20T17:00:00Z",
    "drop_deadline": "2026-06-25T17:00:00Z",
    "minimum_credit": 9.0,
    "maximum_credit": 18.0,
    "status": "OPEN"
  }
}
```

### Related Requirements

* FR-007
* FR-031
* FR-057

---

## 21.2 Create Registration Period

```http
POST /registration-periods
```

### Access

Department administrator or system administrator

### Related Requirement

* FR-081

---

## 21.3 Update Registration Period

```http
PATCH /registration-periods/{period_id}
```

### Access

Department administrator or system administrator

### Related Requirement

* FR-081

---

# 22. Department and Program Endpoints

## 22.1 List Departments

```http
GET /departments
```

## 22.2 Create Department

```http
POST /departments
```

### Access

System administrator

## 22.3 List Programs

```http
GET /programs
```

## 22.4 Create Program

```http
POST /programs
```

### Access

Department administrator or system administrator

---

# 23. Room Endpoints

## 23.1 List Rooms

```http
GET /rooms
```

## 23.2 Create Room

```http
POST /rooms
```

### Access

Department administrator or system administrator

## 23.3 Update Room

```http
PATCH /rooms/{room_id}
```

### Access

Department administrator or system administrator

### Related Requirement

* FR-077

---

# 24. User Administration Endpoints

## 24.1 List Users

```http
GET /users
```

### Access

System administrator

### Query Parameters

* `search`
* `role`
* `account_status`
* `page`
* `page_size`

### Related Requirement

* FR-092

---

## 24.2 Create User

```http
POST /users
```

### Access

System administrator

### Request

```json
{
  "email": "newuser@example.com",
  "full_name": "Samiul Tamim",
  "role": "SYSTEM_ADMIN",
  "temporary_password": "temporary-password"
}
```

### Related Requirements

* FR-092
* FR-093

---

## 24.3 Update User

```http
PATCH /users/{user_id}
```

### Access

System administrator

### Related Requirement

* FR-092

---

## 24.4 Activate or Deactivate User

```http
PATCH /users/{user_id}/status
```

### Request

```json
{
  "account_status": "INACTIVE"
}
```

### Related Requirement

* FR-092

---

## 24.5 Update User Role

```http
PATCH /users/{user_id}/role
```

### Request

```json
{
  "role": "DEPARTMENT_ADMIN"
}
```

### Related Requirements

* FR-093
* FR-094
* FR-096

---

# 25. Audit Log Endpoints

## 25.1 View Audit Logs

```http
GET /audit-logs
```

### Access

System administrator

### Query Parameters

* `user_id`
* `action_type`
* `entity_type`
* `entity_id`
* `start_date`
* `end_date`
* `page`
* `page_size`

### Related Requirements

* FR-095
* FR-096

Audit-log endpoints must not allow normal users to edit or delete audit records.

---

# 26. Role-Permission Matrix

| API Area                   | Student | Advisor | Department Admin | System Admin |
| -------------------------- | ------: | ------: | ---------------: | -----------: |
| Login                      |     Yes |     Yes |              Yes |          Yes |
| View own profile           |     Yes |     Yes |              Yes |          Yes |
| Browse courses             |     Yes |     Yes |              Yes |          Yes |
| Select courses             |     Yes |      No |               No |           No |
| Submit registration        |     Yes |      No |               No |           No |
| Join waiting list          |     Yes |      No |               No |           No |
| View own schedule          |     Yes |      No |               No |           No |
| Review assigned requests   |      No |     Yes |               No |          Yes |
| Approve or reject requests |      No |     Yes |               No |          Yes |
| Manage courses             |      No |      No |              Yes |          Yes |
| Manage sections            |      No |      No |              Yes |          Yes |
| Manage capacities          |      No |      No |              Yes |          Yes |
| Monitor waiting lists      |      No | Limited |              Yes |          Yes |
| Manage users and roles     |      No |      No |               No |          Yes |
| View audit logs            |      No |      No |          Limited |          Yes |

---

# 27. Main Error Codes

| Error Code                  | Description                                            |
| --------------------------- | ------------------------------------------------------ |
| `INVALID_CREDENTIALS`       | Login credentials are incorrect                        |
| `ACCOUNT_INACTIVE`          | User account is inactive                               |
| `UNAUTHORIZED`              | Authentication is required                             |
| `FORBIDDEN`                 | User lacks required permission                         |
| `RESOURCE_NOT_FOUND`        | Requested resource does not exist                      |
| `DUPLICATE_REGISTRATION`    | Student already selected or registered for the section |
| `COURSE_ALREADY_COMPLETED`  | Student previously passed the course                   |
| `MISSING_PREREQUISITE`      | Required prerequisite is missing                       |
| `SCHEDULE_CONFLICT`         | Course schedule overlaps another course                |
| `MINIMUM_CREDIT_NOT_MET`    | Selected credits are below the minimum                 |
| `MAXIMUM_CREDIT_EXCEEDED`   | Selected credits exceed the maximum                    |
| `SECTION_FULL`              | No direct seat is available                            |
| `DUPLICATE_WAITLIST_ENTRY`  | Student is already waitlisted                          |
| `REGISTRATION_CLOSED`       | Registration period is not open                        |
| `DROP_DEADLINE_PASSED`      | Course can no longer be dropped                        |
| `INVALID_STATUS_TRANSITION` | Requested status change is not allowed                 |
| `DATABASE_ERROR`            | Database operation failed                              |
| `INTERNAL_SERVER_ERROR`     | Unexpected application failure                         |

---

# 28. Validation Rules

The API must validate:

* Valid UUID formats
* Required request fields
* Email format
* Positive seat capacities
* Positive credit values
* End time later than start time
* Registration opening time before closing time
* Maximum credits not below minimum credits
* Supported user roles
* Supported registration statuses
* Supported waiting-list statuses
* Required rejection reasons
* Unique course codes
* Unique user emails
* Unique student registrations
* Unique waiting-list entries

---

# 29. Concurrency and Transaction Requirements

Database transactions are required for:

* Final registration submission
* Advisor approval
* Course dropping
* Section-capacity changes
* Waiting-list promotion
* Final-seat allocation

During seat allocation, the backend should lock the related section row.

```sql
SELECT id, seat_capacity
FROM course_sections
WHERE id = :section_id
FOR UPDATE;
```

This prevents two students from receiving the same final available seat.

---

# 30. API Security

The API shall:

* Require HTTPS in production
* Hash passwords securely
* Validate JWT tokens
* Enforce token expiration
* Enforce role-based permissions
* Check resource ownership
* Validate request data
* Use SQLAlchemy or parameterized queries
* Limit repeated login attempts
* Avoid exposing stack traces
* Avoid returning password hashes
* Avoid logging tokens or passwords
* Store secrets in environment variables

---

# 31. Rate Limiting

Sensitive endpoints should support rate limits.

Examples include:

| Endpoint                | Suggested Limit              |
| ----------------------- | ---------------------------- |
| `POST /auth/login`      | 5 failed attempts per minute |
| Course-search endpoints | 60 requests per minute       |
| Registration submission | 10 requests per minute       |
| Waiting-list actions    | 10 requests per minute       |

Rate limits may be adjusted based on actual usage.

---

# 32. API Logging

Each API request should record:

* Request identifier
* Timestamp
* HTTP method
* Request path
* Response status
* Processing time
* Authenticated user ID, when available

Logs must not store:

* Passwords
* Password hashes
* Access tokens
* Secret keys
* Database passwords

---

# 33. API Documentation

FastAPI should automatically provide OpenAPI documentation.

During development, documentation may be available at:

```text
/docs
```

Alternative OpenAPI documentation may be available at:

```text
/redoc
```

Production access to these pages may be restricted.

---

# 34. API Testing

## 34.1 Authentication Tests

Test:

* Valid login
* Invalid login
* Inactive account
* Missing token
* Expired token
* Incorrect user role

## 34.2 Course Tests

Test:

* Course listing
* Search
* Filtering
* Pagination
* Course details
* Course creation permissions

## 34.3 Registration Tests

Test:

* Successful course selection
* Duplicate selection
* Missing prerequisite
* Completed course
* Schedule conflict
* Minimum-credit failure
* Maximum-credit failure
* Full section
* Successful final submission

## 34.4 Waiting-List Tests

Test:

* Successful waiting-list entry
* Duplicate entry
* Queue ordering
* Leaving the queue
* Promotion after a seat becomes available

## 34.5 Advisor Tests

Test:

* Advisor can view assigned students
* Advisor cannot view unauthorized students
* Successful approval
* Rejection without reason
* Successful rejection with reason

## 34.6 Concurrency Tests

Test:

* Two users attempt to claim the final seat.
* Approved count never exceeds capacity.
* Waiting-list promotion remains correctly ordered.

---

# 35. Requirement Traceability

The functional requirement identifiers below come from `13-functional-requirements.md`.

| API Area                            | Related Functional Requirements |
| ----------------------------------- | ------------------------------- |
| Authentication                      | FR-001 to FR-005                |
| Student dashboard                   | FR-006 to FR-008                |
| Course browsing                     | FR-009 to FR-013                |
| Seat availability                   | FR-014 to FR-018                |
| Course selection                    | FR-019 to FR-024                |
| Prerequisites                       | FR-025 to FR-028                |
| Credit validation                   | FR-029 to FR-034                |
| Schedule conflicts                  | FR-035 to FR-040                |
| Waiting lists                       | FR-041 to FR-050                |
| Final submission                    | FR-051 to FR-057                |
| Registration status                 | FR-058 to FR-061                |
| Advisor functions                   | FR-062 to FR-070                |
| Course administration               | FR-071 to FR-084                |
| Student schedule                    | FR-085 to FR-088                |
| Notifications                       | FR-089 to FR-091                |
| User administration                 | FR-092 to FR-096                |
| Error handling and data consistency | FR-097 to FR-100                |

---

# 36. Future API Enhancements

Possible future endpoints may support:

* Refresh tokens
* Password reset
* Email notifications
* SMS notifications
* Degree-progress analysis
* Course recommendations
* Tuition-payment integration
* Registration analytics
* Bulk course import
* University ERP synchronization
* Mobile application support

---

# 37. Conclusion

The CoursePilot REST API provides a structured interface between the React frontend, FastAPI backend, and PostgreSQL database.

The API design supports:

* Secure authentication
* Role-based authorization
* Course and section browsing
* Accurate seat information
* Registration validation
* Schedule-conflict detection
* Credit-limit enforcement
* Waiting-list management
* Advisor approval
* Student schedules
* Administrative management
* Notifications
* Auditing
* Consistent error handling

This API design completes the proposed technical documentation for the CoursePilot system.
