# CoursePilot Acceptance Criteria

## 1. Introduction

Acceptance criteria define the conditions that must be satisfied for each major CoursePilot feature to be considered complete and acceptable.

The criteria are written using the following format:

* **Given** — the initial condition
* **When** — the user action
* **Then** — the expected system response

---

## 2. Student Authentication

### AC-001: Successful Student Login

**Related User Story:** US-001

**Given** the student has a valid university account,
**When** the student enters the correct username and password,
**Then** the system shall authenticate the student and open the student dashboard.

### AC-002: Invalid Login

**Related User Story:** US-001

**Given** the student enters an incorrect username or password,
**When** the student submits the login form,
**Then** the system shall deny access and display a clear error message.

---

## 3. Course Browsing

### AC-003: View Available Courses

**Related User Story:** US-004

**Given** the student is logged in and the registration period is active,
**When** the student opens the course-registration page,
**Then** the system shall display the available courses and sections.

### AC-004: Search for a Course

**Related User Story:** US-005

**Given** courses exist in the system,
**When** the student searches using a course code or title,
**Then** the system shall display matching course results.

### AC-005: View Course Details

**Related User Story:** US-007

**Given** the student selects a course section,
**When** the course-details page opens,
**Then** the system shall display:

* Course code
* Course title
* Credit value
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

## 4. Seat Availability

### AC-006: Display Available Seats

**Related User Story:** US-008

**Given** a course section has a fixed seat capacity,
**When** the student views the course section,
**Then** the system shall display the current number of available seats.

### AC-007: Recheck Seat During Confirmation

**Related User Story:** US-023

**Given** the student has selected a section with available seats,
**When** the student confirms registration,
**Then** the system shall check seat availability again before reserving the seat.

### AC-008: Prevent Over-Enrollment

**Related User Story:** US-023

**Given** a course section has reached its maximum capacity,
**When** another student attempts direct registration,
**Then** the system shall prevent enrollment and offer the waiting-list option.

---

## 5. Prerequisite Validation

### AC-009: Successful Prerequisite Validation

**Related User Story:** US-013

**Given** the student has completed all required prerequisites,
**When** the student selects the course,
**Then** the system shall allow the student to continue registration.

### AC-010: Missing Prerequisite

**Related User Stories:** US-013, US-014

**Given** the student has not completed a required prerequisite,
**When** the student attempts to select the course,
**Then** the system shall block the selection and display the missing prerequisite course code and title.

### AC-011: Display Prerequisite Before Selection

**Related User Story:** US-007

**Given** a course has one or more prerequisites,
**When** the student views the course details,
**Then** the prerequisite information shall be visible before registration.

---

## 6. Credit Validation

### AC-012: Instant Credit Calculation

**Related User Story:** US-017

**Given** the student adds or removes a course,
**When** the selected-course list changes,
**Then** the system shall immediately update the total selected credits.

### AC-013: Minimum Credit Requirement

**Related User Story:** US-018

**Given** the selected credit total is below the configured minimum,
**When** the student clicks Final Submit,
**Then** the system shall block submission and display the minimum-credit requirement.

### AC-014: Maximum Credit Requirement

**Related User Story:** US-019

**Given** the selected credit total exceeds the configured maximum,
**When** the student clicks Final Submit,
**Then** the system shall block submission and display the maximum-credit limit.

### AC-015: Valid Credit Range

**Related User Stories:** US-018, US-019

**Given** the student's selected credits satisfy both the minimum and maximum limits,
**When** final validation is performed,
**Then** the credit validation shall pass.

---

## 7. Schedule-Conflict Detection

### AC-016: Detect Overlapping Courses

**Related User Story:** US-020

**Given** the student has already selected a course,
**When** the student selects another section with an overlapping day and time,
**Then** the system shall detect the schedule conflict.

### AC-017: Display Conflict Details

**Related User Story:** US-021

**Given** a schedule conflict is detected,
**When** the system displays the validation error,
**Then** it shall show:

* Both course codes
* Both section numbers
* Class day
* Start time
* End time

### AC-018: Block Final Submission for Conflict

**Related User Story:** US-022

**Given** two selected courses have overlapping schedules,
**When** the student clicks Final Submit,
**Then** the system shall block final submission.

### AC-019: Successful Conflict Validation

**Related User Story:** US-020

**Given** none of the selected courses overlap,
**When** the system checks the schedules,
**Then** the student shall be allowed to continue registration.

### AC-020: Show Selected Schedule While Browsing

**Related User Story:** US-012

**Given** the student has already selected one or more courses,
**When** the student browses additional course sections,
**Then** the system shall display the schedules of the already selected courses.

---

## 8. Waiting-List Management

### AC-021: Join Waiting List

**Related User Story:** US-024

**Given** a section is full and the student satisfies all eligibility rules,
**When** the student clicks Join Waiting List,
**Then** the system shall add the student to the waiting list.

### AC-022: Waiting-List Position

**Related User Story:** US-025

**Given** the student has joined a waiting list,
**When** the student views the waiting-list page,
**Then** the system shall display the student's current queue position.

### AC-023: First-Come, First-Served Order

**Related User Story:** US-025

**Given** several students join the same waiting list,
**When** their positions are calculated,
**Then** the system shall order them according to the date and time they joined.

### AC-024: Prevent Duplicate Waiting-List Entry

**Related User Story:** US-024

**Given** the student is already on the waiting list for a section,
**When** the student attempts to join the same waiting list again,
**Then** the system shall reject the duplicate request.

### AC-025: Leave Waiting List

**Related User Story:** US-027

**Given** the student is currently on a waiting list,
**When** the student selects Leave Waiting List,
**Then** the system shall remove the student and update the positions of the remaining students.

### AC-026: Promote Eligible Student

**Related User Story:** US-028

**Given** a seat becomes available,
**When** the waiting list is processed,
**Then** the first eligible student shall be moved to Pending Approval or Approved status according to the configured policy.

---

## 9. Course Registration Submission

### AC-027: Review Registration Summary

**Related User Story:** US-029

**Given** the student has selected courses,
**When** the student opens the registration summary,
**Then** the system shall display all selected courses, credits, schedules, prerequisites, and validation results.

### AC-028: Successful Final Submission

**Related User Story:** US-030

**Given** all prerequisites, credits, schedules, seat availability, and registration-period rules are valid,
**When** the student clicks Final Submit,
**Then** the system shall submit the registration request and assign Pending status.

### AC-029: Validation Error Message

**Related User Story:** US-031

**Given** one or more validation rules fail,
**When** the student attempts final submission,
**Then** the system shall block submission and display specific errors.

### AC-030: Registration Period Closed

**Related User Story:** US-003

**Given** the registration period is closed,
**When** the student attempts to submit registration,
**Then** the system shall block submission and display a registration-closed message.

---

## 10. Registration Status

### AC-031: View Registration Status

**Related User Story:** US-032

**Given** the student has submitted a registration request,
**When** the student opens the registration-status page,
**Then** the system shall display one of the following statuses:

* Draft
* Pending
* Approved
* Rejected
* Waitlisted
* Dropped

### AC-032: View Rejection Reason

**Related User Story:** US-033

**Given** an advisor rejects a registration request,
**When** the student views the rejected request,
**Then** the system shall display the rejection reason or advisor comment.

---

## 11. Student Schedule

### AC-033: View Approved Courses

**Related User Story:** US-035

**Given** one or more registration requests have been approved,
**When** the student opens the registered-course page,
**Then** the system shall display all approved courses.

### AC-034: Complete Schedule Information

**Related User Story:** US-036

**Given** an approved course exists,
**When** the student views the schedule,
**Then** the system shall display:

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

### AC-035: Weekly Timetable

**Related User Story:** US-037

**Given** the student has approved courses,
**When** the student selects the weekly timetable view,
**Then** the system shall display the courses according to their class days and times.

---

## 12. Academic Advisor Functions

### AC-036: View Pending Requests

**Related User Story:** US-039

**Given** the advisor is logged in,
**When** the advisor opens the registration-request page,
**Then** the system shall display the pending requests of assigned students.

### AC-037: View Student Registration Details

**Related User Story:** US-040

**Given** a pending request exists,
**When** the advisor opens it,
**Then** the system shall display:

* Student information
* Selected courses
* Total credits
* Prerequisite results
* Conflict results
* Waiting-list information

### AC-038: Approve Registration

**Related User Story:** US-041

**Given** the advisor determines that the request is valid,
**When** the advisor clicks Approve,
**Then** the system shall change the registration status to Approved.

### AC-039: Reject Registration

**Related User Story:** US-042

**Given** the advisor determines that the request is invalid,
**When** the advisor clicks Reject and provides a reason,
**Then** the system shall change the status to Rejected and save the reason.

### AC-040: Add Advisor Comment

**Related User Story:** US-043

**Given** the advisor is reviewing a request,
**When** the advisor enters a comment,
**Then** the system shall save and display the comment with the decision.

---

## 13. Department Administrator Functions

### AC-041: Create Course

**Related User Story:** US-045

**Given** the department administrator is logged in,
**When** valid course information is submitted,
**Then** the system shall create a new course record.

### AC-042: Create Course Section

**Related User Story:** US-047

**Given** a course exists,
**When** the administrator enters valid section information,
**Then** the system shall create the course section.

### AC-043: Set Section Capacity

**Related User Story:** US-048

**Given** a section exists,
**When** the administrator sets a positive seat capacity,
**Then** the system shall save the capacity.

### AC-044: Assign Room and Schedule

**Related User Story:** US-050

**Given** a course section exists,
**When** the administrator assigns a room, day, start time, and end time,
**Then** the system shall save the schedule information.

### AC-045: Define Prerequisites

**Related User Story:** US-051

**Given** a course exists,
**When** the administrator selects one or more prerequisite courses,
**Then** the system shall save those prerequisite relationships.

### AC-046: Open or Close Registration

**Related User Story:** US-053

**Given** the administrator has permission to manage registration periods,
**When** the administrator changes the registration-period status,
**Then** the system shall allow or block student submissions accordingly.

---

## 14. System Administration

### AC-047: Assign User Role

**Related User Story:** US-058

**Given** a user account exists,
**When** the system administrator assigns a role,
**Then** the user shall receive permissions associated with that role.

### AC-048: Enforce Role-Based Access

**Related User Story:** US-059

**Given** a student attempts to access an administrator-only feature,
**When** the request is processed,
**Then** the system shall deny access.

### AC-049: Protect User Data

**Related User Story:** US-059

**Given** a user is authenticated,
**When** the user requests protected information,
**Then** the system shall return only information permitted for that user's role.

---

## 15. General Acceptance Conditions

The CoursePilot product will be accepted when:

1. Students can securely log in.
2. Courses and sections are visible and searchable.
3. Seat availability is displayed and revalidated.
4. Full sections support waiting-list enrollment.
5. Waiting-list positions are visible.
6. Prerequisites are checked automatically.
7. Missing prerequisites are clearly displayed.
8. Selected credits update instantly.
9. Minimum and maximum credit rules are enforced.
10. Schedule conflicts are detected.
11. Final submission is blocked when conflicts exist.
12. Registration requests receive clear statuses.
13. Advisors can approve or reject requests.
14. Rejected requests include reasons.
15. Approved courses appear in a complete student schedule.
16. Administrators can manage courses, sections, capacity, rooms, schedules, and prerequisites.
17. Role-based access is enforced.

## 16. Conclusion

These acceptance criteria provide measurable conditions for evaluating CoursePilot features.

They will be used later to prepare functional requirements, use cases, test cases, and the requirements traceability matrix.
