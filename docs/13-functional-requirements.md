# CoursePilot Functional Requirements

## 1. Introduction

Functional requirements describe the specific actions and services that CoursePilot must provide.

Each requirement is assigned a unique identifier using the following format:

```text
FR-XXX
```

These identifiers will be used later in the Software Requirements Specification, use cases, API design, test cases, and traceability matrix.

---

# 2. Authentication and Authorization Requirements

## FR-001: User Login

The system shall allow registered users to log in using valid university credentials.

## FR-002: Invalid Login Handling

The system shall reject invalid login attempts and display an appropriate error message.

## FR-003: User Logout

The system shall allow authenticated users to log out securely.

## FR-004: Role-Based Access

The system shall provide different access permissions for:

* Students
* Academic advisors
* Department administrators
* System administrators

## FR-005: Unauthorized Access Prevention

The system shall prevent users from accessing pages or functions that are not permitted for their assigned roles.

---

# 3. Student Dashboard Requirements

## FR-006: Student Dashboard

The system shall provide a dashboard for authenticated students.

## FR-007: Registration-Period Status

The student dashboard shall display whether the course-registration period is open or closed.

## FR-008: Registration Summary

The student dashboard shall display a summary of:

* Selected courses
* Pending registrations
* Approved registrations
* Rejected registrations
* Waitlisted courses
* Total selected credits

---

# 4. Course Browsing Requirements

## FR-009: View Courses

The system shall allow students to view available courses and course sections.

## FR-010: Search Courses

The system shall allow students to search courses by:

* Course code
* Course title

## FR-011: Filter Courses

The system shall allow students to filter course sections by:

* Department
* Trimester
* Course level
* Seat availability
* Mandatory or elective status

## FR-012: View Course Details

The system shall display the following information for each course section:

* Course code
* Course title
* Course description
* Credit value
* Section number
* Instructor
* Class day
* Start time
* End time
* Room number
* Total seat capacity
* Available seats
* Prerequisites
* Mandatory or elective status

## FR-013: Display Mandatory Courses

The system shall clearly identify courses that are mandatory for the student's academic program.

---

# 5. Seat Availability Requirements

## FR-014: Display Available Seats

The system shall display the current number of available seats for every course section.

## FR-015: Automatic Seat Update

The system shall update available-seat information when enrollment changes.

## FR-016: Seat Revalidation

The system shall recheck seat availability when a student confirms registration.

## FR-017: Prevent Over-Enrollment

The system shall prevent the number of approved students from exceeding the configured section capacity.

## FR-018: Full-Section Notification

The system shall inform the student when a course section is full.

---

# 6. Course Selection Requirements

## FR-019: Select Course Section

The system shall allow a student to select an eligible course section.

## FR-020: View Selected Courses

The system shall display all currently selected courses in one place.

## FR-021: Remove Selected Course

The system shall allow the student to remove a course before final submission.

## FR-022: Prevent Duplicate Selection

The system shall prevent a student from selecting the same course or section more than once.

## FR-023: Completed-Course Validation

The system shall prevent a student from registering for a previously passed course unless retake permission exists.

## FR-024: Show Selected Schedule While Browsing

The system shall display the student's selected course schedules while the student browses additional course sections.

---

# 7. Prerequisite Requirements

## FR-025: Display Prerequisites

The system shall display all prerequisite requirements before a student selects a course.

## FR-026: Check Prerequisite Completion

The system shall check the student's completed-course records against the selected course prerequisites.

## FR-027: Block Missing Prerequisites

The system shall block course selection when the student has not completed all required prerequisites.

## FR-028: Display Missing Prerequisite

The system shall display the code and title of each missing prerequisite.

---

# 8. Credit Validation Requirements

## FR-029: Calculate Selected Credits

The system shall calculate the total credits of all selected courses.

## FR-030: Instant Credit Update

The system shall update the selected-credit total whenever the student adds or removes a course.

## FR-031: Display Credit Limits

The system shall display:

* Current selected credits
* Minimum required credits
* Maximum allowed credits

## FR-032: Minimum Credit Validation

The system shall block final submission when the selected-credit total is below the configured minimum.

## FR-033: Maximum Credit Validation

The system shall block final submission when the selected-credit total exceeds the configured maximum.

## FR-034: Credit Validation Message

The system shall display a clear error message when the student's credit total violates a configured limit.

---

# 9. Schedule-Conflict Requirements

## FR-035: Detect Schedule Conflicts

The system shall detect overlapping class schedules among selected and already registered course sections.

## FR-036: Conflict-Detection Condition

The system shall identify a schedule conflict when two sections:

* Occur on the same day
* Have overlapping start and end times

## FR-037: Display Conflict Details

The system shall display:

* Both course codes
* Both course titles
* Both section numbers
* Class day
* Start and end times

## FR-038: Block Conflicting Selection

The system shall prevent a student from adding a course section that conflicts with an already selected or approved course.

## FR-039: Block Conflicting Final Submission

The system shall block final registration submission when any schedule conflict exists.

## FR-040: Suggest Alternative Action

The system shall instruct the student to remove one of the conflicting courses or choose another section.

---

# 10. Waiting-List Requirements

## FR-041: Join Waiting List

The system shall allow an eligible student to join a waiting list when a course section is full.

## FR-042: Waiting-List Eligibility

Before adding a student to the waiting list, the system shall verify:

* Prerequisites
* Schedule conflicts
* Duplicate registration
* Registration-period status

## FR-043: Waiting-List Order

The system shall order waiting-list entries according to the date and time they were created.

## FR-044: Display Waiting-List Position

The system shall display the student's current waiting-list position.

## FR-045: Display Waiting-List Details

The system shall display:

* Course code
* Course title
* Section
* Queue position
* Total students waiting
* Waiting-list status

## FR-046: Prevent Duplicate Waiting-List Entry

The system shall prevent a student from joining the same section's waiting list more than once.

## FR-047: Leave Waiting List

The system shall allow a student to leave a waiting list before promotion.

## FR-048: Update Waiting-List Positions

The system shall automatically update waiting-list positions when a student joins, leaves, or is promoted.

## FR-049: Waiting-List Promotion

When a seat becomes available, the system shall identify the first eligible student in the waiting list.

## FR-050: Waiting-List Status Update

The system shall update the promoted student's status to Pending or Approved according to the configured institutional policy.

---

# 11. Final Registration Submission Requirements

## FR-051: View Registration Summary

The system shall allow students to review all selected courses before final submission.

## FR-052: Perform Final Validation

When the student clicks Final Submit, the system shall validate:

* Registration-period status
* Prerequisites
* Credit limits
* Schedule conflicts
* Duplicate courses
* Completed-course restrictions
* Seat availability

## FR-053: Successful Submission

If all validation rules pass, the system shall submit the registration request.

## FR-054: Pending Status

The system shall assign Pending status to a successfully submitted registration request that requires advisor approval.

## FR-055: Block Invalid Submission

The system shall block final submission when one or more validation rules fail.

## FR-056: Display Validation Errors

The system shall display specific validation errors and identify the affected courses.

## FR-057: Closed Registration Period

The system shall block registration submission when the registration period is closed.

---

# 12. Registration Status Requirements

## FR-058: Display Registration Status

The system shall display one of the following statuses for each registration:

* Draft
* Pending
* Approved
* Rejected
* Waitlisted
* Dropped

## FR-059: View Rejection Reason

The system shall display the rejection reason or advisor comment for a rejected request.

## FR-060: Registration History

The system shall maintain a history of registration decisions and status changes.

## FR-061: Drop Course

The system shall allow students to drop an eligible course before the configured deadline.

---

# 13. Academic Advisor Requirements

## FR-062: Advisor Login

The system shall allow academic advisors to log in securely.

## FR-063: View Assigned Students

The system shall allow advisors to view students assigned to them.

## FR-064: View Pending Requests

The system shall allow advisors to view pending registration requests.

## FR-065: View Student Registration Details

The system shall display:

* Student ID
* Student name
* Selected courses
* Total selected credits
* Prerequisite results
* Schedule-conflict results
* Waiting-list information

## FR-066: Approve Registration

The system shall allow an advisor to approve a valid registration request.

## FR-067: Reject Registration

The system shall allow an advisor to reject an invalid registration request.

## FR-068: Require Rejection Reason

The system shall require the advisor to provide a reason when rejecting a request.

## FR-069: Add Advisor Comment

The system shall allow advisors to add comments to registration decisions.

## FR-070: View Decision History

The system shall allow advisors to view previous registration decisions.

---

# 14. Department Administrator Requirements

## FR-071: Create Course

The system shall allow department administrators to create course records.

## FR-072: Update Course

The system shall allow department administrators to update course information.

## FR-073: Create Course Section

The system shall allow department administrators to create sections for existing courses.

## FR-074: Update Course Section

The system shall allow department administrators to update section information.

## FR-075: Set Seat Capacity

The system shall allow department administrators to define the seat capacity for each section.

## FR-076: Assign Instructor

The system shall allow department administrators to assign an instructor to each course section.

## FR-077: Assign Room

The system shall allow department administrators to assign a room to each section.

## FR-078: Assign Class Schedule

The system shall allow department administrators to define:

* Class day
* Start time
* End time

## FR-079: Define Prerequisites

The system shall allow department administrators to define prerequisite relationships between courses.

## FR-080: Mark Mandatory Courses

The system shall allow department administrators to mark courses as mandatory or elective.

## FR-081: Manage Registration Period

The system shall allow authorized administrators to open and close registration periods.

## FR-082: Monitor Enrollment

The system shall allow department administrators to view:

* Section capacity
* Enrolled students
* Available seats
* Waiting-list size

## FR-083: Change Section Capacity

The system shall allow authorized administrators to increase or decrease section capacity when permitted.

## FR-084: Monitor Waiting Lists

The system shall allow department administrators to view waiting-list entries and queue order.

---

# 15. Student Schedule Requirements

## FR-085: View Approved Courses

The system shall allow students to view all approved courses.

## FR-086: Display Schedule Details

The system shall display:

* Course code
* Course title
* Section
* Instructor
* Class day
* Start time
* End time
* Room number
* Credit value
* Registration status

## FR-087: Weekly Timetable View

The system shall display approved courses in a weekly timetable format.

## FR-088: List View

The system shall allow students to view approved courses in a list format.

---

# 16. Notification Requirements

## FR-089: Registration Status Notification

The system shall notify students when a registration status changes.

## FR-090: Waiting-List Notification

The system shall notify students when their waiting-list position or status changes.

## FR-091: Advisor Decision Notification

The system shall notify students when an advisor approves or rejects a request.

---

# 17. System Administration Requirements

## FR-092: Manage User Accounts

The system shall allow system administrators to:

* Create users
* Update users
* Activate users
* Deactivate users

## FR-093: Assign Roles

The system shall allow system administrators to assign user roles.

## FR-094: Manage Permissions

The system shall enforce permissions according to assigned user roles.

## FR-095: View Activity Logs

The system shall record and display important user and system activities.

## FR-096: Maintain Audit Trail

The system shall maintain an audit trail of:

* Registration submissions
* Advisor decisions
* Capacity changes
* Waiting-list promotions
* User-role changes

---

# 18. Error-Handling Requirements

## FR-097: Clear Error Messages

The system shall display understandable error messages when an operation fails.

## FR-098: Standard Error Response

The backend API shall return standardized error responses.

## FR-099: Preserve User Selection

When possible, the system shall preserve the student's selected courses after a validation error.

## FR-100: Prevent Partial Registration

The system shall ensure that failed registration operations do not leave incomplete or inconsistent records.

---

# 19. Functional Requirement Summary

The CoursePilot functional requirements cover:

* Authentication
* Role-based access
* Course browsing
* Real-time seat availability
* Course selection
* Prerequisite validation
* Credit validation
* Schedule-conflict detection
* Waiting-list management
* Final registration submission
* Advisor approval
* Course and section administration
* Registration-status tracking
* Student schedules
* Notifications
* Audit logging
* Error handling

## 20. Conclusion

These functional requirements define the main services and behaviors that CoursePilot must provide.

They will be used in the use cases, SRS, system design, database design, API design, and future test cases.
