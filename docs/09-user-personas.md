# CoursePilot User Personas

## 1. Introduction

User personas are fictional representations of the main users of CoursePilot. They help describe each user group's goals, responsibilities, frustrations, technical ability, and expectations.

The personas in this document are based on the information gathered from student interviews, survey planning, observation of existing course-registration systems, and the identified project requirements.

All names used in this document are fictional.

---

## 2. Persona 1: Undergraduate Student

### Basic Information

| Item              | Details                          |
| ----------------- | -------------------------------- |
| Name              | Arafat Hossain                   |
| Age               | 22                               |
| Role              | Final-year undergraduate student |
| Academic status   | One trimester remaining          |
| Technical ability | Moderate                         |
| Primary device    | Laptop and smartphone            |

### Background

Arafat is a final-year student who has used the university course-registration portal several times. He needs to register for the remaining courses required to complete his degree.

During registration, he often faces difficulties because available-seat information changes quickly. A section may display several available seats, but after confirmation, the system may report that the section is already full.

He also finds it difficult to remember the schedules of previously selected courses while searching for additional sections.

### Goals

Arafat wants to:

* View accurate and updated seat availability.
* Register for required courses quickly.
* Identify mandatory courses.
* See prerequisite requirements before selection.
* Avoid schedule conflicts.
* View the total number of selected credits.
* Join a waiting list when a course is full.
* View his waiting-list position.
* Track registration approval.
* View his final weekly schedule.

### Frustrations

Arafat experiences the following problems:

* Seat counts may become outdated.
* A section may become full during confirmation.
* Prerequisites are not always clearly shown.
* Mandatory courses may not be labelled.
* Selected course times are difficult to remember.
* Students may need to request manual seat increases.
* Registration rejection reasons may not be clear.

### Needs from CoursePilot

Arafat needs CoursePilot to:

* Update seat counts automatically.
* Recheck seat availability during confirmation.
* Show selected courses beside search results.
* Display missing prerequisites.
* Calculate credits instantly.
* Block conflicting selections.
* Provide a waiting-list option.
* Display clear status and error messages.
* Show approved courses in a weekly timetable.

### User Quote

> “I want to know whether a seat is really available before I confirm, and I want to see my selected schedule while choosing another course.”

---

## 3. Persona 2: Academic Advisor

### Basic Information

| Item              | Details            |
| ----------------- | ------------------ |
| Name              | Dr. Farhana Rahman |
| Age               | 41                 |
| Role              | Academic advisor   |
| Experience        | 12 years           |
| Technical ability | Moderate           |
| Primary device    | Desktop computer   |

### Background

Dr. Farhana advises undergraduate students and reviews their course-registration requests.

She regularly checks whether students have selected appropriate courses, completed prerequisites, and followed semester credit limits. Manually checking these conditions for many students takes time and increases the possibility of errors.

### Goals

Dr. Farhana wants to:

* View pending registration requests.
* Review student academic information.
* Check prerequisite completion.
* Review selected credit totals.
* Identify schedule conflicts.
* Approve valid requests.
* Reject invalid requests with explanations.
* View student registration history.
* Reduce repetitive manual verification.

### Frustrations

Her main frustrations include:

* Incomplete student information.
* Too many invalid registration requests.
* Missing prerequisite information.
* Students exceeding credit limits.
* Students asking repeatedly about approval status.
* Difficulty tracking previous decisions.
* Lack of clear rejection comments.

### Needs from CoursePilot

Dr. Farhana needs CoursePilot to:

* Automatically validate prerequisites and credit limits.
* Highlight registration problems.
* Show all selected courses in one place.
* Provide approve and reject actions.
* Allow comments and rejection reasons.
* Keep a history of registration decisions.
* Reduce unnecessary student inquiries.

### User Quote

> “The system should identify academic problems before the request reaches me, so I can focus on advising rather than repeated manual checking.”

---

## 4. Persona 3: Department Administrator

### Basic Information

| Item              | Details                  |
| ----------------- | ------------------------ |
| Name              | Mahmudul Hasan           |
| Age               | 35                       |
| Role              | Department administrator |
| Experience        | 8 years                  |
| Technical ability | Moderate to high         |
| Primary device    | Desktop computer         |

### Background

Mahmudul manages course offerings for each trimester. He creates sections, sets seat limits, assigns rooms and instructors, and monitors enrollment.

When sections become full, students often request additional seats. Managing these requests manually can be difficult and may create confusion about who should receive an available seat.

### Goals

Mahmudul wants to:

* Create and update courses.
* Create course sections.
* Set seat capacities.
* Assign instructors and rooms.
* Define class schedules.
* Configure course prerequisites.
* Mark mandatory courses.
* Monitor enrollment.
* Monitor waiting lists.
* Open and close registration periods.
* Maintain accurate academic data.

### Frustrations

Mahmudul experiences:

* Repeated requests for seat increases.
* Unclear waiting-list priority.
* Incorrect course or room information.
* Over-capacity sections.
* Manual monitoring of available seats.
* Difficulty identifying high-demand sections.
* Registration data spread across different pages.

### Needs from CoursePilot

Mahmudul needs CoursePilot to:

* Maintain section capacity accurately.
* Provide a first-come, first-served waiting list.
* Show real-time enrollment information.
* Prevent over-enrollment.
* Allow course, room, instructor, and schedule updates.
* Display high-demand and full sections.
* Provide clear administrative controls.

### User Quote

> “A proper waiting list would reduce arguments about seat increases and make section management more organized.”

---

## 5. Persona 4: System Administrator

### Basic Information

| Item              | Details              |
| ----------------- | -------------------- |
| Name              | Samiul Tamim         |
| Age               | 30                   |
| Role              | System administrator |
| Experience        | 6 years              |
| Technical ability | High                 |
| Primary device    | Desktop computer     |

### Background

Samiul is responsible for maintaining the technical operation of CoursePilot. He manages accounts, user roles, system access, security, logs, and system configuration.

He must ensure that students cannot access administrative information and that advisors and administrators only access features related to their responsibilities.

### Goals

Samiul wants to:

* Manage user accounts.
* Assign roles and permissions.
* Protect student records.
* Monitor system activity.
* Maintain system availability.
* Review logs and errors.
* Prevent unauthorized access.
* Manage backups and recovery procedures.

### Frustrations

Samiul is concerned about:

* Unauthorized access.
* Incorrect role assignments.
* Weak passwords.
* System downtime during registration.
* Data loss.
* Missing audit logs.
* High traffic during registration periods.

### Needs from CoursePilot

Samiul needs CoursePilot to:

* Use secure authentication.
* Apply role-based access control.
* Record important user activities.
* Protect sensitive academic information.
* Support backups and recovery.
* Provide standardized error logging.
* Remain stable during high registration traffic.

### User Quote

> “Every user should access only the information and actions allowed for their role.”

---

## 6. Persona Comparison

| Persona                  | Primary Goal                           | Main Problem                                  | Important Feature                           |
| ------------------------ | -------------------------------------- | --------------------------------------------- | ------------------------------------------- |
| Student                  | Complete valid course registration     | Outdated seats and unclear course information | Real-time seats, validation, and schedule   |
| Academic advisor         | Review student requests efficiently    | Repetitive manual checking                    | Automated validation and approval dashboard |
| Department administrator | Manage course offerings and seats      | Manual seat and waitlist management           | Section and waitlist management             |
| System administrator     | Maintain secure and reliable operation | Unauthorized access and system downtime       | Role-based access and monitoring            |

## 7. User Priorities

### High-Priority Student Needs

* Accurate seat availability
* Waiting-list position
* Prerequisite visibility
* Instant credit calculation
* Schedule-conflict detection
* Registration-status tracking
* Weekly class timetable

### High-Priority Advisor Needs

* Pending request list
* Student academic summary
* Validation results
* Approval and rejection controls
* Decision comments and history

### High-Priority Administrator Needs

* Course and section management
* Capacity management
* Waiting-list monitoring
* Schedule and room management
* Registration-period control

### High-Priority System Administrator Needs

* User and role management
* Authentication
* Authorization
* Security logs
* Backup and recovery
* System monitoring

## 8. Conclusion

The CoursePilot personas represent the main groups that will interact with the system.

Students require a transparent and simple registration experience. Academic advisors need efficient review tools. Department administrators need reliable course, section, seat, and waiting-list management. System administrators need secure and controlled access.

These personas will guide the user journey, user stories, acceptance criteria, functional requirements, and technical design of CoursePilot.
