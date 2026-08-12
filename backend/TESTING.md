# Backend and API test suite

CoursePilot uses Python's built-in `unittest` runner together with FastAPI's
`TestClient`. The suite is self-contained: database-backed API tests create
temporary SQLite databases and do not require the local development database
or the deployed PostgreSQL database.

## Run the complete suite

From `backend/` on Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

If the virtual environment is already activated:

```powershell
python -m unittest discover -s tests
```

For verbose test names:

```powershell
python -m unittest discover -s tests -v
```

## Run the API regression suite only

```powershell
python -m unittest tests.test_api_regression_suite -v
```

## Regression coverage

The suite covers the main backend risk areas, including:

- JWT registration, login, current-user lookup, invalid tokens, deleted users,
  and inactive-account enforcement;
- role boundaries for students, advisors, department administrators, and
  system administrators;
- course catalogue, registration period, draft selection, final submission,
  advisor review, waitlist, registration status/drop, notifications, audit
  logging, and department-administration APIs;
- prerequisite, credit-load, schedule-conflict, safe-seat, and automatic
  waitlist-promotion business rules;
- shared success/error envelopes and request-validation errors;
- database constraints, schema migrations, seed data, and persistence error
  handling;
- a cross-route API surface regression test so critical endpoints are not
  accidentally removed or left without authentication/error documentation.

A change is ready to merge only when the complete backend suite exits with
status code `0`. Frontend tests, lint, and the production build are verified
separately from `frontend/`.
