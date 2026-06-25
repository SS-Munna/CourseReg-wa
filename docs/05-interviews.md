# CoursePilot Interviews

## 1. Introduction

Interviews were conducted as part of the requirement-gathering process for CoursePilot. The purpose of the interviews was to understand the practical difficulties students experience while registering for courses through the existing university portal.

Three senior students participated in the interviews. One participant had one trimester remaining, while the other two had recently completed their academic coursework. Their experience with multiple course-registration periods made their feedback relevant to the proposed system.

The participants' names have not been included to protect their privacy.

## 2. Interview Objectives

The interviews were conducted to:

* Identify common problems during course registration.
* Understand whether available-seat information is updated in real time.
* Explore the need for a structured waiting-list system.
* Understand difficulties related to course prerequisites.
* Identify problems caused by class-schedule conflicts.
* Determine whether students need instant credit calculations.
* Identify what information should appear in the final registered-course schedule.

## 3. Participant Information

| Participant ID | Role                  | Academic Status                     | Interview Method  |
| -------------- | --------------------- | ----------------------------------- | ----------------- |
| Student 1      | Undergraduate student | Final year, one trimester remaining | Online discussion |
| Student 2      | Undergraduate student | Recently completed coursework       | Online discussion |
| Student 3      | Undergraduate student | Recently completed coursework       | Online discussion |

## 4. Interview Questions

The following questions were discussed with the participants:

1. What problems have you experienced during course registration?
2. Can students currently see the number of available seats?
3. What normally happens when a course section becomes full?
4. Should students be able to see their waiting-list position?
5. What problems do students face with schedule conflicts?
6. Should the portal show the selected credit count and prerequisite eligibility instantly?
7. What information should appear in the final registered-course schedule?

## 5. Interview Responses

### 5.1 Student 1

**Question 1: What problems have you experienced during course registration?**

Response:
The available-seat count does not always update in real time. Sometimes the portal shows that five to ten seats are still available, but after clicking the confirmation button, it says that no seats are left. This usually happens because the page was not refreshed before submission.

The portal also does not clearly show which courses have prerequisites or which courses are mandatory.

**Question 2: Can students currently see the number of available seats?**

Response:
Yes, the number of available seats can be seen. However, the number may be outdated unless the page is manually refreshed.

**Question 3: What normally happens when a course section becomes full?**

Response:
Students usually contact the department and request that the seat limit be increased. This may create competition and confusion among students. A waiting-list system would be more organized and fair.

**Question 4: Should students be able to see their waiting-list position?**

Response:
Yes. Students should be able to see their position so that they can understand their possibility of receiving a seat and decide whether to select another section.

**Question 5: What problems do students face with schedule conflicts?**

Response:
The existing portal does not allow a student to select a course that conflicts with another selected course. However, while searching for new courses, the portal does not clearly show the times of the courses already selected. Therefore, students must remember the schedule or write it down separately.

**Question 6: Should the portal show the selected credit count and prerequisite eligibility instantly?**

Response:
Yes. The portal should show the total number of selected credits immediately. It should also clearly indicate whether the required prerequisite has been completed.

**Question 7: What information should appear in the final registered-course schedule?**

Response:
The schedule should show the course code, course title, section, instructor, class day, class time, room number, credit value, and registration status.

---

### 5.2 Student 2

**Question 1: What problems have you experienced during course registration?**

Response:
The biggest issue is that the seat information can change while students are selecting courses. A course may appear to have seats available, but the seats may already have been taken by other students before final confirmation.

Prerequisite information is also not clearly visible, so students may not know why they cannot select a particular course.

**Question 2: Can students currently see the number of available seats?**

Response:
Yes, but the seat count is not always updated automatically. The page must often be refreshed to see the current seat availability.

**Question 3: What normally happens when a course section becomes full?**

Response:
Students usually request the department to increase the number of seats. Since many students may want the same course, this can create pressure and disagreement. A first-come, first-served waiting list would provide a clearer process.

**Question 4: Should students be able to see their waiting-list position?**

Response:
Yes. The student should see both the waiting-list status and the current position in the queue.

**Question 5: What problems do students face with schedule conflicts?**

Response:
The current system blocks conflicting course selections, which is useful. However, it does not provide a convenient comparison between a new course and the courses already selected. Students have to move between pages or remember the selected class times.

**Question 6: Should the portal show the selected credit count and prerequisite eligibility instantly?**

Response:
Yes. An instant total-credit counter would help students understand whether they have met the minimum credit requirement or exceeded the maximum limit. Missing prerequisites should also be shown before the student tries to register.

**Question 7: What information should appear in the final registered-course schedule?**

Response:
The final schedule should display all registered courses in one place. It should include the course code, course name, section, instructor, class time, room, credit, and approval status.

---

### 5.3 Student 3

**Question 1: What problems have you experienced during course registration?**

Response:
Course registration becomes difficult when many students try to register at the same time. The displayed seat number may not match the actual seat availability during final confirmation.

The portal also does not clearly identify mandatory courses and prerequisite requirements.

**Question 2: Can students currently see the number of available seats?**

Response:
Yes, but the seat number is not reliable without refreshing the page. A live seat count would be more useful.

**Question 3: What normally happens when a course section becomes full?**

Response:
Students contact the department or faculty members and ask for additional seats. Increasing seats may solve the issue temporarily, but it is not a structured solution. A waiting list would help the department manage demand more fairly.

**Question 4: Should students be able to see their waiting-list position?**

Response:
Yes. The position should update automatically when students ahead in the queue receive a seat or leave the waiting list.

**Question 5: What problems do students face with schedule conflicts?**

Response:
The portal prevents direct selection of conflicting courses. However, it is difficult to remember all previously selected class times while browsing additional courses. The system should show the selected schedule beside the course-search results.

**Question 6: Should the portal show the selected credit count and prerequisite eligibility instantly?**

Response:
Yes. Students should see the current selected-credit total after adding or removing a course. The portal should also state the missing prerequisite instead of only preventing selection.

**Question 7: What information should appear in the final registered-course schedule?**

Response:
The final schedule should include course information, section, instructor, day, start and end time, room number, credit, and registration status. A weekly timetable view would also be helpful.

## 6. Summary of Findings

The interviews revealed several common problems in the existing course-registration process:

* All three participants reported that the displayed available-seat count may become outdated.
* All three participants wanted the seat count to update automatically without manually refreshing the page.
* All three participants supported introducing a waiting-list system for full course sections.
* All three participants wanted students to see their current waiting-list position.
* All three participants agreed that schedule conflicts should remain blocked.
* All three participants reported difficulty remembering previously selected course times while browsing additional sections.
* All three participants wanted the portal to show the selected-credit total instantly.
* All three participants wanted prerequisite requirements to be displayed clearly.
* Two participants specifically mentioned that mandatory courses should be identified.
* All three participants wanted a complete final schedule containing course, section, instructor, time, room, credit, and registration-status information.

## 7. Requirements Identified from Interviews

Based on the interview findings, the following requirements were identified:

1. The system should display a real-time or automatically refreshed available-seat count.
2. The system should prevent two students from receiving the same final seat.
3. Students should be able to join a waiting list when a section becomes full.
4. Waiting-list entries should follow a fair first-come, first-served order.
5. Students should be able to view their current waiting-list position.
6. The system should display prerequisite requirements before course selection.
7. The system should clearly identify missing prerequisites.
8. Mandatory courses should be clearly labelled.
9. The system should display the total number of currently selected credits.
10. The system should validate minimum and maximum credit requirements.
11. The system should block the selection or final submission of conflicting courses.
12. The system should display the conflicting course code, section, day, and time.
13. The course-search page should show the schedules of already selected courses.
14. Students should not need to remember or manually write down selected class times.
15. The final registered-course schedule should display:

    * Course code
    * Course title
    * Section
    * Instructor
    * Class day
    * Start and end time
    * Room number
    * Credit value
    * Registration status
16. The system should provide a weekly timetable view of approved courses.

## 8. Influence on CoursePilot

The interview findings directly influenced the proposed CoursePilot features.

### Real-Time Seat Management

CoursePilot will show updated seat availability. Seat allocation will be verified again during registration confirmation to prevent a student from receiving an outdated seat result.

### Waiting-List Management

When a course becomes full, students will be able to join a waiting list instead of depending only on manual seat increases. Students will be able to view their queue position.

### Prerequisite and Mandatory-Course Information

CoursePilot will display prerequisites and clearly state which prerequisite has not been completed. Mandatory courses will also be labelled.

### Credit Tracking

The selected-credit total will update whenever the student adds or removes a course.

### Schedule-Conflict Support

CoursePilot will block conflicting course selections or final submissions. It will also show the selected courses and their class times while the student searches for additional sections.

### Final Schedule Portal

After approval, students will be able to view a complete registered-course schedule and weekly timetable.

## 9. Limitations

The interview process had the following limitations:

* Only three students were interviewed.
* All participants were senior students.
* Academic advisors and department administrators were not included in this initial interview round.
* The findings reflect the experience of one university.
* Registration policies may differ across departments and institutions.

Future requirement-gathering activities should include academic advisors, department administrators, and students from earlier academic years.

## 10. Conclusion

The interviews confirmed that students need more than a basic course-selection system. They need updated seat information, clear prerequisite requirements, instant credit calculation, transparent waiting-list positions, better schedule-conflict information, and a complete final timetable.

These findings will be used in the CoursePilot PRD, SRS, user stories, acceptance criteria, database design, and API design.
