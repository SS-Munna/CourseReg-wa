# CoursePilot Product Requirement Document

## 1. Document Information

| Item              | Details                                            |
| ----------------- | -------------------------------------------------- |
| Product Name      | CoursePilot                                        |
| Document Type     | Product Requirement Document                       |
| Version           | 1.0                                                |
| Product Category  | Course Registration and Waitlist Management System |
| Intended Platform | Web Application                                    |
| Proposed Frontend | React                                              |
| Proposed Backend  | FastAPI                                            |
| Proposed Database | PostgreSQL                                         |

## 2. Product Overview

CoursePilot is a web-based course registration and waitlist management system designed for universities and academic institutions.

The platform will allow students to browse available course sections, view seat availability, register for eligible courses, join waiting lists, track registration status, and view approved class schedules.

The system will also validate prerequisites, minimum and maximum credit requirements, and schedule conflicts before allowing final submission.

Academic advisors will be able to review registration requests, while department administrators will manage courses, sections, schedules, rooms, seat capacities, instructors, and prerequisites.

## 3. Product Vision

The vision of CoursePilot is to provide a transparent, reliable, and user-friendly course registration experience.

The system should reduce registration errors, improve seat and waitlist visibility, provide clear academic validation, and decrease manual work for students, advisors, and department administrators.

## 4. Problem Summary

Students may experience several problems during course registration:

* Seat counts may become outdated without refreshing the page.
* A section may appear available but become full during confirmation.
* Full courses may require students to request manual seat increases.
* Waiting-list positions may not be available.
* Prerequisite requirements may not be clearly displayed.
* Mandatory courses may not be clearly labelled.
* Students may need to remember selected class times while browsing.
* Credit totals may not update instantly.
* Registration decisions may be difficult to track.
* Final schedules may not present all necessary information clearly.

CoursePilot is proposed to address these problems through automated validation and transparent registration workflows.

## 5. Product Goals

The main goals of CoursePilot are:

1. Allow students to register for courses through a single platform.
2. Display updated seat availability for every section.
3. Provide a structured waiting-list system.
4. Display each student's waiting-list position.
5. Check prerequisite completion before registration.
6. Clearly identify missing prerequisites.
7. Display mandatory-course information.
8. Calculate selected credits instantly.
9. Enforce minimum and maximum credit rules.
10. Detect schedule conflicts.
11. Block invalid final registration submissions.
12. Provide clear registration status information.
13. Allow advisors to approve or reject requests.
14. Provide students with a complete weekly class schedule.

## 6. Target Users

### 6.1 Students

Students will use CoursePilot to:

* Log in securely.
* Search for courses and sections.
* View course details.
* View current seat availability.
* Register for courses.
* Join waiting lists.
* View waiting-list positions.
* Check prerequisite eligibility.
* View selected-credit totals.
* Resolve schedule conflicts.
* Submit registrations.
* Track registration status.
* View approved class schedules.

### 6.2 Academic Advisors

Academic advisors will use CoursePilot to:

* View pending registration requests.
* Review student course selections.
* Check prerequisite eligibility.
* Check credit loads.
* Approve or reject requests.
* Add approval or rejection comments.
* View student registration history.

### 6.3 Department Administrators

Department administrators will use CoursePilot to:

* Create and update courses.
* Create course sections.
* Set section capacity.
* Assign instructors.
* Assign rooms.
* Define class schedules.
* Define prerequisites.
* Define mandatory courses.
* Open and close registration periods.
* Monitor registrations and waiting lists.

### 6.4 System Administrators

System administrators will:

* Manage user accounts.
* Assign user roles.
* Manage permissions.
* Monitor system activity.
* Maintain security and availability.

## 7. Product Scope

### 7.1 In Scope

The first version of CoursePilot will include:

* User authentication
* Role-based access
* Course catalogue
* Section listing
* Updated seat availability
* Course registration
* Prerequisite checking
* Mandatory-course labelling
* Minimum and maximum credit validation
* Schedule-conflict detection
* Final-submission blocking
* Waiting-list management
* Waiting-list position tracking
* Advisor approval and rejection
* Registration-status tracking
* Student class schedule
* Weekly timetable view
* Course, section, instructor, room, time, and credit information

### 7.2 Out of Scope

The first version will not include:

* Tuition payment
* Grade calculation
* Attendance management
* Examination management
* Learning-management-system features
* Complete university ERP integration
* Automated instructor workload calculation
* Mobile application development

## 8. Core Product Features

### 8.1 Authentication and Role Management

The system will provide secure login and role-based access for:

* Students
* Academic advisors
* Department administrators
* System administrators

### 8.2 Course and Section Browsing

Students will be able to:

* Search by course code or title.
* Filter by department or semester.
* View sections.
* View instructors.
* View schedules.
* View rooms.
* View credit values.
* View seat availability.
* View prerequisites.
* View mandatory-course labels.

### 8.3 Course Registration

Students will be able to select and request registration for eligible courses.

Before accepting the request, the system will check:

* Prerequisites
* Credit requirements
* Duplicate registration
* Completed-course restrictions
* Schedule conflicts
* Seat availability

### 8.4 Seat Management

Each section will have:

* Fixed seat capacity
* Current enrolled count
* Available-seat count

The system will verify seat availability again during confirmation to prevent outdated seat allocation.

### 8.5 Waiting-List Management

When a section is full:

* Students may join the waiting list.
* Waiting-list order will follow first-come, first-served.
* Students will see their current position.
* Positions will update when the queue changes.
* Eligible students may be promoted when seats become available.

### 8.6 Prerequisite Validation

The system will:

* Display required prerequisites.
* Check completed-course records.
* Identify missing prerequisites.
* Block invalid registration requests.
* Explain why registration is blocked.

### 8.7 Credit Validation

The system will:

* Show selected-credit totals instantly.
* Validate minimum credit requirements.
* Validate maximum credit limits.
* Block invalid final submission.
* Display a clear validation message.

### 8.8 Schedule-Conflict Detection

The system will compare selected and registered course schedules.

When a conflict exists:

* The system will identify the conflicting courses.
* It will display the course codes, sections, days, and times.
* It will block course selection or final submission.
* It will encourage the student to select another section.

### 8.9 Registration Approval

Academic advisors will be able to:

* View pending requests.
* Review academic eligibility.
* Approve requests.
* Reject requests.
* Add comments or rejection reasons.

### 8.10 Registration-Status Tracking

Students will be able to view statuses such as:

* Draft
* Pending
* Approved
* Rejected
* Waitlisted
* Dropped

### 8.11 Student Schedule

Approved courses will appear in a student schedule containing:

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

The system will also provide a weekly timetable view.

## 9. Business Rules

### BR-001: Seat Capacity

A student cannot be directly enrolled when the section capacity has been reached.

### BR-002: Waiting List

When a section is full, an eligible student may join the waiting list.

### BR-003: Waiting-List Order

Waiting-list order will follow the date and time of joining.

### BR-004: Prerequisites

A student cannot register for a course without completing all required prerequisites.

### BR-005: Credit Limit

Final submission must satisfy the configured minimum and maximum credit limits.

### BR-006: Schedule Conflict

A student cannot submit a registration containing overlapping class schedules.

### BR-007: Duplicate Registration

A student cannot register for the same course section more than once.

### BR-008: Completed Course

A student cannot normally register for a course already passed unless retake permission exists.

### BR-009: Advisor Approval

Registrations requiring academic approval remain pending until reviewed by an advisor.

### BR-010: Registration Period

Students can submit registration requests only during an active registration period.

## 10. User Flow

The main student flow is:

```text
Login
→ Browse courses
→ View course details
→ Select section
→ Check prerequisites
→ Check selected credits
→ Check schedule conflicts
→ Check seat availability
→ Register or join waitlist
→ Submit final registration
→ Wait for advisor decision
→ View status
→ View approved schedule
```

## 11. Product Assumptions

The product assumes that:

* Students already have university accounts.
* Student academic records are available.
* Completed-course information is accurate.
* Administrators define courses and sections before registration opens.
* Each section has a configured capacity.
* Registration periods are configured by administrators.
* Advisor assignments are available.
* Class schedules and room information are correct.

## 12. Product Constraints

CoursePilot may be affected by:

* Limited development time.
* Limited integration with existing university systems.
* Incomplete academic records.
* Different registration rules across departments.
* High user activity during registration periods.
* Changes to university academic policies.
* Limited survey and interview participants during initial analysis.

## 13. Success Criteria

CoursePilot will be considered successful when:

* Students can browse and register for courses.
* Seat availability is shown accurately.
* Full sections provide a waiting-list option.
* Waiting-list positions are visible.
* Missing prerequisites are clearly identified.
* Credit totals update immediately.
* Invalid credit loads are blocked.
* Schedule conflicts are detected and explained.
* Final submission is blocked when conflicts exist.
* Advisors can approve or reject requests.
* Students can track registration status.
* Approved courses appear in a complete weekly schedule.

## 14. Product Risks

| Risk                                 | Impact | Proposed Response                                       |
| ------------------------------------ | ------ | ------------------------------------------------------- |
| Two students attempt the final seat  | High   | Use database transactions and seat revalidation         |
| Waiting-list order becomes incorrect | High   | Use timestamp-based queue ordering                      |
| Incorrect prerequisite data          | High   | Allow administrators to verify and update prerequisites |
| High traffic during registration     | High   | Use efficient APIs and database indexes                 |
| Incorrect schedule data              | High   | Validate administrator input                            |
| Unauthorized record access           | High   | Apply authentication and role-based authorization       |
| Scope becomes too large              | Medium | Prioritize core registration features                   |

## 15. Future Enhancements

Possible future improvements include:

* Email or SMS notifications
* Automatic waitlist promotion
* Degree-progress tracking
* Course recommendations
* Advisor appointment scheduling
* Mobile application
* Tuition-payment integration
* Full university ERP integration
* Registration analytics
* Classroom-capacity validation

## 16. Conclusion

CoursePilot is intended to improve course registration by combining seat management, waitlist tracking, prerequisite checking, credit validation, schedule-conflict prevention, advisor approval, and schedule viewing in one platform.

The product requirements in this document will guide the preparation of user personas, user journeys, user stories, acceptance criteria, the Software Requirements Specification, and the Technical Design Document.
