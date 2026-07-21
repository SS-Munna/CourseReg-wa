# CoursePilot Database Design

## 1. Introduction

This document defines the proposed database design for CoursePilot.

CoursePilot uses AWS DynamoDB as the primary database for the current implementation direction. The FastAPI backend accesses DynamoDB through boto3-based data-access functions.

The database design supports:

* Course browsing
* Course search and filtering
* Course and section information
* Seat availability
* Student registration records
* Prerequisite validation
* Schedule-conflict validation
* Waiting-list management
* Advisor decisions
* Notifications
* Audit logging

For the current assessment implementation, the main focus is the course-catalog feature using a DynamoDB course table.

---

## 2. Database Technology

| Item | Selected Technology |
| --- | --- |
| Database Management System | AWS DynamoDB |
| Database Type | Managed NoSQL key-value and document database |
| Backend SDK | boto3 |
| Data Format | JSON-like DynamoDB items |
| Configuration | Environment variables |
| Primary Access Layer | Repository functions in the FastAPI backend |
| Authentication to AWS | Local AWS credentials or IAM role |
| Date and Time Storage | ISO 8601 strings |

DynamoDB is selected because it provides:

* Managed cloud database service
* Simple integration with AWS
* Flexible item-based data model
* Fast key-based reads and writes
* Conditional writes for safe updates
* Optional secondary indexes for future scaling
* No need to manage a database server locally

---

## 3. Database Configuration

The backend should read DynamoDB configuration from environment variables.

Example `.env.example` values:

```text
AWS_REGION=us-east-1
DYNAMODB_COURSES_TABLE=CoursePilotCourses
```

Real AWS access keys, secret keys, and session tokens must not be committed to GitHub.

The backend should use one of the following secure methods for AWS authentication:

1. AWS CLI configured credentials for local development
2. Environment variables stored locally only
3. IAM role when deployed in AWS
4. Temporary credentials when needed for testing

---

## 4. DynamoDB Design Approach

CoursePilot may use multiple DynamoDB tables.

The current implementation uses a separate course table for the course-catalog feature.

Future versions may add additional tables for users, sections, registrations, waiting lists, notifications, and audit logs.

This design uses the following principles:

* Table names are configurable through environment variables.
* The backend does not expose DynamoDB directly to the frontend.
* API routes call services or repositories.
* Repository functions contain boto3 operations.
* Business logic is not placed inside database helper files.
* Conditional writes are used when seat capacity or status changes require consistency.
* Scan-based filtering is acceptable for a small academic development dataset.
* Secondary indexes may be introduced later for larger datasets.

---

## 5. Current Course Catalog Table

### 5.1 Table Name

```text
CoursePilotCourses
```

The actual table name should be loaded from:

```text
DYNAMODB_COURSES_TABLE
```

### 5.2 Primary Key

| Key Type | Attribute | Description |
| --- | --- | --- |
| Partition Key | `course_id` | Unique identifier for each course record |

Example course ID values:

```text
cse-101
cse-201
eee-205
math-101
```

### 5.3 Course Item Structure

Each course item should contain:

| Attribute | Type | Required | Description |
| --- | --- | --- | --- |
| `course_id` | String | Yes | Unique course identifier |
| `code` | String | Yes | Course code, such as `CSE 101` |
| `title` | String | Yes | Course title |
| `department` | String | Yes | Department offering the course |
| `semester` | String | Yes | Offered semester |
| `instructor` | String | Yes | Instructor name |
| `credits` | Number | Yes | Credit value |
| `capacity` | Number | Yes | Maximum seat capacity |
| `available_seats` | Number | Yes | Currently available seats |
| `is_mandatory` | Boolean | Yes | Whether the course is mandatory |
| `level` | String | No | Undergraduate or graduate level |
| `description` | String | No | Short course description |
| `prerequisites` | List | No | List of prerequisite course codes |
| `section` | String | No | Section number or label |
| `schedule` | List | No | Meeting schedule information |
| `room` | String | No | Classroom or lab room |
| `created_at` | String | No | ISO timestamp for creation |
| `updated_at` | String | No | ISO timestamp for last update |

### 5.4 Example Item

```json
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
  "schedule": [
    {
      "day": "Sunday",
      "start_time": "10:00",
      "end_time": "11:30"
    },
    {
      "day": "Tuesday",
      "start_time": "10:00",
      "end_time": "11:30"
    }
  ],
  "room": "CSE-201",
  "created_at": "2026-07-23T10:00:00Z",
  "updated_at": "2026-07-23T10:00:00Z"
}
```

---

## 6. Course Catalog Access Patterns

The course-catalog feature requires the following access patterns.

| Access Pattern | Backend Operation | DynamoDB Operation |
| --- | --- | --- |
| List all courses | `GET /api/courses` | Scan course table |
| Search by course code | `GET /api/courses?search=CSE` | Scan and filter |
| Search by course title | `GET /api/courses?search=data` | Scan and filter |
| Filter by department | `GET /api/courses?department=CSE` | Scan and filter |
| Filter by semester | `GET /api/courses?semester=Fall 2026` | Scan and filter |
| Filter mandatory courses | `GET /api/courses?mandatory=true` | Scan and filter |
| Filter available seats | `GET /api/courses?available_only=true` | Scan and filter |
| Retrieve course detail | `GET /api/courses/{course_id}` | Get item by partition key |

For the current small dataset, table scan with backend filtering is acceptable. For production-scale data, the table should be redesigned with secondary indexes for common query fields such as department, semester, and course code.

---

## 7. Suggested Future Indexes

If the dataset becomes large, the following Global Secondary Indexes may be added.

| Index Name | Partition Key | Sort Key | Purpose |
| --- | --- | --- | --- |
| `DepartmentSemesterIndex` | `department` | `semester` | List courses by department and semester |
| `CourseCodeIndex` | `code` | `semester` | Retrieve courses by course code |
| `MandatoryIndex` | `is_mandatory` | `department` | Filter mandatory courses |
| `SemesterIndex` | `semester` | `code` | List courses for a semester |

The initial implementation does not require these indexes because the current assessment dataset is small.

---

## 8. Future User Table

A future user table may store student, advisor, administrator, and system administrator accounts.

### 8.1 Table Name

```text
CoursePilotUsers
```

### 8.2 Primary Key

| Key Type | Attribute | Description |
| --- | --- | --- |
| Partition Key | `user_id` | Unique user identifier |

### 8.3 Important Attributes

| Attribute | Type | Description |
| --- | --- | --- |
| `user_id` | String | Unique user identifier |
| `email` | String | User email address |
| `password_hash` | String | Secure password hash |
| `role` | String | Student, advisor, department admin, or system admin |
| `status` | String | Active, inactive, or locked |
| `full_name` | String | User full name |
| `student_number` | String | Student ID when applicable |
| `department` | String | Department name |
| `program` | String | Academic program |
| `advisor_id` | String | Assigned advisor ID for students |
| `created_at` | String | Creation timestamp |
| `updated_at` | String | Last update timestamp |

### 8.4 User Data Rules

* Email should be unique.
* Student number should be unique for student users.
* Passwords must never be stored as plain text.
* Password hashes must never be returned in API responses.
* Inactive or locked users should not be allowed to log in.

---

## 9. Future Section Table

Course sections may be stored separately in a future version.

### 9.1 Table Name

```text
CoursePilotSections
```

### 9.2 Primary Key

| Key Type | Attribute | Description |
| --- | --- | --- |
| Partition Key | `section_id` | Unique section identifier |

### 9.3 Important Attributes

| Attribute | Type | Description |
| --- | --- | --- |
| `section_id` | String | Unique section identifier |
| `course_id` | String | Related course identifier |
| `course_code` | String | Course code for easier display |
| `section_number` | String | Section number |
| `semester` | String | Academic semester |
| `instructor` | String | Instructor name |
| `room` | String | Room number |
| `capacity` | Number | Maximum seat count |
| `available_seats` | Number | Available seat count |
| `schedule` | List | List of meeting times |
| `status` | String | Open, closed, or cancelled |

### 9.4 Section Data Rules

* Capacity must be positive.
* Available seats cannot be negative.
* Available seats cannot exceed capacity.
* End time must be later than start time.
* A course section should be unique for a course, semester, and section number.

---

## 10. Future Registration Table

### 10.1 Table Name

```text
CoursePilotRegistrations
```

### 10.2 Primary Key

| Key Type | Attribute | Description |
| --- | --- | --- |
| Partition Key | `registration_id` | Unique registration identifier |

### 10.3 Important Attributes

| Attribute | Type | Description |
| --- | --- | --- |
| `registration_id` | String | Unique registration ID |
| `student_id` | String | Student user ID |
| `section_id` | String | Selected section ID |
| `course_id` | String | Related course ID |
| `semester` | String | Academic semester |
| `status` | String | Draft, pending, approved, rejected, or dropped |
| `selected_at` | String | Selection timestamp |
| `submitted_at` | String | Final submission timestamp |
| `reviewed_at` | String | Advisor review timestamp |
| `advisor_id` | String | Reviewing advisor ID |
| `advisor_comment` | String | Optional advisor comment |

### 10.4 Registration Status Values

```text
DRAFT
PENDING
APPROVED
REJECTED
DROPPED
```

### 10.5 Registration Data Rules

* A student should not register for the same section more than once.
* A student should not register for the same course twice in the same semester.
* Unsupported status transitions should be rejected by backend logic.
* Seat availability should be rechecked before final submission and approval.

---

## 11. Future Waitlist Table

### 11.1 Table Name

```text
CoursePilotWaitlists
```

### 11.2 Primary Key

| Key Type | Attribute | Description |
| --- | --- | --- |
| Partition Key | `waitlist_id` | Unique waitlist record ID |

### 11.3 Important Attributes

| Attribute | Type | Description |
| --- | --- | --- |
| `waitlist_id` | String | Unique waitlist ID |
| `student_id` | String | Student user ID |
| `section_id` | String | Section ID |
| `course_id` | String | Course ID |
| `status` | String | Active, promoted, removed, or expired |
| `joined_at` | String | Queue joining timestamp |
| `promoted_at` | String | Promotion timestamp |
| `removed_at` | String | Removal timestamp |

### 11.4 Waitlist Status Values

```text
ACTIVE
PROMOTED
REMOVED
EXPIRED
```

### 11.5 Waitlist Data Rules

* A student should not join the same section waitlist more than once.
* Active waitlist order is based on `joined_at`.
* Queue position should be calculated dynamically.
* Students should be revalidated before promotion.

---

## 12. Future Academic Record Table

### 12.1 Table Name

```text
CoursePilotAcademicRecords
```

### 12.2 Primary Key

| Key Type | Attribute | Description |
| --- | --- | --- |
| Partition Key | `record_id` | Unique academic record ID |

### 12.3 Important Attributes

| Attribute | Type | Description |
| --- | --- |
| `record_id` | String | Unique academic record ID |
| `student_id` | String | Student user ID |
| `course_id` | String | Completed course ID |
| `course_code` | String | Completed course code |
| `grade` | String | Final grade |
| `semester_completed` | String | Semester completed |
| `passed` | Boolean | Whether the prerequisite is satisfied |

### 12.4 Academic Record Rules

* Completed-course data should be trusted for prerequisite validation.
* A course with a failed grade should not satisfy a prerequisite.
* Minimum-grade rules may be added for advanced prerequisite checks.

---

## 13. Future Notification Table

### 13.1 Table Name

```text
CoursePilotNotifications
```

### 13.2 Primary Key

| Key Type | Attribute | Description |
| --- | --- | --- |
| Partition Key | `notification_id` | Unique notification ID |

### 13.3 Important Attributes

| Attribute | Type | Description |
| --- | --- | --- |
| `notification_id` | String | Unique notification ID |
| `user_id` | String | Recipient user ID |
| `type` | String | Notification type |
| `title` | String | Notification title |
| `message` | String | Notification message |
| `read` | Boolean | Read status |
| `related_entity_id` | String | Optional related record |
| `created_at` | String | Creation timestamp |

---

## 14. Future Audit Log Table

### 14.1 Table Name

```text
CoursePilotAuditLogs
```

### 14.2 Primary Key

| Key Type | Attribute | Description |
| --- | --- | --- |
| Partition Key | `audit_id` | Unique audit log ID |

### 14.3 Important Attributes

| Attribute | Type | Description |
| --- | --- | --- |
| `audit_id` | String | Unique audit record ID |
| `actor_user_id` | String | User who performed the action |
| `action_type` | String | Type of action |
| `entity_type` | String | Affected entity type |
| `entity_id` | String | Affected entity ID |
| `details` | Map | Additional action details |
| `created_at` | String | Timestamp of action |

Audit logs should not be editable by normal users.

---

## 15. Data Relationship Mapping in DynamoDB

DynamoDB does not enforce foreign-key constraints. Relationships are maintained by application logic in the backend.

| Relationship | DynamoDB Representation |
| --- | --- |
| Course to section | `course_id` stored in section item |
| Student to registration | `student_id` stored in registration item |
| Section to registration | `section_id` stored in registration item |
| Student to waitlist | `student_id` stored in waitlist item |
| Section to waitlist | `section_id` stored in waitlist item |
| Course to prerequisite | Prerequisite course codes or IDs stored as a list |
| User to notification | `user_id` stored in notification item |
| User to audit action | `actor_user_id` stored in audit item |

The backend must check related item existence before creating records that depend on them.

---

## 16. Data Validation Rules

The backend should enforce the following validation rules.

### 16.1 Course Validation

* Course code is required.
* Course title is required.
* Department is required.
* Credits must be greater than zero.
* Capacity must be greater than zero.
* Available seats must be greater than or equal to zero.
* Available seats cannot exceed capacity.
* A course cannot list itself as a prerequisite.

### 16.2 User Validation

* Email is required.
* Email format must be valid.
* Role must be one of the allowed roles.
* Student number is required for student users.
* Advisor assignment is required when advisor approval is enabled.

### 16.3 Registration Validation

* Student must exist.
* Section must exist.
* Registration period must be active.
* Duplicate registration must be rejected.
* Prerequisites must be satisfied.
* Schedule conflicts must be rejected.
* Credit limits must be enforced.
* Seat availability must be rechecked before final submission.

### 16.4 Waitlist Validation

* Student must exist.
* Section must exist.
* Section must be full.
* Duplicate active waitlist entry must be rejected.
* Student eligibility must be checked before promotion.

---

## 17. Seat Availability and Conditional Updates

CoursePilot must prevent over-enrollment.

The displayed seat count may become outdated while students are using the frontend. Therefore, the backend must recheck seat availability before any operation that reserves or approves a seat.

### 17.1 Conditional Seat Update

A safe seat update should use a condition similar to:

```text
available_seats > 0
```

The intended update is:

```text
SET available_seats = available_seats - 1
```

This means DynamoDB should only reduce the available seat count when at least one seat is still available.

### 17.2 Failed Conditional Update

If the conditional update fails, the backend should return a conflict response such as:

```json
{
  "success": false,
  "error": {
    "code": "SECTION_FULL",
    "message": "No seats are currently available for this section."
  }
}
```

### 17.3 Multi-Item Consistency

When multiple records must change together, such as updating a registration and decreasing the available seat count, DynamoDB transaction writes should be considered.

---

## 18. Search and Filtering Strategy

The current course-catalog implementation can use scan-based filtering because the development dataset is small.

Search and filtering may include:

* Case-insensitive search by course code
* Case-insensitive search by title
* Department filtering
* Semester filtering
* Mandatory-course filtering
* Available-seat filtering

Example backend filtering logic:

```text
Load course records from DynamoDB.
For each course:
    Check search text against course code and title.
    Check department filter.
    Check semester filter.
    Check mandatory filter.
    Check seat availability filter.
Return matching course records.
```

For larger datasets, filtering should move toward DynamoDB query patterns and indexes.

---

## 19. Seed Data Design

Development seed data should help test the course-catalog feature.

Seed records should include different:

* Departments
* Course levels
* Credit values
* Seat capacities
* Seat availability values
* Mandatory and elective courses
* Semesters
* Instructors

Example seed courses:

| Course Code | Title | Department | Credits | Capacity | Available Seats |
| --- | --- | --- | --- | --- | --- |
| CSE 101 | Introduction to Computer Science | CSE | 3 | 40 | 12 |
| CSE 201 | Data Structures | CSE | 3 | 35 | 8 |
| EEE 205 | Circuit Analysis | EEE | 3 | 30 | 5 |
| MAT 101 | Calculus I | Mathematics | 3 | 45 | 20 |
| PHY 101 | Physics I | Physics | 3 | 40 | 0 |

Seed scripts should not insert duplicate records if the same course already exists.

---

## 20. Backup and Recovery Considerations

DynamoDB is a managed AWS service. Future production deployment may use:

* Point-in-time recovery
* On-demand backups
* Export to S3
* CloudWatch monitoring
* IAM-based access control

For the academic project implementation, backup configuration may be documented as a future enhancement.

---

## 21. Security Considerations

Database security should include:

* No AWS secrets committed to GitHub
* No real `.env` file committed
* Limited AWS permissions for the backend
* Environment-based table names
* Validation of user input before database operations
* No password hashes returned in API responses
* No internal error details exposed to users

For the course-catalog feature, the backend should only need permission to read course records and optionally write seed data during development.

---

## 22. Error Handling

Database-related errors should be handled clearly.

| Error Scenario | Suggested Error Code | Suggested Status |
| --- | --- | --- |
| DynamoDB table name missing | `DYNAMODB_CONFIGURATION_ERROR` | 500 |
| AWS region missing | `DYNAMODB_CONFIGURATION_ERROR` | 500 |
| Course table not found | `COURSE_TABLE_NOT_FOUND` | 500 |
| Course not found | `RESOURCE_NOT_FOUND` | 404 |
| DynamoDB operation failed | `DYNAMODB_OPERATION_FAILED` | 500 |
| Seat conditional update failed | `SECTION_FULL` | 409 |
| Invalid filter value | `VALIDATION_ERROR` | 422 |

API responses should not expose AWS secret values or full stack traces.

---

## 23. Requirement Traceability

| Requirement Area | Database Support |
| --- | --- |
| Course browsing | Course table |
| Course search | Course attributes and future indexes |
| Course filtering | Department, semester, mandatory, and seat attributes |
| Seat availability | Capacity and available-seat attributes |
| Prerequisite checking | Prerequisite list or future prerequisite table |
| Credit validation | Course credit value |
| Schedule-conflict detection | Schedule attributes or future section table |
| Waiting list | Future waitlist table |
| Advisor approval | Future registration table |
| Notifications | Future notification table |
| Audit logging | Future audit log table |

---

## 24. Limitations of Current Database Implementation

The current assessment implementation focuses on the course-catalog workflow.

Current limitations include:

* Course data is the main implemented table.
* Authentication tables may be added later.
* Registration tables may be added later.
* Waitlist tables may be added later.
* Scan-based filtering is used for a small dataset.
* Advanced secondary indexes are future improvements.
* Complex multi-table transaction workflows are planned for later implementation.

These limitations are acceptable for the current feature because the required end-to-end workflow is course browsing/searching from React to FastAPI to DynamoDB.

---

## 25. Conclusion

The CoursePilot database design uses AWS DynamoDB as the primary data layer for the current implementation direction.

The design defines a course table for the implemented course-catalog feature and outlines future tables for users, sections, registrations, waitlists, notifications, and audit logs.

The DynamoDB approach supports the current end-to-end feature by allowing the FastAPI backend to retrieve course records and return them to the React frontend. Future versions can extend the design using additional tables, conditional writes, transaction writes, and secondary indexes.
