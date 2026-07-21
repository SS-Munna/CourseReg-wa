# CoursePilot Project Overview

## 1. Project Name

**CoursePilot**

## 2. Project Type

Web-Based Course Registration and Waitlist Management System

## 3. Project Description

CoursePilot is a web-based platform designed to improve the university course-registration process. It will allow students to log in, view available course sections, submit registration requests, and monitor the status of their selected courses.

Every course section will have a fixed number of available seats. When all seats in a section are filled, additional students will be able to join a waiting list. Students will be able to view their current waitlist position and monitor whether their registration request is pending, approved, rejected, or waitlisted.

The system will also help prevent common registration errors. It will check whether students have completed the required prerequisite courses, verify minimum and maximum credit requirements, and detect overlapping class schedules. Final registration submission will be blocked when a schedule conflict is found.

After course registration is approved, students will be able to view their registered courses in a student portal. The portal will display course codes, course titles, sections, class days, class times, room numbers, instructors, credits, and registration statuses.

## 4. Background

Course registration is an important academic process in universities. However, students may experience difficulties when seats become unavailable, course schedules overlap, prerequisites are not clearly checked, or approval decisions are difficult to track.

A lack of clear seat, waitlist, and registration-status information can make the process confusing and time-consuming. CoursePilot is proposed as a centralized platform that makes the registration process more organized, transparent, and user-friendly.

## 5. Project Objectives

The main objectives of CoursePilot are:

* To provide students with a simple platform for course registration.
* To display available courses, sections, seats, schedules, and room information.
* To manage fixed seat capacity for every course section.
* To allow students to join a waiting list when a section is full.
* To display each student's current waitlist position.
* To check course prerequisites before accepting a registration request.
* To validate minimum and maximum semester credit requirements.
* To detect overlapping class schedules.
* To block final submission when schedule conflicts exist.
* To allow academic advisors to approve or reject registration requests.
* To allow students to track their registration status.
* To provide students with a complete registered-course schedule.

## 6. Intended Users

### 6.1 Students

Students will use the system to:

* Log in to their accounts.
* Browse offered courses and sections.
* View available seats.
* Select courses.
* Join waiting lists.
* Check registration status.
* View registered-course schedules.

### 6.2 Academic Advisors

Academic advisors will use the system to:

* Review student registration requests.
* Check student credit loads.
* Approve or reject registration requests.
* Provide comments when necessary.

### 6.3 Department Administrators

Department administrators will use the system to:

* Add and update courses.
* Create course sections.
* Define seat capacity.
* Assign rooms, schedules, and instructors.
* Define course prerequisites.
* Monitor registrations and waiting lists.

### 6.4 System Administrators

System administrators will manage:

* User accounts.
* User roles and permissions.
* System configuration.
* Security and access control.

## 7. Core Features

The core features of CoursePilot include:

1. User login and authentication.
2. Role-based access for students, advisors, and administrators.
3. Course and section browsing.
4. Seat-capacity management.
5. Course-registration requests.
6. Automatic waiting-list placement.
7. Waitlist-position tracking.
8. Prerequisite validation.
9. Minimum and maximum credit validation.
10. Class-schedule conflict detection.
11. Final-submission blocking for conflicting courses.
12. Registration approval and rejection.
13. Registration-status tracking.
14. Registered-course schedule viewing.
15. Class time and room-number display.

## 8. Proposed Technology Stack

* **Frontend:** React
* **Backend:** FastAPI
* **Database:** AWS DynamoDB
* **API Architecture:** REST API
* **Version Control:** Git and GitHub
* **Project Management:** GitHub Issues and GitHub Projects

## 9. Project Scope

The initial version of CoursePilot will focus on:

* Course and section management.
* Student course registration.
* Seat and waitlist management.
* Registration validation.
* Advisor approval.
* Student schedule viewing.

The following functions are outside the initial project scope:

* Tuition and payment processing.
* Student attendance management.
* Examination management.
* Grade calculation.
* Complete university ERP integration.

## 10. Expected Outcome

The expected outcome is a structured course-registration platform that reduces registration errors and provides clear information about seat availability, waitlist status, approval decisions, and class schedules.

CoursePilot will make the registration process easier for students while helping advisors and administrators manage registrations more efficiently.
