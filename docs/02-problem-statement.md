# CoursePilot Problem Statement

## 1. Introduction

Course registration is an essential academic activity through which students select courses for an upcoming semester. A reliable registration system should help students identify eligible courses, select suitable sections, satisfy academic requirements, and understand the status of their registration requests.

However, students often experience problems such as unavailable seats, unclear waiting-list procedures, overlapping class schedules, missing prerequisite information, and delayed registration decisions. These issues can make the registration process confusing, time-consuming, and stressful.

CoursePilot is proposed to address these problems through a centralized course-registration and waitlist-management platform.

## 2. Existing Problems

### 2.1 Limited Visibility of Available Seats

Students may not always have clear or updated information about the number of seats remaining in a course section. As a result, they may spend time attempting to register for sections that are already full.

### 2.2 Unclear Waiting-List Process

When a course section reaches its seat limit, students may not know:

* Whether they can join a waiting list.
* Their current position on the waiting list.
* Whether their waiting-list request has been accepted.
* What happens when a seat becomes available.

A lack of transparency can create uncertainty and repeated inquiries to academic offices.

### 2.3 Schedule Conflicts

Students may select two course sections that are scheduled on the same day and at overlapping times. If the system does not detect this conflict, the student may create an invalid class schedule.

The final registration submission should therefore be blocked until the student removes the conflict or selects another section.

### 2.4 Missing Prerequisite Validation

Some advanced courses require students to complete specific prerequisite courses. Without automatic prerequisite checking, students may attempt to register for courses for which they are not academically eligible.

This can create additional work for advisors and administrators because invalid requests must be reviewed manually.

### 2.5 Credit-Requirement Problems

Universities may define minimum and maximum credit limits for a semester. A student may accidentally select:

* Fewer credits than the required minimum.
* More credits than the allowed maximum.

A registration system should calculate the student's selected credits and provide a clear validation message before final submission.

### 2.6 Unclear Registration Status

Students may not clearly understand whether a selected course is:

* Pending approval.
* Approved.
* Rejected.
* Waitlisted.
* Dropped.

Without clear status information, students may repeatedly contact advisors or administrative offices for updates.

### 2.7 Lack of Detailed Rejection Information

A registration request may be rejected because of:

* Missing prerequisites.
* Credit-limit violations.
* Schedule conflicts.
* Administrative decisions.
* Course restrictions.

If the system only displays “Rejected” without an explanation, the student may not understand how to correct the problem.

### 2.8 Difficulty Viewing the Final Class Schedule

After registration, students need a clear schedule containing:

* Course code and title.
* Section.
* Instructor.
* Class day.
* Start and end time.
* Room number.
* Credit value.

If this information is displayed across multiple pages, students may find it difficult to understand their complete semester schedule.

### 2.9 Manual Administrative Work

Advisors and department administrators may need to manually verify:

* Student prerequisites.
* Credit totals.
* Seat availability.
* Registration conflicts.
* Waiting-list order.

This increases administrative workload and may lead to delays or human error.

## 3. Problem Impact

The existing problems may result in:

* Invalid course selections.
* Overlapping class schedules.
* Delayed registration approval.
* Confusion about waiting-list positions.
* Repeated student inquiries.
* Increased advisor and administrator workload.
* Poor student experience.
* Inaccurate or incomplete semester schedules.

## 4. Proposed Solution

CoursePilot will provide a centralized web-based system where students can browse course sections, view seat availability, select courses, and submit registration requests.

The system will automatically:

* Check course prerequisites.
* Calculate selected credits.
* Validate minimum and maximum credit limits.
* Detect overlapping class schedules.
* Block final submission when a conflict exists.
* Place students on a waiting list when a course is full.
* Display waiting-list positions.
* Show registration statuses.
* Provide registered-course schedule information.

Academic advisors will be able to review pending registration requests and approve or reject them. Department administrators will be able to manage courses, sections, seat limits, schedules, rooms, instructors, and prerequisites.

## 5. Problem Statement

The current course-registration process may lack transparent seat information, automatic waiting-list management, prerequisite validation, credit validation, schedule-conflict detection, and clear registration-status tracking.

Therefore, there is a need for a web-based system that allows students to register for eligible courses, prevents invalid final submissions, manages course capacity and waiting lists, supports advisor approval, and provides a clear semester class schedule.

CoursePilot aims to meet this need by making course registration more accurate, transparent, efficient, and user-friendly.

## 6. Expected Benefits

CoursePilot is expected to:

* Reduce invalid registration requests.
* Prevent students from submitting conflicting course schedules.
* Improve waiting-list transparency.
* Reduce manual verification work.
* Provide faster and clearer registration feedback.
* Improve communication between students, advisors, and administrators.
* Provide students with an organized semester schedule.
