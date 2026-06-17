# CoursePilot Software Requirements Specification

## 1. Introduction

### 1.1 Purpose

This Software Requirements Specification defines the functional, non-functional, interface, data, security, and business requirements of CoursePilot.

CoursePilot is a web-based course registration and waitlist management system designed to help students register for courses, monitor seat availability, join waiting lists, satisfy academic requirements, track approval status, and view their approved class schedules.

This document will guide the design, implementation, testing, and evaluation of the system.

### 1.2 Document Scope

This document covers:

* System purpose and scope
* User roles
* Functional requirements
* Non-functional requirements
* Business rules
* Use cases
* External interfaces
* Data requirements
* Security requirements
* Assumptions and constraints

### 1.3 Intended Audience

This document is intended for:

* Students
* Academic advisors
* Department administrators
* System administrators
* Project evaluators
* Developers
* Testers
* Future maintenance teams

### 1.4 Related Documents

The following documents provide supporting requirements and technical information for CoursePilot:

* [Project Overview](01-project-overview.md)
* [Product Requirements Document](08-prd.md)
* [User Personas](09-user-personas.md)
* [User Journey](10-user-journey.md)
* [User Stories](11-user-stories.md)
* [Acceptance Criteria](12-acceptance-criteria.md)
* [Functional Requirements](13-functional-requirements.md)
* [Non-Functional Requirements](14-non-functional-requirements.md)
* [Use Cases](15-use-cases.md)
* [Data Flow Diagrams](16-dfd.md)
* [Entity Relationship Diagram](18-erd.md)
* [System Design](19-system-design.md)
* [Technical Design Document](20-tdd.md)
* [Database Design](21-database-design.md)
* [REST API Design](22-api-design.md)

---

## 2. Product Overview

CoursePilot provides a centralized platform for managing university course registration.

Students can:

* Log in
* Browse courses and sections
* View available seats
* View prerequisites
* Select eligible courses
* Monitor selected credits
* Detect schedule conflicts
* Join waiting lists
* Submit final registration
* Track approval status
* View approved schedules

Academic advisors can review, approve, or reject registration requests.

Department administrators can manage courses, sections, schedules, rooms, instructors, prerequisites, capacities, and registration periods.

System administrators can manage accounts, roles, permissions, logs, and system configuration.

---

## 3. Product Objectives

CoursePilot aims to:

1. Improve the course-registration experience.
2. Display accurate seat availability.
3. Provide a structured waiting-list process.
4. Make waiting-list positions visible.
5. Display prerequisite requirements clearly.
6. Validate prerequisite completion automatically.
7. Calculate selected credits instantly.
8. Enforce minimum and maximum credit limits.
9. Detect overlapping class schedules.
10. Block invalid final submissions.
11. Support advisor approval and rejection.
12. Provide clear registration statuses.
13. Display approved courses in a complete weekly schedule.
14. Reduce manual administrative work.

---

## 4. Product Scope

### 4.1 In-Scope Features

The first version of CoursePilot will include:

* User authentication
* Role-based access
* Student dashboard
* Course and section browsing
* Course search and filtering
* Seat-capacity display
* Seat revalidation during confirmation
* Course selection
* Prerequisite checking
* Mandatory-course labelling
* Credit calculation
* Minimum and maximum credit validation
* Schedule-conflict detection
* Final-submission blocking
* Waiting-list management
* Waiting-list position tracking
* Registration submission
* Advisor approval and rejection
* Rejection reasons
* Registration-status tracking
* Course-drop functionality
* Student schedule and weekly timetable
* Course and section administration
* User and role administration
* Activity and audit logging

### 4.2 Out-of-Scope Features

The first version will not include:

* Tuition payment
* Grade management
* Attendance management
* Examination management
* Learning-management-system features
* Full university ERP integration
* Native mobile application
* Automated degree audit
* Automated instructor workload calculation

---

## 5. User Classes

### 5.1 Student

Students are the primary users.

They can:

* Browse courses
* Select sections
* View seats
* Check prerequisites
* Monitor credits
* Join waiting lists
* Submit registration
* Track statuses
* View schedules

### 5.2 Academic Advisor

Academic advisors can:

* View assigned students
* Review pending requests
* Check academic eligibility
* Approve registrations
* Reject registrations
* Add comments
* View decision history

### 5.3 Department Administrator

Department administrators can:

* Create and update courses
* Create sections
* Set capacities
* Assign instructors
* Assign rooms
* Define schedules
* Define prerequisites
* Mark mandatory courses
* Manage registration periods
* Monitor registrations and waiting lists

### 5.4 System Administrator

System administrators can:

* Manage user accounts
* Assign roles
* Manage permissions
* Monitor logs
* Maintain security
* Manage system settings
* Support backup and recovery

---

## 6. Operating Environment

### 6.1 Client Environment

CoursePilot will operate through a web browser.

Supported browsers should include recent versions of:

* Google Chrome
* Mozilla Firefox
* Microsoft Edge
* Safari

### 6.2 Server Environment

The proposed server environment includes:

* FastAPI backend
* PostgreSQL database
* REST API
* JWT-based authentication
* Linux-compatible deployment environment
* Optional Docker deployment

### 6.3 Frontend Environment

The frontend will be developed using:

* React
* TypeScript
* Vite
* Responsive web design

---

## 7. Assumptions

The system assumes that:

1. Students already have university accounts.
2. User roles are assigned correctly.
3. Student academic records are available.
4. Completed-course information is accurate.
5. Courses are configured before registration begins.
6. Sections contain valid schedules and capacities.
7. Registration periods are configured.
8. Students are assigned to academic advisors.
9. Prerequisite information is accurate.
10. Room and instructor information is available.

---

## 8. Constraints

The project is subject to the following constraints:

* Limited development time
* Limited initial integration with university systems
* Academic rules may differ by department
* Registration policies may change
* High traffic may occur during registration
* Survey and interview participation may be limited
* The first version will focus on core functionality

---


# 9. Functional Requirements

The complete and authoritative functional requirements for CoursePilot are documented in [13-functional-requirements.md](13-functional-requirements.md).

The identifiers defined in that document, from `FR-001` through `FR-100`, shall be used consistently throughout the SRS, Technical Design Document, database design, API design, use cases, test cases, and requirement-traceability records.

## 9.1 Functional Requirement Summary

| Requirement Area                 | Requirement IDs  | Summary                                                                                                                   |
| -------------------------------- | ---------------- | ------------------------------------------------------------------------------------------------------------------------- |
| Authentication and authorization | FR-001 to FR-005 | User login, logout, role-based access, and unauthorized-access prevention                                                 |
| Student dashboard                | FR-006 to FR-008 | Student dashboard, registration-period status, and registration summary                                                   |
| Course browsing                  | FR-009 to FR-013 | Course viewing, searching, filtering, details, and mandatory-course labels                                                |
| Seat availability                | FR-014 to FR-018 | Available-seat display, seat updates, revalidation, over-enrollment prevention, and full-section notification             |
| Course selection                 | FR-019 to FR-024 | Section selection, selected-course management, duplicate prevention, completed-course validation, and schedule visibility |
| Prerequisite validation          | FR-025 to FR-028 | Prerequisite display, completion checking, blocking, and missing-prerequisite details                                     |
| Credit validation                | FR-029 to FR-034 | Credit calculation, instant updates, limits, validation, and error messages                                               |
| Schedule-conflict detection      | FR-035 to FR-040 | Conflict detection, overlap rules, conflict details, blocking, and corrective guidance                                    |
| Waiting-list management          | FR-041 to FR-050 | Waiting-list eligibility, queue order, position, entry management, promotion, and status updates                          |
| Final registration submission    | FR-051 to FR-057 | Registration summary, final validation, submission, pending status, errors, and closed-period handling                    |
| Registration status              | FR-058 to FR-061 | Status display, rejection reasons, registration history, and course dropping                                              |
| Academic advisor functions       | FR-062 to FR-070 | Advisor login, assigned students, request review, approval, rejection, comments, and history                              |
| Department administration        | FR-071 to FR-084 | Course, section, capacity, instructor, room, schedule, prerequisite, period, enrollment, and waitlist management          |
| Student schedule                 | FR-085 to FR-088 | Approved courses, schedule details, weekly timetable, and list view                                                       |
| Notifications                    | FR-089 to FR-091 | Registration, waiting-list, and advisor-decision notifications                                                            |
| System administration            | FR-092 to FR-096 | User accounts, roles, permissions, activity logs, and audit trails                                                        |
| Error handling                   | FR-097 to FR-100 | Clear errors, standardized API responses, selection preservation, and transaction consistency                             |

## 9.2 Requirement Authority

When another CoursePilot document refers to a functional requirement, the identifier and definition in [13-functional-requirements.md](13-functional-requirements.md) shall take priority.

This prevents the same requirement from receiving different identifiers in different documents.


---

# 10. Non-Functional Requirements

The complete and authoritative non-functional requirements for CoursePilot are documented in [14-non-functional-requirements.md](14-non-functional-requirements.md).

The identifiers defined in that document, from `NFR-001` through `NFR-084`, shall be used consistently throughout the SRS, Technical Design Document, system design, database design, API design, implementation, and testing documents.

## 10.1 Non-Functional Requirement Summary

| Requirement Area    | Requirement IDs    | Summary                                                                                                                                       |
| ------------------- | ------------------ | --------------------------------------------------------------------------------------------------------------------------------------------- |
| Performance         | NFR-001 to NFR-006 | Page loading, API response time, registration validation, seat updates, concurrent users, and search performance                              |
| Availability        | NFR-007 to NFR-010 | System availability, maintenance scheduling, service recovery, and registration-period availability                                           |
| Reliability         | NFR-011 to NFR-016 | Consistent registration processing, seat allocation, waiting-list order, transactions, rollback, and status consistency                       |
| Security            | NFR-017 to NFR-028 | Authentication, password protection, authorization, secure communication, session control, input validation, and secure error handling        |
| Privacy             | NFR-029 to NFR-032 | Student-data confidentiality, minimum data access, limited data collection, and accountability                                                |
| Usability           | NFR-033 to NFR-040 | Navigation, interface clarity, feedback, validation messages, status visibility, schedule readability, seat visibility, and credit visibility |
| Accessibility       | NFR-041 to NFR-045 | Keyboard navigation, form labels, text contrast, error identification, and readable zoomed text                                               |
| Compatibility       | NFR-046 to NFR-049 | Browser compatibility, responsive design, JSON communication, and standard web protocols                                                      |
| Scalability         | NFR-050 to NFR-053 | User growth, database growth, horizontal expansion, and searchable-field indexing                                                             |
| Maintainability     | NFR-054 to NFR-060 | Modular architecture, readable code, documentation, version control, issue tracking, configuration, and dependency management                 |
| Testability         | NFR-061 to NFR-065 | Unit tests, API tests, registration-rule tests, invalid-input tests, and repeatable test results                                              |
| Data Integrity      | NFR-066 to NFR-072 | Duplicate prevention, valid capacity, enrollment limits, referential integrity, valid schedules, and controlled statuses                      |
| Backup and Recovery | NFR-073 to NFR-076 | Regular backups, secure backup storage, restoration, and recovery testing                                                                     |
| Logging and Audit   | NFR-077 to NFR-080 | Error logging, registration auditing, administrative auditing, and log protection                                                             |
| Deployment          | NFR-081 to NFR-084 | Environment separation, environment variables, Docker support, and API documentation                                                          |

## 10.2 Requirement Authority

When another CoursePilot document refers to a non-functional requirement, the identifier and definition in [14-non-functional-requirements.md](14-non-functional-requirements.md) shall take priority.

This prevents the same non-functional requirement from receiving different identifiers in separate documents.


---

# 11. External Interface Requirements

## 11.1 User Interface

The student interface shall provide:

* Login page
* Dashboard
* Course-search page
* Course-details page
* Selected-course list
* Credit summary
* Conflict messages
* Waiting-list page
* Registration-status page
* Weekly schedule

The advisor interface shall provide:

* Pending-request list
* Student registration details
* Approval and rejection controls
* Comment field
* Decision history

The administrator interface shall provide:

* Course management
* Section management
* Capacity management
* Schedule and room management
* Prerequisite management
* Registration-period management
* Enrollment and waitlist monitoring

## 11.2 API Interface

The React frontend will communicate with the FastAPI backend using REST APIs.

Example API categories include:

* Authentication
* Courses
* Sections
* Registrations
* Waiting lists
* Student schedules
* Advisor decisions
* Administrative management

## 11.3 Database Interface

The FastAPI backend will communicate with PostgreSQL through SQLAlchemy or another compatible ORM.

## 11.4 Communication Interface

The deployed system should use HTTPS.

Data will be exchanged using JSON.

---

# 12. Data Requirements

## 12.1 Main Data Entities

The system will maintain data for:

* Users
* Students
* Advisors
* Departments
* Courses
* Course sections
* Semesters
* Rooms
* Class schedules
* Prerequisites
* Completed courses
* Registrations
* Waiting-list entries
* Registration periods
* Notifications
* Audit logs

## 12.2 Data Validation

The system shall validate:

* Required fields
* Unique user identifiers
* Unique course codes
* Positive seat capacities
* Valid schedule times
* Valid registration statuses
* Valid foreign-key relationships
* Duplicate registration prevention
* Duplicate waiting-list prevention

## 12.3 Data Retention

Registration decisions and status history should remain available for auditing and academic review.

---

# 13. Business Rules

## BR-001: Registration Period

Students may submit registrations only during an active registration period.

## BR-002: Seat Capacity

Approved registration count shall not exceed section capacity.

## BR-003: Seat Revalidation

Seat availability shall be checked again during confirmation.

## BR-004: Waiting List

An eligible student may join a waiting list when a section is full.

## BR-005: Waiting-List Order

Waiting-list order shall follow joining date and time.

## BR-006: Prerequisites

Students shall complete all required prerequisites before registration.

## BR-007: Minimum Credit

Final submission shall satisfy the minimum credit requirement.

## BR-008: Maximum Credit

Final submission shall not exceed the maximum credit limit.

## BR-009: Schedule Conflict

A student shall not submit overlapping course sections.

## BR-010: Duplicate Registration

A student shall not register for the same course section more than once.

## BR-011: Completed Course

A student shall not register for a previously passed course unless retake permission exists.

## BR-012: Advisor Approval

Registrations requiring advisor review shall remain pending until a decision is made.

## BR-013: Rejection Reason

An advisor must provide a reason when rejecting a request.

## BR-014: Course Drop

A course may be dropped only before the configured deadline.

---

# 14. Major Use Cases

The main CoursePilot use cases include:

1. User login
2. Browse and search courses
3. Select a course section
4. Validate prerequisites
5. Detect schedule conflicts
6. Validate credit limits
7. Join a waiting list
8. Submit final registration
9. Review registration request
10. View registration status
11. View registered schedule
12. Manage courses and sections
13. Manage waiting lists
14. Drop a registered course
15. Manage user accounts and roles

Detailed flows are documented in `15-use-cases.md`.

---

# 15. Data Flow Summary

CoursePilot exchanges data among:

* Students
* Academic advisors
* Department administrators
* System administrators
* Course records
* Academic records
* Registration records
* Waiting-list records
* Schedule records
* User accounts
* Audit logs

The detailed Context, Level 0, and Level 1 Data Flow Diagrams are documented in `16-dfd.md`.

---

# 16. Error Handling

The system shall provide clear messages for:

* Invalid login
* Missing prerequisite
* Duplicate selection
* Previously completed course
* Schedule conflict
* Minimum-credit violation
* Maximum-credit violation
* Full section
* Duplicate waitlist request
* Closed registration period
* Unauthorized access
* Invalid administrator input
* Failed registration operation

The system should preserve student selections after recoverable validation errors.

---

# 17. Acceptance Summary

CoursePilot will be accepted when:

1. Users can log in securely.
2. Students can browse and search courses.
3. Available seats are displayed and revalidated.
4. Prerequisites are visible and validated.
5. Credits are calculated instantly.
6. Credit limits are enforced.
7. Schedule conflicts are detected.
8. Conflicting final submissions are blocked.
9. Full sections support waiting lists.
10. Waiting-list positions are visible.
11. Final registration can be submitted when valid.
12. Advisors can approve or reject requests.
13. Rejection reasons are visible.
14. Students can track registration statuses.
15. Approved courses appear in a complete schedule.
16. Administrators can manage course-registration data.
17. Role-based access is enforced.

---

# 18. Future Enhancements

Possible future improvements include:

* Email notifications
* SMS notifications
* Automatic degree-progress checking
* Course recommendation
* Advisor appointment scheduling
* Tuition-payment integration
* Native mobile application
* Full ERP integration
* Registration analytics
* Classroom-capacity validation
* Automated waitlist expiration

---

# 19. Conclusion

This SRS defines the expected behavior and quality standards of CoursePilot.

The system will provide a structured course-registration process with seat management, waiting-list tracking, prerequisite validation, credit validation, schedule-conflict prevention, advisor approval, status tracking, and student schedule management.

This document will serve as the foundation for the CoursePilot Technical Design Document, Entity Relationship Diagram, database design, API design, implementation, and testing.
