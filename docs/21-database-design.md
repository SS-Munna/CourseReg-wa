# CoursePilot Database Design

## 1. Introduction

This document defines the proposed PostgreSQL database design for CoursePilot.

The database supports:

* User authentication and role management
* Student, advisor, and instructor profiles
* Academic departments and programs
* Course and section management
* Prerequisite validation
* Completed-course records
* Registration processing
* Seat-capacity control
* Waiting-list management
* Advisor approval
* Class schedules and rooms
* Notifications
* Audit logging

The Entity Relationship Diagram is documented in `18-erd.md`.

---

# 2. Database Technology

| Item                       | Selected Technology                        |
| -------------------------- | ------------------------------------------ |
| Database Management System | PostgreSQL                                 |
| ORM                        | SQLAlchemy                                 |
| Migration Tool             | Alembic                                    |
| Backend Framework          | FastAPI                                    |
| Data Validation            | Pydantic                                   |
| Primary-Key Type           | UUID                                       |
| Date and Time Storage      | PostgreSQL date, time, and timestamp types |

PostgreSQL is selected because it provides:

* Relational integrity
* Foreign-key constraints
* Transactions
* Row-level locking
* Indexing
* Check constraints
* Reliable concurrent access
* Strong support for structured data

---

# 3. Database Design Principles

The CoursePilot database should follow these principles:

1. Each table must have a primary key.
2. Related tables must use foreign keys.
3. Duplicate business records must be prevented using unique constraints.
4. Invalid values must be prevented using check constraints.
5. Frequently searched columns should be indexed.
6. Registration and seat-allocation operations must use transactions.
7. Passwords must never be stored as plain text.
8. Important records should include timestamps.
9. Status values should be limited to predefined values.
10. Historical registration and audit data should not be deleted without authorization.

---

# 4. Naming Conventions

The proposed naming conventions are:

| Database Object       | Convention                          | Example                  |
| --------------------- | ----------------------------------- | ------------------------ |
| Table names           | Lowercase plural snake case         | `course_sections`        |
| Column names          | Lowercase snake case                | `student_id`             |
| Primary keys          | `id`                                | `id UUID`                |
| Foreign keys          | Referenced entity plus `_id`        | `course_id`              |
| Boolean columns       | Begin with `is_` or `has_`          | `is_mandatory`           |
| Date and time columns | End with `_at`, `_date`, or `_time` | `created_at`             |
| Unique constraints    | `uq_<table>_<columns>`              | `uq_users_email`         |
| Check constraints     | `ck_<table>_<rule>`                 | `ck_sections_capacity`   |
| Indexes               | `ix_<table>_<columns>`              | `ix_courses_course_code` |

---

# 5. PostgreSQL Extensions

UUID values may be generated using PostgreSQL.

```sql
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
```

The primary key default may use:

```sql
gen_random_uuid()
```

---

# 6. Controlled Status Values

PostgreSQL enum types may be used for controlled status values.

## 6.1 User Role

```sql
CREATE TYPE user_role AS ENUM (
    'STUDENT',
    'ADVISOR',
    'INSTRUCTOR',
    'DEPARTMENT_ADMIN',
    'SYSTEM_ADMIN'
);
```

## 6.2 Account Status

```sql
CREATE TYPE account_status AS ENUM (
    'ACTIVE',
    'INACTIVE',
    'SUSPENDED'
);
```

## 6.3 Registration Status

```sql
CREATE TYPE registration_status AS ENUM (
    'DRAFT',
    'PENDING',
    'APPROVED',
    'REJECTED',
    'DROPPED'
);
```

## 6.4 Waiting-List Status

```sql
CREATE TYPE waitlist_status AS ENUM (
    'ACTIVE',
    'PROMOTED',
    'REMOVED',
    'EXPIRED'
);
```

## 6.5 Semester Status

```sql
CREATE TYPE semester_status AS ENUM (
    'UPCOMING',
    'ACTIVE',
    'COMPLETED',
    'ARCHIVED'
);
```

## 6.6 Registration-Period Status

```sql
CREATE TYPE registration_period_status AS ENUM (
    'SCHEDULED',
    'OPEN',
    'CLOSED'
);
```

---

# 7. Table Summary

| Table                  | Purpose                                              |
| ---------------------- | ---------------------------------------------------- |
| `users`                | Stores common account and authentication information |
| `departments`          | Stores academic departments                          |
| `programs`             | Stores academic programs                             |
| `students`             | Stores student-specific academic information         |
| `advisors`             | Stores advisor information                           |
| `instructors`          | Stores instructor information                        |
| `semesters`            | Stores semester or trimester information             |
| `registration_periods` | Stores registration and drop dates                   |
| `courses`              | Stores course catalogue information                  |
| `course_prerequisites` | Stores prerequisite relationships                    |
| `course_sections`      | Stores individual course offerings                   |
| `rooms`                | Stores classroom information                         |
| `section_schedules`    | Stores section meeting times                         |
| `completed_courses`    | Stores student academic history                      |
| `registrations`        | Stores student course registrations                  |
| `waitlist_entries`     | Stores waiting-list records                          |
| `notifications`        | Stores in-system user notifications                  |
| `audit_logs`           | Stores important system activity                     |

---

# 8. Detailed Table Design

## 8.1 Users Table

### Purpose

The `users` table stores shared account information for every system user.

### Structure

| Column           | Data Type        | Constraints              | Description                  |
| ---------------- | ---------------- | ------------------------ | ---------------------------- |
| `id`             | UUID             | Primary key              | Unique user identifier       |
| `email`          | VARCHAR(255)     | Unique, not null         | User login email             |
| `password_hash`  | VARCHAR(255)     | Not null                 | Secure password hash         |
| `full_name`      | VARCHAR(150)     | Not null                 | User's full name             |
| `role`           | `user_role`      | Not null                 | Assigned system role         |
| `account_status` | `account_status` | Not null, default ACTIVE | Current account state        |
| `last_login_at`  | TIMESTAMPTZ      | Nullable                 | Most recent successful login |
| `created_at`     | TIMESTAMPTZ      | Not null                 | Account creation time        |
| `updated_at`     | TIMESTAMPTZ      | Not null                 | Last account update          |

### Constraints

* Email must be unique.
* Password hash must not be empty.
* Role must use a supported enum value.

### Indexes

* Unique index on `email`
* Index on `role`
* Index on `account_status`

### Related Requirements

* FR-001 to FR-005
* FR-092 to FR-096

---

## 8.2 Departments Table

### Purpose

The `departments` table stores academic department information.

| Column            | Data Type    | Constraints      | Description           |
| ----------------- | ------------ | ---------------- | --------------------- |
| `id`              | UUID         | Primary key      | Department identifier |
| `department_code` | VARCHAR(20)  | Unique, not null | Short department code |
| `department_name` | VARCHAR(150) | Unique, not null | Department name       |
| `created_at`      | TIMESTAMPTZ  | Not null         | Creation time         |
| `updated_at`      | TIMESTAMPTZ  | Not null         | Last update time      |

### Example

```text
Code: CSE
Name: Computer Science and Engineering
```

---

## 8.3 Programs Table

### Purpose

The `programs` table stores academic programs offered by departments.

| Column           | Data Type    | Constraints           | Description                      |
| ---------------- | ------------ | --------------------- | -------------------------------- |
| `id`             | UUID         | Primary key           | Program identifier               |
| `department_id`  | UUID         | Foreign key, not null | Owning department                |
| `program_code`   | VARCHAR(30)  | Unique, not null      | Program code                     |
| `program_name`   | VARCHAR(150) | Not null              | Program name                     |
| `minimum_credit` | NUMERIC(4,1) | Not null              | Default minimum semester credits |
| `maximum_credit` | NUMERIC(4,1) | Not null              | Default maximum semester credits |
| `created_at`     | TIMESTAMPTZ  | Not null              | Creation time                    |
| `updated_at`     | TIMESTAMPTZ  | Not null              | Last update time                 |

### Check Constraints

```text
minimum_credit >= 0
maximum_credit >= minimum_credit
```

---

## 8.4 Advisors Table

### Purpose

The `advisors` table stores academic advisor profiles.

| Column            | Data Type   | Constraints                  | Description                   |
| ----------------- | ----------- | ---------------------------- | ----------------------------- |
| `id`              | UUID        | Primary key                  | Advisor identifier            |
| `user_id`         | UUID        | Unique foreign key, not null | Associated user account       |
| `department_id`   | UUID        | Foreign key, not null        | Advisor department            |
| `employee_number` | VARCHAR(50) | Unique, not null             | Institutional employee number |
| `created_at`      | TIMESTAMPTZ | Not null                     | Creation time                 |
| `updated_at`      | TIMESTAMPTZ | Not null                     | Last update time              |

### Relationship

One advisor may be assigned to many students.

---

## 8.5 Instructors Table

### Purpose

The `instructors` table stores faculty members assigned to sections.

| Column            | Data Type   | Constraints                  | Description                   |
| ----------------- | ----------- | ---------------------------- | ----------------------------- |
| `id`              | UUID        | Primary key                  | Instructor identifier         |
| `user_id`         | UUID        | Unique foreign key, not null | Associated user account       |
| `department_id`   | UUID        | Foreign key, not null        | Instructor department         |
| `employee_number` | VARCHAR(50) | Unique, not null             | Institutional employee number |
| `created_at`      | TIMESTAMPTZ | Not null                     | Creation time                 |
| `updated_at`      | TIMESTAMPTZ | Not null                     | Last update time              |

---

## 8.6 Students Table

### Purpose

The `students` table stores student-specific academic information.

| Column              | Data Type   | Constraints                  | Description               |
| ------------------- | ----------- | ---------------------------- | ------------------------- |
| `id`                | UUID        | Primary key                  | Student identifier        |
| `user_id`           | UUID        | Unique foreign key, not null | Associated user account   |
| `program_id`        | UUID        | Foreign key, not null        | Academic program          |
| `advisor_id`        | UUID        | Foreign key, nullable        | Assigned academic advisor |
| `student_number`    | VARCHAR(50) | Unique, not null             | University student number |
| `current_trimester` | INTEGER     | Not null                     | Current trimester number  |
| `academic_status`   | VARCHAR(30) | Not null                     | Current academic state    |
| `created_at`        | TIMESTAMPTZ | Not null                     | Creation time             |
| `updated_at`        | TIMESTAMPTZ | Not null                     | Last update time          |

### Check Constraint

```text
current_trimester > 0
```

### Indexes

* Unique index on `student_number`
* Index on `program_id`
* Index on `advisor_id`

---

## 8.7 Semesters Table

### Purpose

The `semesters` table represents academic semesters or trimesters.

| Column          | Data Type         | Constraints | Description                |
| --------------- | ----------------- | ----------- | -------------------------- |
| `id`            | UUID              | Primary key | Semester identifier        |
| `semester_name` | VARCHAR(50)       | Not null    | Semester or trimester name |
| `academic_year` | INTEGER           | Not null    | Academic year              |
| `start_date`    | DATE              | Not null    | Semester start date        |
| `end_date`      | DATE              | Not null    | Semester end date          |
| `status`        | `semester_status` | Not null    | Semester state             |
| `created_at`    | TIMESTAMPTZ       | Not null    | Creation time              |
| `updated_at`    | TIMESTAMPTZ       | Not null    | Last update time           |

### Unique Constraint

```text
semester_name + academic_year
```

### Check Constraint

```text
end_date > start_date
```

---

## 8.8 Registration Periods Table

### Purpose

The `registration_periods` table controls when registration and course dropping are allowed.

| Column           | Data Type                    | Constraints           | Description                       |
| ---------------- | ---------------------------- | --------------------- | --------------------------------- |
| `id`             | UUID                         | Primary key           | Registration-period identifier    |
| `semester_id`    | UUID                         | Foreign key, not null | Related semester                  |
| `opening_time`   | TIMESTAMPTZ                  | Not null              | Registration opening time         |
| `closing_time`   | TIMESTAMPTZ                  | Not null              | Registration closing time         |
| `drop_deadline`  | TIMESTAMPTZ                  | Not null              | Last time a course may be dropped |
| `minimum_credit` | NUMERIC(4,1)                 | Not null              | Minimum allowed credits           |
| `maximum_credit` | NUMERIC(4,1)                 | Not null              | Maximum allowed credits           |
| `status`         | `registration_period_status` | Not null              | Current registration state        |
| `created_at`     | TIMESTAMPTZ                  | Not null              | Creation time                     |
| `updated_at`     | TIMESTAMPTZ                  | Not null              | Last update time                  |

### Check Constraints

```text
closing_time > opening_time
drop_deadline >= closing_time
minimum_credit >= 0
maximum_credit >= minimum_credit
```

### Related Requirements

* FR-007
* FR-031 to FR-034
* FR-052
* FR-057
* FR-081

---

## 8.9 Courses Table

### Purpose

The `courses` table stores general course catalogue information.

| Column               | Data Type    | Constraints             | Description                           |
| -------------------- | ------------ | ----------------------- | ------------------------------------- |
| `id`                 | UUID         | Primary key             | Course identifier                     |
| `department_id`      | UUID         | Foreign key, not null   | Owning department                     |
| `course_code`        | VARCHAR(30)  | Unique, not null        | Course code                           |
| `course_title`       | VARCHAR(200) | Not null                | Course title                          |
| `course_description` | TEXT         | Nullable                | Detailed description                  |
| `credit_value`       | NUMERIC(3,1) | Not null                | Course credit value                   |
| `course_level`       | INTEGER      | Nullable                | Academic level                        |
| `course_type`        | VARCHAR(30)  | Not null                | Theory, laboratory, project, or other |
| `is_mandatory`       | BOOLEAN      | Not null, default false | Mandatory-course indicator            |
| `is_active`          | BOOLEAN      | Not null, default true  | Course availability                   |
| `created_at`         | TIMESTAMPTZ  | Not null                | Creation time                         |
| `updated_at`         | TIMESTAMPTZ  | Not null                | Last update time                      |

### Check Constraints

```text
credit_value > 0
course_level IS NULL OR course_level > 0
```

### Indexes

* Unique index on `course_code`
* Index on `department_id`
* Index on `course_title`
* Index on `is_mandatory`
* Index on `is_active`

### Related Requirements

* FR-009 to FR-013
* FR-071 to FR-072
* FR-080

---

## 8.10 Course Prerequisites Table

### Purpose

The `course_prerequisites` table represents relationships between target courses and required prerequisite courses.

| Column                   | Data Type   | Constraints           | Description              |
| ------------------------ | ----------- | --------------------- | ------------------------ |
| `id`                     | UUID        | Primary key           | Relationship identifier  |
| `course_id`              | UUID        | Foreign key, not null | Target course            |
| `prerequisite_course_id` | UUID        | Foreign key, not null | Required course          |
| `minimum_grade`          | VARCHAR(5)  | Nullable              | Minimum acceptable grade |
| `created_at`             | TIMESTAMPTZ | Not null              | Creation time            |

### Unique Constraint

```text
course_id + prerequisite_course_id
```

### Check Constraint

```text
course_id <> prerequisite_course_id
```

### Related Requirements

* FR-025 to FR-028
* FR-079

---

## 8.11 Course Sections Table

### Purpose

The `course_sections` table stores specific course offerings for a semester.

| Column           | Data Type   | Constraints           | Description                |
| ---------------- | ----------- | --------------------- | -------------------------- |
| `id`             | UUID        | Primary key           | Section identifier         |
| `course_id`      | UUID        | Foreign key, not null | Related course             |
| `semester_id`    | UUID        | Foreign key, not null | Related semester           |
| `instructor_id`  | UUID        | Foreign key, nullable | Assigned instructor        |
| `section_number` | VARCHAR(20) | Not null              | Section label              |
| `seat_capacity`  | INTEGER     | Not null              | Maximum number of seats    |
| `section_status` | VARCHAR(20) | Not null              | Open, closed, or cancelled |
| `created_at`     | TIMESTAMPTZ | Not null              | Creation time              |
| `updated_at`     | TIMESTAMPTZ | Not null              | Last update time           |

### Unique Constraint

```text
course_id + semester_id + section_number
```

### Check Constraint

```text
seat_capacity > 0
```

### Indexes

* Index on `course_id`
* Index on `semester_id`
* Index on `instructor_id`
* Index on `section_status`

### Related Requirements

* FR-014 to FR-018
* FR-073 to FR-078
* FR-082 to FR-084

---

## 8.12 Rooms Table

### Purpose

The `rooms` table stores classroom information.

| Column          | Data Type    | Constraints | Description            |
| --------------- | ------------ | ----------- | ---------------------- |
| `id`            | UUID         | Primary key | Room identifier        |
| `building_name` | VARCHAR(100) | Not null    | Building name          |
| `room_number`   | VARCHAR(30)  | Not null    | Room number            |
| `room_capacity` | INTEGER      | Not null    | Physical room capacity |
| `room_status`   | VARCHAR(20)  | Not null    | Active or unavailable  |
| `created_at`    | TIMESTAMPTZ  | Not null    | Creation time          |
| `updated_at`    | TIMESTAMPTZ  | Not null    | Last update time       |

### Unique Constraint

```text
building_name + room_number
```

### Check Constraint

```text
room_capacity > 0
```

---

## 8.13 Section Schedules Table

### Purpose

The `section_schedules` table stores weekly meeting times for course sections.

| Column        | Data Type   | Constraints           | Description            |
| ------------- | ----------- | --------------------- | ---------------------- |
| `id`          | UUID        | Primary key           | Schedule identifier    |
| `section_id`  | UUID        | Foreign key, not null | Related course section |
| `room_id`     | UUID        | Foreign key, not null | Assigned room          |
| `day_of_week` | VARCHAR(10) | Not null              | Scheduled class day    |
| `start_time`  | TIME        | Not null              | Class start time       |
| `end_time`    | TIME        | Not null              | Class end time         |
| `created_at`  | TIMESTAMPTZ | Not null              | Creation time          |
| `updated_at`  | TIMESTAMPTZ | Not null              | Last update time       |

### Check Constraint

```text
end_time > start_time
```

### Unique Constraint

A section should not contain an identical schedule record.

```text
section_id + day_of_week + start_time + end_time
```

### Indexes

* Index on `section_id`
* Index on `room_id`
* Composite index on `day_of_week`, `start_time`, and `end_time`

### Related Requirements

* FR-024
* FR-035 to FR-040
* FR-078
* FR-086 to FR-088

---

## 8.14 Completed Courses Table

### Purpose

The `completed_courses` table stores student academic history used for prerequisite checking.

| Column              | Data Type   | Constraints           | Description                   |
| ------------------- | ----------- | --------------------- | ----------------------------- |
| `id`                | UUID        | Primary key           | Record identifier             |
| `student_id`        | UUID        | Foreign key, not null | Related student               |
| `course_id`         | UUID        | Foreign key, not null | Completed course              |
| `grade`             | VARCHAR(5)  | Nullable              | Final grade                   |
| `completion_status` | VARCHAR(20) | Not null              | Passed, failed, or incomplete |
| `completed_at`      | DATE        | Nullable              | Completion date               |
| `created_at`        | TIMESTAMPTZ | Not null              | Record creation time          |
| `updated_at`        | TIMESTAMPTZ | Not null              | Last update time              |

### Unique Constraint

```text
student_id + course_id
```

A future version may allow repeated attempts using an additional attempt number.

### Indexes

* Index on `student_id`
* Index on `course_id`
* Composite index on `student_id` and `completion_status`

### Related Requirements

* FR-023
* FR-026 to FR-028

---

## 8.15 Registrations Table

### Purpose

The `registrations` table stores student course-selection and registration records.

| Column                | Data Type             | Constraints           | Description                      |
| --------------------- | --------------------- | --------------------- | -------------------------------- |
| `id`                  | UUID                  | Primary key           | Registration identifier          |
| `student_id`          | UUID                  | Foreign key, not null | Student making the registration  |
| `section_id`          | UUID                  | Foreign key, not null | Selected course section          |
| `reviewed_by`         | UUID                  | Foreign key, nullable | Advisor who reviewed the request |
| `registration_status` | `registration_status` | Not null              | Current registration state       |
| `advisor_comment`     | TEXT                  | Nullable              | Advisor decision comment         |
| `submitted_at`        | TIMESTAMPTZ           | Nullable              | Final-submission time            |
| `reviewed_at`         | TIMESTAMPTZ           | Nullable              | Approval or rejection time       |
| `dropped_at`          | TIMESTAMPTZ           | Nullable              | Course-drop time                 |
| `created_at`          | TIMESTAMPTZ           | Not null              | Initial selection time           |
| `updated_at`          | TIMESTAMPTZ           | Not null              | Last status update               |

### Unique Constraint

```text
student_id + section_id
```

### Important Rules

* A student cannot create duplicate registrations for the same section.
* A rejection should include an advisor comment.
* Only approved registrations consume confirmed seats.
* Draft, rejected, and dropped registrations should not consume confirmed seats.
* Status changes must follow allowed transitions.

### Indexes

* Index on `student_id`
* Index on `section_id`
* Index on `registration_status`
* Composite index on `section_id` and `registration_status`
* Composite index on `student_id` and `registration_status`

### Related Requirements

* FR-019 to FR-024
* FR-029 to FR-040
* FR-051 to FR-070
* FR-085 to FR-091

---

## 8.16 Waitlist Entries Table

### Purpose

The `waitlist_entries` table stores student requests for full sections.

| Column            | Data Type         | Constraints           | Description               |
| ----------------- | ----------------- | --------------------- | ------------------------- |
| `id`              | UUID              | Primary key           | Waitlist-entry identifier |
| `student_id`      | UUID              | Foreign key, not null | Waiting student           |
| `section_id`      | UUID              | Foreign key, not null | Full course section       |
| `waitlist_status` | `waitlist_status` | Not null              | Current queue state       |
| `joined_at`       | TIMESTAMPTZ       | Not null              | Queue-joining time        |
| `promoted_at`     | TIMESTAMPTZ       | Nullable              | Promotion time            |
| `removed_at`      | TIMESTAMPTZ       | Nullable              | Removal time              |
| `created_at`      | TIMESTAMPTZ       | Not null              | Record creation time      |
| `updated_at`      | TIMESTAMPTZ       | Not null              | Last update time          |

### Unique Constraint

```text
student_id + section_id
```

### Queue Ordering

Active waiting-list records should be ordered by:

```text
joined_at ASC, id ASC
```

### Queue Position

Queue position should be calculated dynamically.

```text
Position = Number of active entries ahead + 1
```

### Indexes

* Index on `student_id`
* Index on `section_id`
* Index on `waitlist_status`
* Composite index on `section_id`, `waitlist_status`, and `joined_at`

### Related Requirements

* FR-041 to FR-050
* FR-084
* FR-090

---

## 8.17 Notifications Table

### Purpose

The `notifications` table stores in-system messages for users.

| Column                | Data Type    | Constraints             | Description                 |
| --------------------- | ------------ | ----------------------- | --------------------------- |
| `id`                  | UUID         | Primary key             | Notification identifier     |
| `user_id`             | UUID         | Foreign key, not null   | Recipient                   |
| `notification_type`   | VARCHAR(50)  | Not null                | Notification category       |
| `title`               | VARCHAR(200) | Not null                | Short title                 |
| `message`             | TEXT         | Not null                | Notification message        |
| `related_entity_type` | VARCHAR(50)  | Nullable                | Related resource type       |
| `related_entity_id`   | UUID         | Nullable                | Related resource identifier |
| `is_read`             | BOOLEAN      | Not null, default false | Read state                  |
| `created_at`          | TIMESTAMPTZ  | Not null                | Creation time               |
| `read_at`             | TIMESTAMPTZ  | Nullable                | Time marked as read         |

### Indexes

* Index on `user_id`
* Composite index on `user_id` and `is_read`
* Index on `created_at`

### Related Requirements

* FR-089 to FR-091

---

## 8.18 Audit Logs Table

### Purpose

The `audit_logs` table stores important user and system actions.

| Column           | Data Type    | Constraints           | Description                   |
| ---------------- | ------------ | --------------------- | ----------------------------- |
| `id`             | UUID         | Primary key           | Audit-record identifier       |
| `user_id`        | UUID         | Foreign key, nullable | User performing the action    |
| `action_type`    | VARCHAR(100) | Not null              | Type of activity              |
| `entity_type`    | VARCHAR(50)  | Not null              | Affected resource type        |
| `entity_id`      | UUID         | Nullable              | Affected resource ID          |
| `action_details` | JSONB        | Nullable              | Structured action information |
| `ip_address`     | INET         | Nullable              | Request IP address            |
| `created_at`     | TIMESTAMPTZ  | Not null              | Activity time                 |

### Example Actions

* `REGISTRATION_SUBMITTED`
* `REGISTRATION_APPROVED`
* `REGISTRATION_REJECTED`
* `COURSE_DROPPED`
* `WAITLIST_PROMOTED`
* `SECTION_CAPACITY_UPDATED`
* `USER_ROLE_UPDATED`

### Indexes

* Index on `user_id`
* Index on `action_type`
* Composite index on `entity_type` and `entity_id`
* Index on `created_at`

### Related Requirements

* FR-060
* FR-070
* FR-095
* FR-096

---

# 9. Foreign-Key Relationships

| Child Table            | Foreign Key              | Parent Table      |
| ---------------------- | ------------------------ | ----------------- |
| `programs`             | `department_id`          | `departments`     |
| `students`             | `user_id`                | `users`           |
| `students`             | `program_id`             | `programs`        |
| `students`             | `advisor_id`             | `advisors`        |
| `advisors`             | `user_id`                | `users`           |
| `advisors`             | `department_id`          | `departments`     |
| `instructors`          | `user_id`                | `users`           |
| `instructors`          | `department_id`          | `departments`     |
| `registration_periods` | `semester_id`            | `semesters`       |
| `courses`              | `department_id`          | `departments`     |
| `course_prerequisites` | `course_id`              | `courses`         |
| `course_prerequisites` | `prerequisite_course_id` | `courses`         |
| `course_sections`      | `course_id`              | `courses`         |
| `course_sections`      | `semester_id`            | `semesters`       |
| `course_sections`      | `instructor_id`          | `instructors`     |
| `section_schedules`    | `section_id`             | `course_sections` |
| `section_schedules`    | `room_id`                | `rooms`           |
| `completed_courses`    | `student_id`             | `students`        |
| `completed_courses`    | `course_id`              | `courses`         |
| `registrations`        | `student_id`             | `students`        |
| `registrations`        | `section_id`             | `course_sections` |
| `registrations`        | `reviewed_by`            | `advisors`        |
| `waitlist_entries`     | `student_id`             | `students`        |
| `waitlist_entries`     | `section_id`             | `course_sections` |
| `notifications`        | `user_id`                | `users`           |
| `audit_logs`           | `user_id`                | `users`           |

---

# 10. Delete and Update Behaviors

Recommended foreign-key actions include:

| Relationship            | Recommended Action                                        |
| ----------------------- | --------------------------------------------------------- |
| User to student profile | Restrict deletion                                         |
| Course to section       | Restrict deletion when sections exist                     |
| Section to registration | Restrict deletion when registrations exist                |
| Section to schedule     | Cascade delete when an unused section is deleted          |
| Section to waitlist     | Restrict or archive                                       |
| User to notification    | Cascade delete only when account deletion is permitted    |
| User to audit log       | Set user ID to null rather than deleting logs             |
| Advisor to student      | Set advisor ID to null when advisor assignment is removed |
| Room to schedule        | Restrict deletion while schedules reference the room      |

Important academic and registration records should normally be deactivated or archived rather than physically deleted.

---

# 11. Seat Availability Query

Available seats may be calculated using:

```sql
SELECT
    cs.id AS section_id,
    cs.seat_capacity,
    COUNT(r.id) FILTER (
        WHERE r.registration_status = 'APPROVED'
    ) AS approved_count,
    cs.seat_capacity -
    COUNT(r.id) FILTER (
        WHERE r.registration_status = 'APPROVED'
    ) AS available_seats
FROM course_sections cs
LEFT JOIN registrations r
    ON r.section_id = cs.id
WHERE cs.id = :section_id
GROUP BY cs.id, cs.seat_capacity;
```

The query result must be rechecked during final seat allocation.

---

# 12. Schedule-Conflict Query Logic

Two schedules conflict when:

```text
same day
AND new start time < existing end time
AND new end time > existing start time
```

A simplified PostgreSQL query is:

```sql
SELECT
    existing_section.id AS conflicting_section_id,
    existing_course.course_code,
    existing_schedule.day_of_week,
    existing_schedule.start_time,
    existing_schedule.end_time
FROM registrations r
JOIN course_sections existing_section
    ON existing_section.id = r.section_id
JOIN courses existing_course
    ON existing_course.id = existing_section.course_id
JOIN section_schedules existing_schedule
    ON existing_schedule.section_id = existing_section.id
JOIN section_schedules new_schedule
    ON new_schedule.section_id = :new_section_id
WHERE r.student_id = :student_id
  AND r.registration_status IN ('DRAFT', 'PENDING', 'APPROVED')
  AND existing_schedule.day_of_week = new_schedule.day_of_week
  AND new_schedule.start_time < existing_schedule.end_time
  AND new_schedule.end_time > existing_schedule.start_time;
```

---

# 13. Prerequisite Validation Query Logic

The system retrieves the selected course's prerequisites and checks whether matching passed courses exist.

```sql
SELECT
    prerequisite_course.id,
    prerequisite_course.course_code,
    prerequisite_course.course_title,
    cp.minimum_grade
FROM course_prerequisites cp
JOIN courses prerequisite_course
    ON prerequisite_course.id = cp.prerequisite_course_id
WHERE cp.course_id = :course_id
  AND NOT EXISTS (
      SELECT 1
      FROM completed_courses cc
      WHERE cc.student_id = :student_id
        AND cc.course_id = cp.prerequisite_course_id
        AND cc.completion_status = 'PASSED'
  );
```

If this query returns records, those prerequisites are missing.

---

# 14. Credit Calculation Query

```sql
SELECT
    COALESCE(SUM(c.credit_value), 0) AS selected_credits
FROM registrations r
JOIN course_sections cs
    ON cs.id = r.section_id
JOIN courses c
    ON c.id = cs.course_id
WHERE r.student_id = :student_id
  AND cs.semester_id = :semester_id
  AND r.registration_status IN ('DRAFT', 'PENDING', 'APPROVED');
```

The result is compared with the applicable minimum and maximum credit values.

---

# 15. Waiting-List Position Query

```sql
SELECT COUNT(*) + 1 AS queue_position
FROM waitlist_entries other_entry
WHERE other_entry.section_id = :section_id
  AND other_entry.waitlist_status = 'ACTIVE'
  AND (
      other_entry.joined_at < :joined_at
      OR (
          other_entry.joined_at = :joined_at
          AND other_entry.id < :entry_id
      )
  );
```

The queue position is calculated only among active entries.

---

# 16. Transaction Design

Transactions are required for operations that modify several related records.

## 16.1 Final Registration Submission

A transaction should include:

1. Lock affected sections.
2. Recheck seat availability.
3. Recheck registration rules.
4. Update registration statuses.
5. Create notifications.
6. Create audit records.
7. Commit all changes together.

If any operation fails, all changes should be rolled back.

## 16.2 Advisor Approval

A transaction should include:

1. Lock the pending registration.
2. Lock the related section.
3. Recheck section capacity.
4. Change status to Approved.
5. Store advisor information.
6. Create a notification.
7. Create an audit record.
8. Commit.

## 16.3 Course Drop

A transaction should include:

1. Lock the registration.
2. Change status to Dropped.
3. Release the seat.
4. Process the waiting list.
5. Notify affected users.
6. Create an audit log.
7. Commit.

## 16.4 Waiting-List Promotion

A transaction should include:

1. Lock the course section.
2. Retrieve the first active waitlist entry.
3. Revalidate student eligibility.
4. Promote the eligible student.
5. Update the waitlist status.
6. Create or update the registration record.
7. Create a notification.
8. Create an audit record.
9. Commit.

---

# 17. Row-Level Locking

PostgreSQL row-level locking should be used during final seat allocation.

```sql
SELECT id, seat_capacity
FROM course_sections
WHERE id = :section_id
FOR UPDATE;
```

This prevents multiple transactions from allocating the same final seat simultaneously.

---

# 18. Index Design

Recommended indexes include:

```sql
CREATE UNIQUE INDEX uq_users_email
ON users (email);

CREATE UNIQUE INDEX uq_courses_course_code
ON courses (course_code);

CREATE INDEX ix_course_sections_semester_id
ON course_sections (semester_id);

CREATE INDEX ix_registrations_student_status
ON registrations (student_id, registration_status);

CREATE INDEX ix_registrations_section_status
ON registrations (section_id, registration_status);

CREATE INDEX ix_waitlist_section_status_joined
ON waitlist_entries (
    section_id,
    waitlist_status,
    joined_at
);

CREATE INDEX ix_section_schedules_conflict
ON section_schedules (
    day_of_week,
    start_time,
    end_time
);

CREATE INDEX ix_completed_courses_student_status
ON completed_courses (
    student_id,
    completion_status
);

CREATE INDEX ix_notifications_user_read
ON notifications (
    user_id,
    is_read
);
```

Indexes should be reviewed based on actual query performance.

---

# 19. Data Integrity Rules

The database must enforce the following rules:

1. User email must be unique.
2. Student number must be unique.
3. Course code must be unique.
4. A course cannot be its own prerequisite.
5. A section capacity must be positive.
6. Room capacity must be positive.
7. Class end time must be later than start time.
8. Registration opening time must be earlier than closing time.
9. Maximum credits must not be below minimum credits.
10. A student cannot register for the same section twice.
11. A student cannot join the same section's waiting list twice.
12. Registration status must use a supported value.
13. Waiting-list status must use a supported value.
14. Foreign-key references must point to valid records.
15. Approved enrollment must not exceed section capacity.

The approved-enrollment limit is enforced primarily through transactional application logic because it depends on counting multiple registration rows.

---

# 20. Data Security

## 20.1 Password Protection

Only password hashes shall be stored.

The following must never be stored:

* Plain-text passwords
* Passwords in logs
* Access tokens in audit records

## 20.2 Database Credentials

Database credentials must be stored in environment variables.

```text
DATABASE_URL=postgresql+psycopg://username:password@database:5432/coursepilot
```

The real `.env` file must not be committed to GitHub.

## 20.3 Database User Permissions

The application should use a restricted database account.

The account should have only the permissions required by CoursePilot.

## 20.4 Sensitive Data Access

* Students may only access their own records.
* Advisors may only access assigned students.
* Administrators require appropriate roles.
* Audit logs should be restricted to authorized administrators.

---

# 21. Backup and Recovery

The database should support regular backups.

A PostgreSQL backup may be created using:

```bash
pg_dump -U coursepilot_user -d coursepilot > coursepilot_backup.sql
```

A backup may be restored using:

```bash
psql -U coursepilot_user -d coursepilot < coursepilot_backup.sql
```

Backup files should:

* Be stored securely
* Be protected from unauthorized access
* Include creation dates
* Be tested periodically
* Not be stored directly in the public GitHub repository

---

# 22. Database Migration Strategy

Alembic should be used to manage database-schema changes.

Typical commands include:

```bash
alembic revision --autogenerate -m "create initial tables"
alembic upgrade head
```

Each migration should:

* Have a clear name
* Include upgrade logic
* Include downgrade logic when practical
* Be reviewed before production deployment
* Be committed to the repository

---

# 23. Seed Data

Development seed data may include:

* One department
* One academic program
* Student accounts
* Advisor accounts
* Instructor accounts
* One active semester
* One registration period
* Sample courses
* Sample sections
* Sample prerequisites
* Sample room and schedule records
* Sample completed-course records

Seed data must not contain real passwords or confidential student information.

---

# 24. Data Retention

Recommended retention rules include:

* Registration history should be retained.
* Advisor decisions should be retained.
* Audit logs should be retained.
* Dropped registrations should remain recorded.
* Removed waiting-list entries should remain available for auditing.
* Old semesters may be archived.
* User accounts may be deactivated instead of deleted.

---

# 25. Database Error Handling

The backend should translate database errors into understandable API responses.

| Database Error               | API Response                                  |
| ---------------------------- | --------------------------------------------- |
| Unique user email violation  | Email already exists                          |
| Duplicate registration       | Student is already registered for the section |
| Duplicate waiting-list entry | Student is already on the waiting list        |
| Foreign-key violation        | Related record does not exist                 |
| Check-constraint violation   | Submitted value is invalid                    |
| Transaction conflict         | Operation should be retried                   |
| Database unavailable         | Temporary server error                        |

Internal database messages must not be returned directly to normal users.

---

# 26. Requirement Traceability

The following requirement identifiers come from `13-functional-requirements.md`.

| Database Area                            | Related Functional Requirements    |
| ---------------------------------------- | ---------------------------------- |
| User accounts and roles                  | FR-001 to FR-005, FR-092 to FR-096 |
| Course catalogue                         | FR-009 to FR-013, FR-071 to FR-072 |
| Seat management                          | FR-014 to FR-018                   |
| Course selection                         | FR-019 to FR-024                   |
| Prerequisite validation                  | FR-025 to FR-028                   |
| Credit validation                        | FR-029 to FR-034                   |
| Schedule-conflict detection              | FR-035 to FR-040                   |
| Waiting-list management                  | FR-041 to FR-050                   |
| Final registration                       | FR-051 to FR-057                   |
| Registration status                      | FR-058 to FR-061                   |
| Advisor review                           | FR-062 to FR-070                   |
| Course and section administration        | FR-071 to FR-084                   |
| Student schedule                         | FR-085 to FR-088                   |
| Notifications                            | FR-089 to FR-091                   |
| System administration and audit          | FR-092 to FR-096                   |
| Error handling and transaction integrity | FR-097 to FR-100                   |

---

# 27. Assumptions

The database design assumes that:

* One user has one primary system role.
* Every student belongs to one academic program.
* Every student may have one assigned advisor.
* A course may have multiple sections.
* A section belongs to one semester.
* A section may have multiple weekly schedule records.
* Waiting-list order follows server-generated timestamps.
* Only approved registrations consume confirmed seats.
* Academic records are available for prerequisite validation.
* Historical records should normally be archived rather than deleted.

---

# 28. Future Database Enhancements

Possible future additions include:

* Degree requirements
* Course-retake approvals
* Student-specific credit exceptions
* Multiple advisor assignments
* Registration request groups
* Email and SMS delivery records
* Payment records
* Attendance records
* Grade records
* Course recommendations
* Analytics tables
* University ERP synchronization logs

---

# 29. Conclusion

The CoursePilot database design provides a structured PostgreSQL schema for user management, course offerings, registration, prerequisites, schedule validation, seat allocation, waiting lists, advisor decisions, notifications, and auditing.

The design uses:

* UUID primary keys
* Foreign-key relationships
* Unique constraints
* Check constraints
* Controlled status values
* Indexes
* Database transactions
* Row-level locking
* Backup and migration procedures

This database structure will support the CoursePilot REST API and the business rules defined in the functional requirements and Technical Design Document.
