# CoursePilot

CoursePilot is a student course registration and course catalogue web application.

The current implemented features include a responsive student dashboard,
registration-period status, registration summary, course catalogue, and
authenticated draft-course selection. Students can search and filter current
offerings by department, semester, level, course type, and seat availability;
open a complete section-details view; check live availability; validate prerequisite completion
and minimum grades, add, list, or remove their own draft selections, and see
whether their active credit load is within program limits. Overlapping class
schedules are detected across draft, pending, and approved registrations and
blocked with both course and time details. Approved-seat allocation rechecks
capacity inside a locked transaction, so concurrent requests cannot consume
the same final seat. Final submission revalidates the student's current load
and atomically moves only valid draft selections to `pending` advisor review.
The dashboard now exposes that full workflow through an interactive selected-course
panel, live credit summary, actionable validation messages, and a final review
dialog before submission. It also includes student-facing registration-status
and waiting-list panels, so pending, approved, rejected, dropped, and waitlisted
outcomes, advisor comments, and live queue positions are visible in one place.
Eligible students can join or leave full-section waiting lists directly from
the course catalogue and see their live first-come, first-served queue positions.
Approved current-semester registrations are also surfaced as a responsive student
schedule with both weekly timetable and list views, including section, instructor,
meeting time, and room details when they are available. When a seat is released, the
promotion service can atomically approve the first still-eligible student and
record the queue transition, notification, and audit event. Assigned advisors
can list and inspect submitted requests, then atomically approve the whole load
with live capacity protection or reject it with a required reason. Every
advisor decision records the reviewer and time and creates one student
notification and one audit event. Students can read their registration-status
history, including rejection comments and active waiting-list entries, and
drop an owned approved course through its configured deadline. A valid drop
releases the seat and processes one waiting-list promotion in the same
transaction.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, TypeScript, Vite |
| Backend | FastAPI, Python |
| Database Layer | SQLAlchemy relational database |
| Local Demo Database | SQLite |
| Future Database Option | PostgreSQL through DATABASE_URL |

## Current Feature Flow

Role-aware React workspaces -> frontend API services -> FastAPI endpoints -> SQLAlchemy repositories -> registration and course tables -> shared JSON responses -> student registration and advisor review workflows

## Student Registration Workflow

1. Sign in with a student account and confirm that the registration period is open.
2. Browse the current-semester catalogue and add available sections to the draft selection.
3. Review selected sections, schedules, and the active credit-load summary; remove or replace drafts as needed.
4. Open final review. The application rechecks credit limits and schedule conflicts and displays any prerequisite or availability problem returned by the API.
5. Submit the valid selection. Draft registrations move to `pending` for advisor review.
6. Monitor advisor decisions, comments, and waiting-list positions from the dashboard; full sections can be joined or left from the waiting-list workflow.
7. Review approved current-semester courses in the weekly timetable or switch to the detailed list view for section, instructor, room, and meeting-time information.


## Role-Aware Access and Advisor Review

- CoursePilot uses one login page for all existing accounts and routes the authenticated user by role.
- Public self-registration creates `student` accounts only; staff and administrative roles are not selectable from the public sign-up form.
- Only accounts with `account_status = active` can sign in or continue using an existing access token.
- Students open the student registration dashboard and can jump directly to the course catalogue from the primary dashboard action.
- Advisors open a dedicated review queue containing only registration requests assigned to their advisor profile. They can inspect course, prerequisite, credit-load, and schedule information before approving or rejecting a pending request.
- Rejections require a reason. Advisor decisions continue to use the backend notification and audit-log workflow.
- Department and system administrator accounts are kept out of the student workspace; their management interface is handled by the department-administration feature.


## Main API Endpoints

GET /api/courses

GET /api/courses/{course_id}/availability

GET /api/courses/{course_id}/prerequisite-validation

GET /api/registration-periods/current

GET /api/selections

POST /api/selections

GET /api/selections/credit-validation

POST /api/selections/credit-validation

GET /api/selections/schedule-conflict-validation

POST /api/selections/schedule-conflict-validation

DELETE /api/selections/{course_id}

POST /api/registrations/submit

GET /api/registrations

POST /api/registrations/{registration_id}/drop

GET /api/waitlists

POST /api/waitlists

DELETE /api/waitlists/{course_id}

GET /api/advisor/registration-requests

GET /api/advisor/registration-requests/{request_id}

POST /api/advisor/registration-requests/{request_id}/decision

Optional query parameters:

- search
- department
- semester
- level
- is_mandatory
- available_only

Example:

GET /api/courses?search=CSE&department=CSE&available_only=true

## Backend Local Setup

From the backend folder:

    .\.venv\Scripts\python.exe -m pip install -r requirements.txt
    .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload

Open:

- http://127.0.0.1:8000/health
- http://127.0.0.1:8000/api/database/status
- http://127.0.0.1:8000/api/courses
- http://127.0.0.1:8000/api/courses/cse-101/availability
- http://127.0.0.1:8000/api/courses/cse-201/prerequisite-validation
- http://127.0.0.1:8000/api/registration-periods/current
- http://127.0.0.1:8000/api/selections
- http://127.0.0.1:8000/api/registrations/submit
- http://127.0.0.1:8000/api/registrations
- http://127.0.0.1:8000/api/waitlists
- http://127.0.0.1:8000/docs

## Frontend Local Setup

From the frontend folder:

    npm install
    npm run dev

Run frontend tests and a production build:

    npm test
    npm run build

Open:

- http://localhost:5173

## Database

The backend uses SQLAlchemy for database access. For local development, the app uses a SQLite database file. The database tables are created automatically when the backend starts, and development seed data is inserted if the tables are empty.

The same SQLAlchemy structure can later connect to PostgreSQL by changing DATABASE_URL.

## Current Backend Structure

- backend/app/database.py
- backend/app/models/completed_course.py
- backend/app/models/course.py
- backend/app/models/course_prerequisite.py
- backend/app/models/registration_period.py
- backend/app/models/user.py
- backend/app/schemas/course.py
- backend/app/schemas/registration_period.py
- backend/app/repositories/course_repository.py
- backend/app/repositories/registration_period_status_repository.py
- backend/app/repositories/credit_repository.py
- backend/app/repositories/prerequisite_repository.py
- backend/app/repositories/course_drop_repository.py
- backend/app/repositories/registration_submission_repository.py
- backend/app/repositories/registration_status_repository.py
- backend/app/repositories/schedule_conflict_repository.py
- backend/app/repositories/seat_allocation_repository.py
- backend/app/repositories/section_transaction.py
- backend/app/repositories/selection_repository.py
- backend/app/repositories/waitlist_promotion_repository.py
- backend/app/repositories/waitlist_repository.py
- backend/app/schemas/registration_submission.py
- backend/app/schemas/registration_status.py
- backend/app/schemas/schedule_conflict.py
- backend/app/schemas/seat_allocation.py
- backend/app/schemas/waitlist.py
- backend/app/schemas/waitlist_promotion.py
- backend/app/api/routes/courses.py
- backend/app/api/routes/registration_periods.py
- backend/app/api/routes/registrations.py
- backend/app/api/routes/selections.py
- backend/app/api/routes/waitlists.py
- backend/app/seed_data.py
- backend/app/main.py

## Current Frontend Structure

- frontend/src/pages/StudentDashboardPage/
- frontend/src/pages/AdvisorDashboardPage/
- frontend/src/pages/RoleWorkspacePage/
- frontend/src/components/CourseCard/
- frontend/src/components/CourseDetailsModal/
- frontend/src/components/CourseFilters/
- frontend/src/components/CourseStats/
- frontend/src/components/RegistrationWorkspace/
- frontend/src/components/RegistrationReviewModal/
- frontend/src/components/RegistrationStatusPanel/
- frontend/src/components/ApprovedSchedule/
- frontend/src/components/WaitlistPanel/
- frontend/src/services/apiClient.ts
- frontend/src/services/advisorApi.ts
- frontend/src/services/courseApi.ts
- frontend/src/services/dashboardApi.ts
- frontend/src/services/selectionApi.ts
- frontend/src/services/waitlistApi.ts
- frontend/src/types/advisor.ts
- frontend/src/types/course.ts
- frontend/src/types/dashboard.ts
- frontend/src/types/selection.ts
- frontend/src/types/waitlist.ts

## Notes

Local database files are ignored by Git and should not be committed.
## Department administration

CoursePilot provides role-aware administration for `department-admin` and
`system-admin` accounts.

- Students continue to self-register with the public student sign-up.
- Staff roles cannot be selected during public registration.
- Administrators can provision advisor accounts with a department and employee
  number, activate or suspend access, search accounts, and review account
  status from the administration workspace.
- Department administrators can manage advisor access. System administrators
  can additionally provision department administrators and manage non-system
  accounts.
- Suspended, pending, and rejected accounts cannot authenticate or reuse an
  existing access token.

For a fresh deployment, the first system administrator can be created without
hard-coded credentials by setting these backend environment variables and
redeploying once:

```env
BOOTSTRAP_SYSTEM_ADMIN_NAME=System Administrator
BOOTSTRAP_SYSTEM_ADMIN_EMAIL=admin@example.edu
BOOTSTRAP_SYSTEM_ADMIN_PASSWORD=replace-with-a-strong-unique-password
```

The bootstrap is idempotent: if that email already exists, CoursePilot does not
change its role or password. Keep the password in the deployment environment,
not in source control.

## Notifications and audit activity

CoursePilot exposes account-scoped notifications at `/api/notifications` and a
system-administrator audit feed at `/api/admin/audit-logs`.

- Every authenticated user can view only their own notifications.
- Notifications can be marked read individually or all at once from the shared
  top-bar notification center.
- Advisor decisions, waitlist promotions, course drops, student profile linking,
  staff provisioning, access changes, and final registration submission produce
  persisted activity records where applicable.
- Final registration submission notifies the assigned advisor that a review is
  waiting.
- System administrators can review recent audit events from the administration
  workspace. Department administrators cannot read the global audit feed.

## Backend and API Regression Tests

Run the complete backend suite from `backend/` with:

    python -m unittest discover -s tests

The suite uses temporary SQLite databases for API integration tests, so it does
not modify the local development database or require the deployed PostgreSQL
instance. It covers authentication and role boundaries, core registration and
waitlist workflows, advisor/admin APIs, notification and audit access, shared
error contracts, persistence constraints, and a cross-route API surface
regression matrix. See `backend/TESTING.md` for focused and verbose commands.
