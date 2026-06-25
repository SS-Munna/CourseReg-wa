# CoursePilot Survey Analysis

## 1. Introduction

An online survey was conducted to collect student opinions about common course-registration problems and the proposed features of CoursePilot.

The survey focused on:

* Course-seat availability
* Waiting-list support
* Prerequisite visibility
* Mandatory-course identification
* Selected-credit calculation
* Schedule-conflict handling
* Registration rejection explanations
* Final class-schedule information

The findings were used to validate the proposed CoursePilot requirements and identify the features students considered most useful.

---

## 2. Survey Method

The survey was created using Google Forms and distributed online to university students and recent graduates.

### Survey Details

| Item                | Information                                                           |
| ------------------- | --------------------------------------------------------------------- |
| Survey method       | Online questionnaire using Google Forms                               |
| Collection date     | June 17, 2026                                                         |
| Total responses     | 10                                                                    |
| Question types      | Multiple choice, multiple selection, and optional open-ended response |
| Target participants | Current university students and recent graduates                      |

Participation was voluntary, and no sensitive personal information was required.

---

## 3. Respondent Academic Levels

| Academic Level     | Number of Respondents | Percentage |
| ------------------ | --------------------: | ---------: |
| Final year         |                     6 |        60% |
| Recently completed |                     3 |        30% |
| Third year         |                     1 |        10% |
| **Total**          |                **10** |   **100%** |

Most respondents were final-year students or had recently completed their studies. Therefore, the majority had significant experience with university course-registration systems.

---

## 4. Experience with Full Course Sections

Participants were asked whether they had experienced a course becoming full while they were completing registration.

| Response | Number | Percentage |
| -------- | -----: | ---------: |
| Yes      |      9 |        90% |
| No       |      1 |        10% |

### Finding

Nine out of ten respondents had experienced a course becoming full during registration.

This strongly supports the need for:

* Accurate seat information
* Confirmation-time seat revalidation
* Structured waiting-list management
* Clear full-section notifications

---

## 5. Automatic Seat-Count Updates

Participants were asked whether the displayed available-seat count should update automatically without manually refreshing the page.

| Response | Number | Percentage |
| -------- | -----: | ---------: |
| Yes      |      2 |        20% |
| No       |      7 |        70% |
| Not sure |      1 |        10% |

### Finding

Only 20% directly preferred automatic seat-count updates, while 70% selected No.

However, real-time seat availability was later selected as the most useful CoursePilot feature by half of the respondents. This suggests that students value accurate seat information, although they may not consider continuous automatic refreshing necessary.

### Design Decision

CoursePilot should:

* Display the latest known seat count clearly.
* Refresh seat information at reasonable intervals.
* Allow students to refresh the information manually.
* Always revalidate seat availability during final confirmation.

Confirmation-time validation is essential because the displayed seat count may change while multiple students are registering.

---

## 6. Waiting-List Support

Participants were asked whether students should be able to join a waiting list when a course section is full.

| Response | Number | Percentage |
| -------- | -----: | ---------: |
| Yes      |      6 |        60% |
| No       |      4 |        40% |

### Finding

Most respondents supported a waiting-list system.

This supports including a structured waiting-list process instead of relying only on manual requests for increasing section capacity.

---

## 7. Waiting-List Position Visibility

Participants were asked whether students should be able to see their current waiting-list position.

| Response | Number | Percentage |
| -------- | -----: | ---------: |
| Yes      |      5 |        50% |
| No       |      5 |        50% |

### Finding

Opinions were equally divided.

Although only half of the respondents requested visible queue positions, position tracking remains useful for transparency. It allows students to understand their place in the queue and make alternative registration decisions.

### Design Decision

CoursePilot will display waiting-list positions as a transparency feature, but the interface should remain simple and avoid creating unrealistic guarantees that a seat will become available.

---

## 8. Prerequisite Visibility

Participants were asked whether prerequisite requirements should be clearly displayed before course selection.

| Response | Number | Percentage |
| -------- | -----: | ---------: |
| Yes      |      7 |        70% |
| No       |      2 |        20% |
| Not sure |      1 |        10% |

### Finding

Most respondents supported clear prerequisite visibility.

CoursePilot should display prerequisite information before students attempt to select a course. When a prerequisite is missing, the system should identify the specific required course.

---

## 9. Mandatory-Course Labels

Participants were asked whether mandatory courses should be clearly labelled in the registration portal.

| Response | Number | Percentage |
| -------- | -----: | ---------: |
| Yes      |      7 |        70% |
| No       |      3 |        30% |

### Finding

Most respondents supported mandatory-course labels.

CoursePilot should visually distinguish mandatory courses from elective courses to reduce the possibility of students overlooking required subjects.

---

## 10. Instant Selected-Credit Calculation

Participants were asked whether the system should instantly display the total number of currently selected credits.

| Response | Number | Percentage |
| -------- | -----: | ---------: |
| Yes      |      8 |        80% |
| No       |      1 |        10% |
| Not sure |      1 |        10% |

### Finding

Instant credit calculation received strong support.

CoursePilot should display:

* Current selected credits
* Minimum required credits
* Maximum permitted credits

The value should update whenever a course is added or removed.

---

## 11. Schedule-Conflict Submission Rules

Participants were asked whether final registration submission should be blocked when selected courses have overlapping class times.

| Response              | Number | Percentage |
| --------------------- | -----: | ---------: |
| Yes, block submission |      6 |        60% |
| Show a warning only   |      4 |        40% |
| No action required    |      0 |         0% |

### Finding

Every respondent supported some form of schedule-conflict intervention.

* 60% supported completely blocking invalid submission.
* 40% preferred displaying a warning.
* No respondent supported ignoring schedule conflicts.

### Design Decision

CoursePilot will display a detailed conflict warning immediately and block final submission until the conflict is resolved. This prevents students from creating an unusable class schedule.

---

## 12. Schedule-Conflict Details

Participants were asked whether the system should display the conflicting course code, section, day, and time.

| Response | Number | Percentage |
| -------- | -----: | ---------: |
| Yes      |      7 |        70% |
| No       |      2 |        20% |
| Not sure |      1 |        10% |

### Finding

Most respondents preferred detailed conflict information.

Instead of displaying only a general error, CoursePilot should identify:

* Both conflicting course codes
* Both section numbers
* Class day
* Start time
* End time

This will help students select a suitable alternative section.

---

## 13. Rejection Explanations

Participants were asked whether a rejected registration request should include a clear explanation.

| Response | Number | Percentage |
| -------- | -----: | ---------: |
| Yes      |      6 |        60% |
| No       |      3 |        30% |
| Not sure |      1 |        10% |

### Finding

Most respondents supported clear rejection explanations.

CoursePilot should allow academic advisors to enter a comment or reason when rejecting a request. Students should be able to view that explanation from the registration-status page.

---

## 14. Final Schedule Information

Participants selected the information they wanted to appear in the final registered-course schedule.

Because respondents could select multiple options, the percentages do not total 100%.

| Schedule Information  | Number Selecting It | Percentage |
| --------------------- | ------------------: | ---------: |
| Class day             |                  10 |       100% |
| Course code           |                   9 |        90% |
| Section               |                   9 |        90% |
| Course title          |                   7 |        70% |
| Start and end time    |                   7 |        70% |
| Instructor            |                   4 |        40% |
| Room number           |                   4 |        40% |
| Registration status   |                   4 |        40% |
| Credit value          |                   3 |        30% |
| Weekly timetable view |                   3 |        30% |

### Finding

The most important schedule information was:

1. Class day
2. Course code
3. Section
4. Course title
5. Start and end time

### Design Decision

CoursePilot will display all major schedule details, including:

* Course code
* Course title
* Section
* Instructor
* Class day
* Start and end time
* Room number
* Credit value
* Registration status

A weekly timetable will also be provided as an additional view.

---

## 15. Most Useful CoursePilot Feature

Participants selected the CoursePilot feature they considered most useful.

| Feature                        | Number | Percentage |
| ------------------------------ | -----: | ---------: |
| Real-time seat availability    |      5 |        50% |
| Waiting-list management        |      2 |        20% |
| Schedule-conflict detection    |      2 |        20% |
| Waiting-list position tracking |      1 |        10% |

### Finding

Real-time seat availability was the most frequently selected feature.

Waiting-list functionality and schedule-conflict detection were also identified as valuable features.

The results support prioritizing:

1. Accurate seat availability
2. Waiting-list management
3. Schedule-conflict detection
4. Waiting-list position tracking

---

## 16. Additional Suggestions

Most participants did not provide an additional written suggestion.

One respondent emphasized that the registration portal should be smooth and clear.

### Design Decision

The CoursePilot interface should prioritize:

* Simple navigation
* Clear labels
* Understandable error messages
* Visible registration statuses
* Responsive pages
* Minimal unnecessary steps

---

## 17. Summary of Survey Findings

| Survey Finding                                                      | Requirement Supported                                    |
| ------------------------------------------------------------------- | -------------------------------------------------------- |
| 90% experienced a full course section                               | Seat verification and waiting-list support               |
| 50% selected real-time seat availability as the most useful feature | Accurate seat display and confirmation-time revalidation |
| 60% supported joining a waiting list                                | Waiting-list enrollment                                  |
| 50% supported visible waiting-list positions                        | Queue-position tracking                                  |
| 70% supported clear prerequisite display                            | Prerequisite visibility and validation                   |
| 70% supported mandatory-course labels                               | Mandatory-course identification                          |
| 80% supported instant credit calculation                            | Selected-credit counter                                  |
| 100% supported either blocking or warning for conflicts             | Schedule-conflict detection                              |
| 70% supported detailed conflict information                         | Detailed conflict messages                               |
| 60% supported registration-rejection explanations                   | Advisor comments and rejection reasons                   |
| 100% selected class day for the final schedule                      | Complete registered-course schedule                      |

---

## 18. Impact on CoursePilot Requirements

The survey findings influenced the following CoursePilot decisions:

### High-Priority Requirements

* Accurate section-seat information
* Seat revalidation during confirmation
* Prerequisite visibility and checking
* Instant selected-credit calculation
* Schedule-conflict detection
* Detailed conflict messages
* Final-submission validation

### Supported Requirements

* Waiting-list enrollment
* Waiting-list position display
* Mandatory-course labels
* Advisor rejection explanations
* Complete registered-course schedule
* Weekly timetable view

### Usability Requirements

* Simple and smooth interface
* Clear system messages
* Visible status information
* Easy-to-understand course and schedule details

---

## 19. Survey Limitations

The survey has several limitations:

1. The sample contained only 10 respondents.
2. Most respondents were final-year students or recent graduates.
3. Responses were collected during a single day.
4. The survey used convenience sampling.
5. Some answers showed mixed preferences.
6. Only one participant provided a substantive written suggestion.

Therefore, the results should be treated as supporting evidence rather than a complete representation of all university students.

Additional surveys and usability testing would be useful during future development.

---

## 20. Conclusion

The survey confirms that students frequently experience full course sections and value accurate seat information, credit calculation, prerequisite visibility, and schedule-conflict handling.

The results support the main CoursePilot features, particularly:

* Confirmation-time seat verification
* Waiting-list management
* Prerequisite checking
* Mandatory-course labels
* Instant credit totals
* Schedule-conflict prevention
* Detailed registration feedback
* Complete final schedules

These findings were incorporated into the CoursePilot PRD, SRS, functional requirements, acceptance criteria, and technical design.
