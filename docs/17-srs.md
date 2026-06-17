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

## 9.1 Authentication

### FR-001

The system shall allow registered users to log in using valid credentials.

### FR-002

The system shall reject invalid login attempts.

### FR-003

The system shall allow authenticated users to log out.

### FR-004

The system shall enforce role-based access.

### FR-005

The system shall prevent unauthorized access.

---

## 9.2 Course Browsing

### FR-006

The system shall display available courses and sections.

### FR-007

The system shall allow search by course code or title.

### FR-008

The system shall allow filtering by department, trimester, availability, and course type.

### FR-009

The system shall display:

* Course code
* Course title
* Credit
* Section
* Instructor
* Class day
* Start and end time
* Room number
* Seat capacity
* Available seats
* Prerequisites
* Mandatory or elective status

---

## 9.3 Seat Management

### FR-010

The system shall display current available seats.

### FR-011

The system shall update seat availability when enrollment changes.

### FR-012

The system shall recheck seat availability during confirmation.

### FR-013

The system shall prevent over-enrollment.

### FR-014

The system shall identify full sections.

---

## 9.4 Course Selection

### FR-015

The system shall allow students to select eligible course sections.

### FR-016

The system shall display all selected courses.

### FR-017

The system shall allow removal of a selected course before final submission.

### FR-018

The system shall prevent duplicate course selection.

### FR-019

The system shall prevent registration for a previously passed course unless retake permission exists.

### FR-020

The system shall display selected course schedules while the student browses other sections.

---

## 9.5 Prerequisite Validation

### FR-021

The system shall display prerequisite requirements.

### FR-022

The system shall compare prerequisites with completed-course records.

### FR-023

The system shall block course selection when a prerequisite is missing.

### FR-024

The system shall display missing prerequisite information.

---

## 9.6 Credit Validation

### FR-025

The system shall calculate total selected credits.

### FR-026

The selected-credit total shall update immediately after course changes.

### FR-027

The system shall display minimum and maximum credit limits.

### FR-028

The system shall block final submission below the minimum credit requirement.

### FR-029

The system shall block final submission above the maximum credit limit.

---

## 9.7 Schedule-Conflict Detection

### FR-030

The system shall detect overlapping schedules.

### FR-031

A conflict shall exist when two sections occur on the same day and their time ranges overlap.

### FR-032

The system shall display both conflicting courses, sections, days, and times.

### FR-033

The system shall block conflicting course selection.

### FR-034

The system shall block final submission while any conflict exists.

---

## 9.8 Waiting-List Management

### FR-035

The system shall allow eligible students to join a waiting list when a section is full.

### FR-036

The system shall order waiting-list entries by joining time.

### FR-037

The system shall display the current waiting-list position.

### FR-038

The system shall prevent duplicate waiting-list entries.

### FR-039

The system shall allow students to leave a waiting list.

### FR-040

The system shall update waiting-list positions automatically.

### FR-041

The system shall identify the first eligible student when a seat becomes available.

### FR-042

The system shall update the promoted student’s status according to institutional policy.

---

## 9.9 Final Registration Submission

### FR-043

The system shall display a registration summary before final submission.

### FR-044

The system shall validate:

* Registration period
* Prerequisites
* Credit limits
* Schedule conflicts
* Duplicate courses
* Completed-course restrictions
* Seat availability

### FR-045

The system shall submit the registration request when all validations pass.

### FR-046

The system shall assign Pending status when advisor approval is required.

### FR-047

The system shall block invalid submission.

### FR-048

The system shall display clear validation messages.

---

## 9.10 Advisor Approval

### FR-049

The system shall allow advisors to view pending requests.

### FR-050

The system shall display student, course, credit, prerequisite, and conflict details.

### FR-051

The system shall allow advisors to approve requests.

### FR-052

The system shall allow advisors to reject requests.

### FR-053

The system shall require a rejection reason.

### FR-054

The system shall allow advisors to add comments.

### FR-055

The system shall maintain decision history.

---

## 9.11 Registration Status

### FR-056

The system shall display the following statuses:

* Draft
* Pending
* Approved
* Rejected
* Waitlisted
* Dropped

### FR-057

The system shall display rejection reasons.

### FR-058

The system shall maintain status history.

### FR-059

The system shall allow eligible course drops before the deadline.

---

## 9.12 Course and Section Administration

### FR-060

The system shall allow department administrators to create and update courses.

### FR-061

The system shall allow department administrators to create and update sections.

### FR-062

The system shall allow seat-capacity configuration.

### FR-063

The system shall allow instructor assignment.

### FR-064

The system shall allow room assignment.

### FR-065

The system shall allow class schedule configuration.

### FR-066

The system shall allow prerequisite configuration.

### FR-067

The system shall allow courses to be marked mandatory or elective.

### FR-068

The system shall allow registration periods to be opened and closed.

### FR-069

The system shall display section enrollment and waiting-list information.

---

## 9.13 Student Schedule

### FR-070

The system shall display all approved courses.

### FR-071

The system shall display:

* Course code
* Course title
* Section
* Instructor
* Day
* Start time
* End time
* Room
* Credit
* Status

### FR-072

The system shall provide a weekly timetable view.

### FR-073

The system shall provide a list view.

---

## 9.14 System Administration

### FR-074

The system shall allow user account creation and updating.

### FR-075

The system shall allow account activation and deactivation.

### FR-076

The system shall allow role assignment.

### FR-077

The system shall enforce role permissions.

### FR-078

The system shall record important activities.

### FR-079

The system shall maintain an audit trail.

---

# 10. Non-Functional Requirements

## 10.1 Performance

### NFR-001

Standard pages should load within three seconds under normal conditions.

### NFR-002

Normal API requests should complete within two seconds.

### NFR-003

Registration validation should complete within three seconds.

### NFR-004

Course search results should appear within two seconds.

### NFR-005

The initial system should support at least 500 concurrent users.

---

## 10.2 Reliability

### NFR-006

Registration operations shall not create incomplete records.

### NFR-007

Seat allocation shall use database transactions.

### NFR-008

Waiting-list order shall remain consistent.

### NFR-009

Failed registration operations shall roll back incomplete changes.

### NFR-010

Registration statuses shall remain consistent across all user views.

---

## 10.3 Security

### NFR-011

Protected functions shall require authentication.

### NFR-012

Passwords shall be securely hashed.

### NFR-013

The system shall enforce role-based authorization.

### NFR-014

Students shall only access their own records.

### NFR-015

Sensitive communication should use HTTPS.

### NFR-016

All inputs shall be validated.

### NFR-017

Database access shall use an ORM or parameterized queries.

### NFR-018

Error responses shall not expose sensitive internal information.

---

## 10.4 Usability

### NFR-019

The user interface shall provide clear navigation.

### NFR-020

Validation messages shall identify the problem and affected course.

### NFR-021

Registration statuses shall be clearly visible.

### NFR-022

Seat availability and selected credits shall remain easy to view.

### NFR-023

The schedule shall be readable and organized.

---

## 10.5 Compatibility

### NFR-024

The system shall support recent desktop and mobile browsers.

### NFR-025

The frontend shall be responsive.

### NFR-026

The API shall use JSON.

### NFR-027

The API shall use standard HTTP methods and status codes.

---

## 10.6 Maintainability

### NFR-028

The system shall use a modular architecture.

### NFR-029

Source code shall follow consistent naming and formatting.

### NFR-030

The project shall include setup, API, database, and technical documentation.

### NFR-031

Git and GitHub shall be used for version control.

### NFR-032

GitHub Issues and Projects shall be used for task tracking.

---

## 10.7 Data Integrity

### NFR-033

Duplicate registrations shall be prevented.

### NFR-034

Duplicate waiting-list entries shall be prevented.

### NFR-035

Section capacity shall be a positive integer.

### NFR-036

Approved enrollment shall not exceed section capacity.

### NFR-037

Foreign-key relationships shall maintain referential integrity.

### NFR-038

Class end time shall be later than start time.

---

## 10.8 Logging and Recovery

### NFR-039

Backend errors shall be logged.

### NFR-040

Registration decisions shall be recorded.

### NFR-041

Administrative changes shall be recorded.

### NFR-042

Regular database backups should be created.

### NFR-043

Authorized administrators should be able to restore valid backups.

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
