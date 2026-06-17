# CoursePilot Non-Functional Requirements

## 1. Introduction

Non-functional requirements define the quality standards and operational constraints of CoursePilot. They describe how the system should perform rather than the specific functions it should provide.

Each requirement uses the following identifier format:

```text
NFR-XXX
```

---

# 2. Performance Requirements

## NFR-001: Page Response Time

The system should load standard pages within three seconds under normal operating conditions.

## NFR-002: API Response Time

The backend API should respond to normal read requests within two seconds under standard system load.

## NFR-003: Registration Validation Time

Course-registration validation should complete within three seconds, including:

* Prerequisite checking
* Credit calculation
* Schedule-conflict checking
* Seat verification

## NFR-004: Seat Update Speed

Changes in available seats should be reflected in the system within five seconds.

## NFR-005: Concurrent Users

The system should support at least 500 concurrent users during course-registration periods.

## NFR-006: Search Performance

Course search and filtering results should appear within two seconds.

---

# 3. Availability Requirements

## NFR-007: System Availability

CoursePilot should maintain at least 99% availability during active registration periods.

## NFR-008: Planned Maintenance

Planned maintenance should be scheduled outside major registration periods whenever possible.

## NFR-009: Service Recovery

The system should recover from common service failures within 30 minutes.

## NFR-010: Registration-Period Availability

Core registration features must remain available throughout the configured registration period.

---

# 4. Reliability Requirements

## NFR-011: Consistent Registration Processing

The system shall process registration requests consistently and prevent incomplete registration records.

## NFR-012: Seat Allocation Reliability

The system shall verify seat availability before confirming enrollment.

## NFR-013: Waiting-List Order Reliability

Waiting-list positions shall remain ordered according to the recorded joining date and time.

## NFR-014: Transaction Reliability

Seat allocation, registration creation, and waiting-list promotion shall use database transactions.

## NFR-015: Failure Handling

If a registration operation fails, the system shall roll back incomplete database changes.

## NFR-016: Status Consistency

Registration statuses shall remain consistent across student, advisor, and administrator views.

---

# 5. Security Requirements

## NFR-017: Secure Authentication

The system shall require authentication before users access protected features.

## NFR-018: Password Protection

Passwords shall be stored using a secure password-hashing method.

## NFR-019: Role-Based Authorization

The system shall restrict access according to the user's assigned role.

## NFR-020: Protected Student Records

Students shall only access their own academic and registration information.

## NFR-021: Administrative Access

Only authorized administrators shall create or modify courses, sections, prerequisites, rooms, and seat capacities.

## NFR-022: Advisor Access

Academic advisors shall only access registration requests for students assigned to them, unless broader permission is granted.

## NFR-023: Secure Communication

Data transmitted between the frontend and backend should use HTTPS in the deployed environment.

## NFR-024: Session Expiration

Inactive user sessions should expire after a configurable period.

## NFR-025: Login Protection

The system should limit repeated failed login attempts.

## NFR-026: Input Validation

All frontend and backend inputs shall be validated before processing.

## NFR-027: SQL Injection Prevention

The backend shall use parameterized queries or an ORM to reduce SQL injection risk.

## NFR-028: Sensitive Error Protection

Error messages shall not expose database credentials, server details, access tokens, or internal stack traces to normal users.

---

# 6. Privacy Requirements

## NFR-029: Data Privacy

Student academic and registration information shall be treated as confidential.

## NFR-030: Minimum Data Access

Users shall only access the minimum information required for their responsibilities.

## NFR-031: Personal Information Collection

The system shall not collect unnecessary personal information.

## NFR-032: Activity Logging

Sensitive administrative actions shall be recorded for accountability.

---

# 7. Usability Requirements

## NFR-033: Simple Navigation

Users should be able to access primary features within three navigation actions from the dashboard.

## NFR-034: Clear Interface

The interface shall use clear labels, buttons, headings, and status indicators.

## NFR-035: Registration Feedback

The system shall display immediate feedback after registration, waitlist, approval, rejection, and course-drop actions.

## NFR-036: Clear Validation Messages

Validation messages shall explain:

* What went wrong
* Which course is affected
* What the student should do next

## NFR-037: Status Visibility

Registration statuses shall be visually distinguishable.

## NFR-038: Schedule Readability

The class schedule shall clearly display course, section, day, time, room, and instructor information.

## NFR-039: Seat Visibility

The available-seat count shall be visible without requiring the student to open multiple pages.

## NFR-040: Credit Visibility

The selected-credit total shall remain visible while the student selects courses.

---

# 8. Accessibility Requirements

## NFR-041: Keyboard Navigation

Major system functions should be accessible using keyboard navigation.

## NFR-042: Form Labels

All form fields shall include clear and descriptive labels.

## NFR-043: Text Contrast

Text and interface elements should maintain sufficient visual contrast.

## NFR-044: Error Identification

Errors shall not be communicated using colour alone.

## NFR-045: Responsive Text

Text should remain readable when users increase browser zoom.

---

# 9. Compatibility Requirements

## NFR-046: Browser Compatibility

The system should support recent versions of:

* Google Chrome
* Mozilla Firefox
* Microsoft Edge
* Safari

## NFR-047: Responsive Design

The interface shall adapt to desktop, tablet, and mobile screen sizes.

## NFR-048: API Format

The backend API shall exchange data using JSON.

## NFR-049: Standard Web Protocols

The system shall use standard HTTP methods and status codes.

---

# 10. Scalability Requirements

## NFR-050: User Growth

The system architecture should allow future increases in the number of students, courses, sections, and departments.

## NFR-051: Database Growth

The database shall support increasing volumes of registration and waiting-list records without redesigning the main data model.

## NFR-052: Horizontal Expansion

The backend architecture should allow future deployment across multiple application instances.

## NFR-053: Search Scalability

Frequently searched database fields should support indexing.

---

# 11. Maintainability Requirements

## NFR-054: Modular Architecture

The system shall separate frontend, backend, database, and business-logic responsibilities.

## NFR-055: Code Readability

Source code shall use meaningful names and consistent formatting.

## NFR-056: Documentation

The project shall include:

* Setup instructions
* API documentation
* Database documentation
* Requirement documents
* Technical design documents

## NFR-057: Version Control

All source code and documentation shall be managed using Git and GitHub.

## NFR-058: Issue Tracking

Development tasks and defects shall be tracked using GitHub Issues.

## NFR-059: Configuration Management

Environment-specific values shall be stored in configuration or environment files rather than hard-coded.

## NFR-060: Dependency Management

Frontend and backend dependencies shall be recorded in their respective dependency files.

---

# 12. Testability Requirements

## NFR-061: Unit Testing

Core business rules should be covered by automated unit tests.

## NFR-062: API Testing

Critical API endpoints should have automated tests.

## NFR-063: Registration Validation Testing

Tests shall cover:

* Prerequisite validation
* Credit limits
* Schedule conflicts
* Seat capacity
* Waiting-list order

## NFR-064: Error Testing

The system shall be tested for invalid input and unauthorized access.

## NFR-065: Repeatable Tests

Automated tests should produce consistent results in the same environment.

---

# 13. Data Integrity Requirements

## NFR-066: Unique Registration

The database shall prevent duplicate registration records for the same student and course section.

## NFR-067: Unique Waiting-List Entry

The database shall prevent duplicate waiting-list entries for the same student and course section.

## NFR-068: Valid Seat Capacity

Section capacity shall always be a positive integer.

## NFR-069: Enrollment Limit

The number of approved registrations shall not exceed the section capacity.

## NFR-070: Referential Integrity

Related records shall be protected using foreign-key constraints.

## NFR-071: Valid Schedule Time

A class end time shall be later than its start time.

## NFR-072: Valid Registration Status

Registration status values shall be limited to approved system-defined values.

---

# 14. Backup and Recovery Requirements

## NFR-073: Regular Backup

The system should create regular backups of registration and academic data.

## NFR-074: Backup Protection

Backups shall be stored securely.

## NFR-075: Data Restoration

Authorized administrators should be able to restore the database from a valid backup.

## NFR-076: Recovery Verification

Backup restoration procedures should be tested periodically.

---

# 15. Logging and Audit Requirements

## NFR-077: Error Logging

The system shall record backend errors with timestamps.

## NFR-078: Registration Audit Log

The system shall record important registration actions, including:

* Final submission
* Approval
* Rejection
* Course drop
* Waiting-list promotion

## NFR-079: Administrative Audit Log

The system shall record important administrative actions, including:

* Course creation
* Section creation
* Capacity changes
* Prerequisite changes
* Role changes

## NFR-080: Log Protection

Normal users shall not be able to modify audit logs.

---

# 16. Deployment Requirements

## NFR-081: Environment Separation

The system should support separate development, testing, and production environments.

## NFR-082: Environment Variables

Database credentials, secret keys, and deployment settings shall be managed using environment variables.

## NFR-083: Container Support

The application should support containerized deployment using Docker.

## NFR-084: API Documentation

FastAPI shall provide interactive OpenAPI documentation for authorized development use.

---

# 17. Non-Functional Requirement Summary

CoursePilot's non-functional requirements focus on:

* Performance
* Availability
* Reliability
* Security
* Privacy
* Usability
* Accessibility
* Compatibility
* Scalability
* Maintainability
* Testability
* Data integrity
* Backup and recovery
* Logging and auditing
* Deployment readiness

## 18. Conclusion

These non-functional requirements define the expected quality and operational standards of CoursePilot.

They will guide the system architecture, database design, API implementation, interface design, deployment, and testing activities.
