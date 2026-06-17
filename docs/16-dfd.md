# CoursePilot Data Flow Diagrams

## 1. Introduction

A Data Flow Diagram (DFD) shows how information moves between users, system processes, and data stores.

This document includes:

* Context Diagram
* Level 0 DFD
* Level 1 DFD for Course Registration
* Level 1 DFD for Waitlist Management
* Level 1 DFD for Advisor Approval
* Data stores and major data flows

---

# 2. DFD Components

## 2.1 External Entities

| Entity ID | External Entity          | Description                                                                                   |
| --------- | ------------------------ | --------------------------------------------------------------------------------------------- |
| E1        | Student                  | Browses courses, selects sections, submits registration, joins waitlists, and views schedules |
| E2        | Academic Advisor         | Reviews, approves, or rejects registration requests                                           |
| E3        | Department Administrator | Manages courses, sections, rooms, schedules, capacities, and prerequisites                    |
| E4        | System Administrator     | Manages user accounts, roles, permissions, and system settings                                |

## 2.2 Main Processes

| Process ID | Process                       | Description                                                                 |
| ---------- | ----------------------------- | --------------------------------------------------------------------------- |
| P1         | User Authentication           | Authenticates users and identifies their roles                              |
| P2         | Course and Section Management | Manages course offerings and section information                            |
| P3         | Course Registration           | Processes course selection and final registration                           |
| P4         | Registration Validation       | Checks prerequisites, credits, conflicts, duplicates, and seat availability |
| P5         | Waitlist Management           | Manages waiting-list entries, positions, and promotions                     |
| P6         | Advisor Approval              | Handles registration approval and rejection                                 |
| P7         | Schedule Management           | Generates registered-course lists and weekly schedules                      |
| P8         | User and Role Management      | Manages accounts, roles, and permissions                                    |

## 2.3 Data Stores

| Data Store ID | Data Store                | Description                                                             |
| ------------- | ------------------------- | ----------------------------------------------------------------------- |
| D1            | User Accounts             | Stores login details, account status, and roles                         |
| D2            | Student Records           | Stores student profiles, programs, and advisor assignments              |
| D3            | Course Catalogue          | Stores course codes, titles, credits, and mandatory status              |
| D4            | Course Sections           | Stores sections, instructors, capacities, semesters, and availability   |
| D5            | Academic Records          | Stores completed courses and grades                                     |
| D6            | Prerequisite Records      | Stores prerequisite relationships between courses                       |
| D7            | Registration Records      | Stores selected, pending, approved, rejected, and dropped registrations |
| D8            | Waitlist Records          | Stores queue entries, positions, timestamps, and statuses               |
| D9            | Schedule and Room Records | Stores class days, times, rooms, and timetable information              |
| D10           | Registration Periods      | Stores registration opening and closing dates                           |
| D11           | Notifications             | Stores registration, approval, and waitlist notifications               |
| D12           | Audit Logs                | Stores important system and administrative activities                   |

---

# 3. Context Diagram

The context diagram represents CoursePilot as one main process and shows how external users exchange information with the system.

```mermaid
flowchart LR
    Student[Student]
    Advisor[Academic Advisor]
    DeptAdmin[Department Administrator]
    SysAdmin[System Administrator]

    System((CoursePilot System))

    Student -->|Login credentials, course selections, registration requests, waitlist requests| System
    System -->|Courses, seats, validation messages, statuses, waitlist position, class schedule| Student

    Advisor -->|Login credentials, approval decisions, rejection reasons, comments| System
    System -->|Pending requests, student details, validation results| Advisor

    DeptAdmin -->|Course, section, room, schedule, capacity, prerequisite data| System
    System -->|Enrollment data, section status, waiting-list reports| DeptAdmin

    SysAdmin -->|User account, role, and permission updates| System
    System -->|User information, activity logs, system status| SysAdmin
```

---

# 4. Level 0 DFD

The Level 0 DFD divides CoursePilot into its major processes.

```mermaid
flowchart LR
    Student[Student]
    Advisor[Academic Advisor]
    DeptAdmin[Department Administrator]
    SysAdmin[System Administrator]

    P1((1.0 User Authentication))
    P2((2.0 Course and Section Management))
    P3((3.0 Course Registration))
    P4((4.0 Registration Validation))
    P5((5.0 Waitlist Management))
    P6((6.0 Advisor Approval))
    P7((7.0 Schedule Management))
    P8((8.0 User and Role Management))

    D1[(D1 User Accounts)]
    D2[(D2 Student Records)]
    D3[(D3 Course Catalogue)]
    D4[(D4 Course Sections)]
    D5[(D5 Academic Records)]
    D6[(D6 Prerequisites)]
    D7[(D7 Registration Records)]
    D8[(D8 Waitlist Records)]
    D9[(D9 Schedule and Room Records)]
    D10[(D10 Registration Periods)]
    D11[(D11 Notifications)]
    D12[(D12 Audit Logs)]

    Student -->|Credentials| P1
    Advisor -->|Credentials| P1
    DeptAdmin -->|Credentials| P1
    SysAdmin -->|Credentials| P1
    P1 <--> D1
    P1 -->|Authentication result| Student
    P1 -->|Authentication result| Advisor
    P1 -->|Authentication result| DeptAdmin
    P1 -->|Authentication result| SysAdmin

    DeptAdmin -->|Course and section data| P2
    P2 <--> D3
    P2 <--> D4
    P2 <--> D6
    P2 <--> D9
    P2 <--> D10
    P2 -->|Course and section information| Student

    Student -->|Selected courses and final submission| P3
    P3 -->|Validation request| P4
    P4 <--> D2
    P4 <--> D4
    P4 <--> D5
    P4 <--> D6
    P4 <--> D7
    P4 <--> D9
    P4 <--> D10
    P4 -->|Validation result| P3

    P3 <--> D7
    P3 -->|Registration status| Student
    P3 -->|Pending request| P6

    Student -->|Join or leave waitlist| P5
    P5 <--> D4
    P5 <--> D8
    P5 -->|Waitlist position and status| Student
    P5 -->|Promotion request| P6

    Advisor -->|Approval or rejection decision| P6
    P6 <--> D7
    P6 <--> D2
    P6 -->|Updated status| Student
    P6 --> D11
    P6 --> D12

    Student -->|Schedule request| P7
    P7 <--> D7
    P7 <--> D9
    P7 -->|Registered-course schedule| Student

    SysAdmin -->|Account and role updates| P8
    P8 <--> D1
    P8 --> D12
```

---

# 5. Level 1 DFD: Course Registration

This diagram shows the detailed course-registration process.

```mermaid
flowchart TD
    Student[Student]

    P31((3.1 Browse Courses))
    P32((3.2 Select Course Section))
    P33((3.3 Check Duplicate and Completed Course))
    P34((3.4 Check Prerequisites))
    P35((3.5 Check Schedule Conflict))
    P36((3.6 Calculate and Validate Credits))
    P37((3.7 Check Seat Availability))
    P38((3.8 Review Registration Summary))
    P39((3.9 Submit Final Registration))

    D3[(D3 Course Catalogue)]
    D4[(D4 Course Sections)]
    D5[(D5 Academic Records)]
    D6[(D6 Prerequisites)]
    D7[(D7 Registration Records)]
    D9[(D9 Schedule and Room Records)]
    D10[(D10 Registration Periods)]

    Student -->|Search and filter request| P31
    P31 <--> D3
    P31 <--> D4
    P31 <--> D9
    P31 -->|Course and section results| Student

    Student -->|Selected section| P32
    P32 --> P33

    P33 <--> D5
    P33 <--> D7
    P33 -->|Valid selection| P34
    P33 -->|Duplicate or completed-course error| Student

    P34 <--> D5
    P34 <--> D6
    P34 -->|Prerequisite passed| P35
    P34 -->|Missing prerequisite message| Student

    P35 <--> D7
    P35 <--> D9
    P35 -->|No conflict| P36
    P35 -->|Conflict details| Student

    P36 <--> D3
    P36 -->|Valid credit total| P37
    P36 -->|Credit warning or error| Student

    P37 <--> D4
    P37 -->|Seat available| P38
    P37 -->|Section full| Student

    P38 -->|Registration summary| Student
    Student -->|Final confirmation| P39

    P39 <--> D10
    P39 <--> D4
    P39 --> D7
    P39 -->|Pending registration status| Student
```

---

# 6. Course Registration Data Flow Description

## 6.1 Course Browsing

The student sends search and filter information to the system.

The system reads:

* Course information from the Course Catalogue
* Section information from Course Sections
* Class time and room information from Schedule and Room Records

The system returns matching course sections to the student.

## 6.2 Course Selection

When the student selects a section, the system checks:

* Duplicate registration
* Previously completed course
* Course prerequisites
* Class schedule conflicts
* Credit limits
* Seat availability

## 6.3 Final Submission

When the student clicks Final Submit, the system performs all validations again.

If every rule passes:

* The registration record is created
* The registration receives Pending status
* The request is sent for advisor review

If a rule fails:

* Submission is blocked
* A clear validation message is returned

---

# 7. Level 1 DFD: Schedule-Conflict Validation

```mermaid
flowchart TD
    Student[Student]

    P41((4.1 Receive Selected Section))
    P42((4.2 Retrieve Selected and Approved Courses))
    P43((4.3 Compare Class Days))
    P44((4.4 Compare Start and End Times))
    P45((4.5 Generate Validation Result))

    D7[(D7 Registration Records)]
    D9[(D9 Schedule and Room Records)]

    Student -->|New course section| P41
    P41 --> P42

    P42 <--> D7
    P42 <--> D9
    P42 --> P43

    P43 -->|Different days| P45
    P43 -->|Same day| P44

    P44 -->|No overlap| P45
    P44 -->|Overlap found| P45

    P45 -->|Valid schedule| Student
    P45 -->|Conflict error with course, section, day and time| Student
```

## 7.1 Conflict Rule

Two classes conflict when:

```text
They occur on the same day
AND
New start time is earlier than the existing end time
AND
New end time is later than the existing start time
```

If a conflict exists, the system blocks course selection or final submission.

---

# 8. Level 1 DFD: Waitlist Management

```mermaid
flowchart TD
    Student[Student]
    DeptAdmin[Department Administrator]

    P51((5.1 Receive Waitlist Request))
    P52((5.2 Validate Eligibility))
    P53((5.3 Create Waitlist Entry))
    P54((5.4 Calculate Queue Position))
    P55((5.5 Monitor Seat Availability))
    P56((5.6 Promote Eligible Student))
    P57((5.7 Update Queue Positions))
    P58((5.8 Send Status Notification))

    D4[(D4 Course Sections)]
    D5[(D5 Academic Records)]
    D6[(D6 Prerequisites)]
    D7[(D7 Registration Records)]
    D8[(D8 Waitlist Records)]
    D9[(D9 Schedule Records)]
    D11[(D11 Notifications)]

    Student -->|Join waitlist request| P51
    P51 --> P52

    P52 <--> D5
    P52 <--> D6
    P52 <--> D7
    P52 <--> D9
    P52 -->|Eligible| P53
    P52 -->|Not eligible with reason| Student

    P53 --> D8
    P53 --> P54
    P54 <--> D8
    P54 -->|Queue position| Student

    DeptAdmin -->|Capacity update| P55
    P55 <--> D4
    P55 <--> D7
    P55 -->|Seat available| P56

    P56 <--> D8
    P56 <--> D5
    P56 <--> D6
    P56 --> D7
    P56 --> P57

    P57 <--> D8
    P57 --> P58
    P58 --> D11
    P58 -->|Waitlist status update| Student
```

---

# 9. Waitlist Data Flow Description

## 9.1 Joining the Waitlist

When a section is full, the student sends a waitlist request.

The system checks:

* Whether the student is already registered
* Whether the student is already waitlisted
* Prerequisite completion
* Schedule conflicts
* Registration-period status

If the student is eligible:

* A waitlist entry is created
* The joining time is recorded
* A queue position is calculated
* The position is displayed to the student

## 9.2 Seat Availability

A seat may become available when:

* A registered student drops the course
* The administrator increases section capacity
* An approved registration is cancelled

## 9.3 Promotion

When a seat becomes available:

1. The system reads the ordered waiting list.
2. The first eligible student is selected.
3. The student is promoted to Pending or Approved status.
4. Remaining waiting-list positions are updated.
5. A notification is generated.

---

# 10. Level 1 DFD: Advisor Approval

```mermaid
flowchart TD
    Advisor[Academic Advisor]
    Student[Student]

    P61((6.1 View Pending Requests))
    P62((6.2 Retrieve Student Registration Details))
    P63((6.3 Review Validation Results))
    P64((6.4 Approve or Reject Request))
    P65((6.5 Record Decision and Comment))
    P66((6.6 Notify Student))

    D2[(D2 Student Records)]
    D5[(D5 Academic Records)]
    D7[(D7 Registration Records)]
    D8[(D8 Waitlist Records)]
    D11[(D11 Notifications)]
    D12[(D12 Audit Logs)]

    Advisor -->|Request pending registrations| P61
    P61 <--> D7
    P61 -->|Pending request list| Advisor

    Advisor -->|Select registration request| P62
    P62 <--> D2
    P62 <--> D5
    P62 <--> D7
    P62 <--> D8
    P62 --> P63

    P63 -->|Student, credit, prerequisite and conflict information| Advisor
    Advisor -->|Approval or rejection decision| P64

    P64 --> P65
    P65 --> D7
    P65 --> D12
    P65 --> P66

    P66 --> D11
    P66 -->|Updated status and advisor comment| Student
```

---

# 11. Advisor Approval Data Flow Description

The advisor requests a list of pending registrations.

The system retrieves:

* Student information
* Selected courses
* Total credits
* Prerequisite validation results
* Schedule-conflict results
* Waitlist information

The advisor then:

* Approves the request, or
* Rejects the request and provides a reason

The decision is saved in Registration Records and Audit Logs.

The student receives the updated registration status.

---

# 12. Level 1 DFD: Course and Section Management

```mermaid
flowchart TD
    DeptAdmin[Department Administrator]

    P21((2.1 Create or Update Course))
    P22((2.2 Create or Update Section))
    P23((2.3 Assign Instructor))
    P24((2.4 Assign Room and Schedule))
    P25((2.5 Set Seat Capacity))
    P26((2.6 Define Prerequisites))
    P27((2.7 Manage Registration Period))

    D3[(D3 Course Catalogue)]
    D4[(D4 Course Sections)]
    D6[(D6 Prerequisite Records)]
    D9[(D9 Schedule and Room Records)]
    D10[(D10 Registration Periods)]
    D12[(D12 Audit Logs)]

    DeptAdmin -->|Course information| P21
    P21 --> D3
    P21 --> D12

    DeptAdmin -->|Section information| P22
    P22 <--> D3
    P22 --> D4
    P22 --> D12

    DeptAdmin -->|Instructor assignment| P23
    P23 --> D4
    P23 --> D12

    DeptAdmin -->|Room, day and time| P24
    P24 --> D9
    P24 --> D12

    DeptAdmin -->|Section capacity| P25
    P25 --> D4
    P25 --> D12

    DeptAdmin -->|Prerequisite relationship| P26
    P26 <--> D3
    P26 --> D6
    P26 --> D12

    DeptAdmin -->|Opening and closing dates| P27
    P27 --> D10
    P27 --> D12
```

---

# 13. Main Data Flow Summary

| Source                            | Data Flow                        | Destination             |
| --------------------------------- | -------------------------------- | ----------------------- |
| Student                           | Login credentials                | Authentication Process  |
| Authentication Process            | Login result and role            | Student                 |
| Student                           | Search and filter request        | Course Browsing Process |
| Course Data Stores                | Course and section details       | Student                 |
| Student                           | Selected course section          | Registration Process    |
| Academic Records                  | Completed courses                | Prerequisite Validation |
| Schedule Records                  | Class days and times             | Conflict Validation     |
| Course Sections                   | Capacity and available seats     | Seat Validation         |
| Student                           | Waitlist request                 | Waitlist Management     |
| Waitlist Records                  | Queue position                   | Student                 |
| Registration Process              | Pending request                  | Academic Advisor        |
| Academic Advisor                  | Approval or rejection            | Registration Records    |
| Registration Records              | Updated status                   | Student                 |
| Registration and Schedule Records | Approved class schedule          | Student                 |
| Department Administrator          | Course and section configuration | Course Data Stores      |
| System Administrator              | User and role updates            | User Accounts           |

---

# 14. DFD Assumptions

The diagrams assume that:

* Students, advisors, and administrators already have user accounts.
* Student academic records are available.
* Courses and sections are configured before registration begins.
* Prerequisite records are accurate.
* Class schedules and room details are available.
* Registration periods are configured.
* Each student has an assigned academic advisor.
* Waitlist order follows the joining timestamp.

---

# 15. Conclusion

The CoursePilot DFDs show how registration information moves between students, advisors, administrators, system processes, and data stores.

The diagrams cover:

* Authentication
* Course browsing
* Course registration
* Prerequisite validation
* Credit validation
* Schedule-conflict detection
* Seat management
* Waiting-list management
* Advisor approval
* Class-schedule generation
* Administrative course management

These data flows will support the complete SRS, ERD, system design, database design, and API design.
