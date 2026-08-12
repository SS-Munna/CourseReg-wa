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
Eligible students can join or leave full-section waiting lists and see their
live first-come, first-served queue positions. When a seat is released, the
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

React Student Dashboard -> frontend API services -> FastAPI endpoints -> SQLAlchemy repositories -> registration and course tables -> shared JSON responses -> dashboard summaries and course cards

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
- frontend/src/components/CourseCard/
- frontend/src/components/CourseDetailsModal/
- frontend/src/components/CourseFilters/
- frontend/src/components/CourseStats/
- frontend/src/services/courseApi.ts
- frontend/src/services/dashboardApi.ts
- frontend/src/types/course.ts
- frontend/src/types/dashboard.ts

## Notes

Local database files are ignored by Git and should not be committed.
