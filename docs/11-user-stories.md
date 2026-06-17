# CoursePilot User Stories

## 1. Introduction

User stories describe CoursePilot features from the perspective of the people who will use the system.

Each story follows this structure:

> As a [user role], I want [goal], so that [benefit].

The stories are grouped by user type and assigned unique identifiers for later use in the acceptance criteria, functional requirements, use cases, and test cases.

---

# 2. Student User Stories

## Authentication and Dashboard

### US-001: Student Login

**As a student,**
I want to log in using my university account,
**so that** I can securely access course-registration features.

### US-002: View Student Dashboard

**As a student,**
I want to view a dashboard after login,
**so that** I can quickly access registration, waitlist, status, and schedule information.

### US-003: View Registration Period

**As a student,**
I want to see whether the registration period is open or closed,
**so that** I know whether I can submit a course-registration request.

---

## Course Browsing

### US-004: Browse Available Courses

**As a student,**
I want to browse available courses and sections,
**so that** I can identify suitable courses for the trimester.

### US-005: Search Courses

**As a student,**
I want to search courses by course code or title,
**so that** I can find a specific course quickly.

### US-006: Filter Courses

**As a student,**
I want to filter courses by department, trimester, availability, and course type,
**so that** I can reduce the number of displayed results.

### US-007: View Course Details

**As a student,**
I want to view complete course and section details,
**so that** I can make an informed registration decision.

Course details should include:

* Course code
* Course title
* Credit value
* Section
* Instructor
* Class day and time
* Room number
* Seat capacity
* Available seats
* Prerequisites
* Mandatory or elective status

### US-008: View Real-Time Seat Availability

**As a student,**
I want to see the current number of available seats,
**so that** I know whether direct registration is possible.

### US-009: View Mandatory-Course Label

**As a student,**
I want mandatory courses to be clearly labelled,
**so that** I do not miss a required course.

---

## Course Selection and Validation

### US-010: Select a Course Section

**As a student,**
I want to select a course section,
**so that** I can include it in my registration plan.

### US-011: View Selected Courses

**As a student,**
I want to see all currently selected courses in one place,
**so that** I can review my planned registration.

### US-012: View Selected Course Times While Browsing

**As a student,**
I want to see the schedules of my selected courses while browsing additional sections,
**so that** I do not have to remember or write down class times.

### US-013: Check Prerequisite Eligibility

**As a student,**
I want the system to check course prerequisites automatically,
**so that** I do not select a course for which I am not eligible.

### US-014: View Missing Prerequisite

**As a student,**
I want the system to show which prerequisite is missing,
**so that** I understand why registration is blocked.

### US-015: Prevent Duplicate Course Selection

**As a student,**
I want the system to prevent duplicate course registration,
**so that** I do not register for the same course more than once.

### US-016: Prevent Registration for Completed Courses

**As a student,**
I want the system to warn or block me from selecting a course I have already passed,
**so that** I avoid an unnecessary registration.

### US-017: View Selected Credit Total

**As a student,**
I want the selected-credit total to update instantly,
**so that** I can monitor my semester credit load.

### US-018: Validate Minimum Credit Requirement

**As a student,**
I want the system to check the minimum credit requirement,
**so that** I do not submit an incomplete registration.

### US-019: Validate Maximum Credit Limit

**As a student,**
I want the system to check the maximum credit limit,
**so that** I do not register for more credits than permitted.

### US-020: Detect Schedule Conflicts

**As a student,**
I want the system to detect overlapping class schedules,
**so that** I do not register for courses that occur at the same time.

### US-021: View Conflict Details

**As a student,**
I want the conflict message to show the affected courses, sections, days, and times,
**so that** I can choose another suitable section.

### US-022: Block Conflicting Final Submission

**As a student,**
I want the system to block final submission when schedule conflicts exist,
**so that** I cannot create an invalid class schedule.

---

## Seat and Waiting-List Management

### US-023: Verify Seat During Confirmation

**As a student,**
I want seat availability to be checked again during registration confirmation,
**so that** I do not receive outdated seat information.

### US-024: Join a Waiting List

**As a student,**
I want to join a waiting list when a course section is full,
**so that** I may receive a seat later.

### US-025: View Waiting-List Position

**As a student,**
I want to view my current waiting-list position,
**so that** I can estimate the possibility of receiving a seat.

### US-026: View Waiting-List Details

**As a student,**
I want to see the course, section, queue position, and status of each waitlisted course,
**so that** I can monitor my waiting-list requests.

### US-027: Leave a Waiting List

**As a student,**
I want to leave a waiting list,
**so that** I can withdraw my request if I no longer need the course.

### US-028: Receive Waiting-List Status Update

**As a student,**
I want to be notified when my waiting-list status changes,
**so that** I can respond when a seat becomes available.

---

## Final Submission and Status

### US-029: Review Registration Summary

**As a student,**
I want to review all selected courses before final submission,
**so that** I can identify mistakes before confirming.

### US-030: Submit Final Registration

**As a student,**
I want to submit my final registration request,
**so that** it can be reviewed and approved.

### US-031: View Validation Errors

**As a student,**
I want clear validation messages when submission is blocked,
**so that** I know what must be corrected.

### US-032: Track Registration Status

**As a student,**
I want to view whether each registration is pending, approved, rejected, waitlisted, or dropped,
**so that** I can monitor the outcome.

### US-033: View Rejection Reason

**As a student,**
I want to see the reason when a registration request is rejected,
**so that** I understand the advisor's decision.

### US-034: Drop a Course

**As a student,**
I want to drop an eligible course before the deadline,
**so that** I can update my registration plan.

---

## Class Schedule

### US-035: View Registered Courses

**As a student,**
I want to view all approved courses,
**so that** I know which courses I am officially registered for.

### US-036: View Complete Schedule Information

**As a student,**
I want the schedule to display course code, title, section, instructor, time, room, credit, and status,
**so that** I have all class information in one place.

### US-037: View Weekly Timetable

**As a student,**
I want to view approved courses in a weekly timetable,
**so that** I can understand my class schedule easily.

---

# 3. Academic Advisor User Stories

### US-038: Advisor Login

**As an academic advisor,**
I want to log in securely,
**so that** I can access assigned student registration requests.

### US-039: View Pending Requests

**As an academic advisor,**
I want to view pending registration requests,
**so that** I can review them efficiently.

### US-040: View Student Registration Details

**As an academic advisor,**
I want to view the student's selected courses, credit total, prerequisites, and conflicts,
**so that** I can make an informed decision.

### US-041: Approve Registration

**As an academic advisor,**
I want to approve a valid registration request,
**so that** the student can complete enrollment.

### US-042: Reject Registration

**As an academic advisor,**
I want to reject an invalid registration request,
**so that** academic rules are maintained.

### US-043: Add Advisor Comments

**As an academic advisor,**
I want to add comments to a registration decision,
**so that** the student understands the reason or required action.

### US-044: View Decision History

**As an academic advisor,**
I want to view previous registration decisions,
**so that** I can review earlier advising actions.

---

# 4. Department Administrator User Stories

### US-045: Create a Course

**As a department administrator,**
I want to create a course record,
**so that** it can be offered during registration.

### US-046: Update Course Information

**As a department administrator,**
I want to update course details,
**so that** students see accurate information.

### US-047: Create Course Sections

**As a department administrator,**
I want to create one or more sections for a course,
**so that** students can select suitable class times.

### US-048: Set Section Capacity

**As a department administrator,**
I want to define the seat capacity for each section,
**so that** enrollment does not exceed the allowed limit.

### US-049: Assign Instructor

**As a department administrator,**
I want to assign an instructor to a course section,
**so that** students can see who will teach the course.

### US-050: Assign Room and Schedule

**As a department administrator,**
I want to assign a room, day, and time to each section,
**so that** the class schedule is complete.

### US-051: Define Course Prerequisites

**As a department administrator,**
I want to define course prerequisites,
**so that** eligibility can be checked automatically.

### US-052: Mark Mandatory Courses

**As a department administrator,**
I want to mark courses as mandatory or elective,
**so that** students can identify degree requirements.

### US-053: Manage Registration Period

**As a department administrator,**
I want to open and close registration periods,
**so that** submissions occur only within the allowed dates.

### US-054: Monitor Section Enrollment

**As a department administrator,**
I want to monitor enrolled and available seats,
**so that** I can identify full or high-demand sections.

### US-055: Monitor Waiting Lists

**As a department administrator,**
I want to view waiting-list queues,
**so that** I can manage seat demand fairly.

### US-056: Increase Section Capacity

**As a department administrator,**
I want to update section capacity when permitted,
**so that** additional students may be accommodated.

---

# 5. System Administrator User Stories

### US-057: Manage User Accounts

**As a system administrator,**
I want to create, update, activate, or deactivate user accounts,
**so that** system access remains controlled.

### US-058: Assign User Roles

**As a system administrator,**
I want to assign roles to users,
**so that** each user receives the correct permissions.

### US-059: Enforce Role-Based Access

**As a system administrator,**
I want the system to restrict features by role,
**so that** users cannot access unauthorized functions.

### US-060: View System Logs

**As a system administrator,**
I want to view system and activity logs,
**so that** I can investigate errors and unusual activity.

### US-061: Maintain System Availability

**As a system administrator,**
I want to monitor system performance and availability,
**so that** the platform remains usable during registration periods.

### US-062: Manage Backups

**As a system administrator,**
I want to create and restore system backups,
**so that** important registration data is protected.

---

# 6. User Story Prioritization

The following priority levels are used:

* **Must Have:** Essential for the first working version
* **Should Have:** Important but can follow the core implementation
* **Could Have:** Useful enhancement
* **Won't Have Now:** Outside the initial scope

## 6.1 Must-Have Stories

| Story ID | User Story                      |
| -------- | ------------------------------- |
| US-001   | Student login                   |
| US-004   | Browse available courses        |
| US-007   | View course details             |
| US-008   | View seat availability          |
| US-010   | Select course section           |
| US-013   | Check prerequisite eligibility  |
| US-017   | View selected-credit total      |
| US-018   | Validate minimum credits        |
| US-019   | Validate maximum credits        |
| US-020   | Detect schedule conflicts       |
| US-022   | Block conflicting submission    |
| US-023   | Verify seat during confirmation |
| US-024   | Join waiting list               |
| US-025   | View waiting-list position      |
| US-029   | Review registration summary     |
| US-030   | Submit final registration       |
| US-032   | Track registration status       |
| US-035   | View registered courses         |
| US-039   | View pending advisor requests   |
| US-041   | Approve registration            |
| US-042   | Reject registration             |
| US-045   | Create course                   |
| US-047   | Create course section           |
| US-048   | Set section capacity            |
| US-050   | Assign room and schedule        |
| US-051   | Define prerequisites            |
| US-057   | Manage user accounts            |
| US-058   | Assign user roles               |

## 6.2 Should-Have Stories

| Story ID | User Story                            |
| -------- | ------------------------------------- |
| US-005   | Search courses                        |
| US-006   | Filter courses                        |
| US-009   | View mandatory-course label           |
| US-012   | View selected schedule while browsing |
| US-014   | View missing prerequisite             |
| US-021   | View conflict details                 |
| US-026   | View waiting-list details             |
| US-028   | Receive waiting-list updates          |
| US-031   | View validation errors                |
| US-033   | View rejection reason                 |
| US-036   | View complete schedule information    |
| US-043   | Add advisor comments                  |
| US-054   | Monitor section enrollment            |
| US-055   | Monitor waiting lists                 |

## 6.3 Could-Have Stories

| Story ID | User Story                    |
| -------- | ----------------------------- |
| US-027   | Leave waiting list            |
| US-034   | Drop course                   |
| US-037   | View weekly timetable         |
| US-044   | View advisor decision history |
| US-056   | Increase section capacity     |
| US-060   | View system logs              |
| US-062   | Manage backups                |

---

# 7. User Story Dependencies

| User Story                        | Depends On                                     |
| --------------------------------- | ---------------------------------------------- |
| US-010 Select course section      | US-004, US-007                                 |
| US-013 Prerequisite checking      | Student academic records and prerequisite data |
| US-020 Conflict detection         | Course schedule and selected-course data       |
| US-024 Join waiting list          | Section must be full                           |
| US-025 View waiting-list position | US-024                                         |
| US-030 Final submission           | US-013, US-018, US-019, US-020, US-023         |
| US-032 Track status               | US-030                                         |
| US-035 View registered courses    | US-041                                         |
| US-041 Advisor approval           | US-039, US-040                                 |
| US-047 Create course section      | US-045                                         |
| US-050 Assign room and schedule   | US-047                                         |
| US-055 Monitor waiting lists      | US-024                                         |

---

# 8. Conclusion

The user stories define the expected CoursePilot behavior from the perspective of students, academic advisors, department administrators, and system administrators.

These stories will be used to create measurable acceptance criteria and will later be mapped to functional requirements, use cases, APIs, database entities, and test cases.
