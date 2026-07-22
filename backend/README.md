# CoursePilot Backend

This folder contains the FastAPI backend setup for CoursePilot.

The backend provides REST API endpoints for the CoursePilot frontend and connects to AWS DynamoDB using `boto3`.

## Setup

Create a virtual environment:

```powershell
py -m venv .venv
```

Install dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Run the backend server:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

## Local URLs

- API root: http://127.0.0.1:8000
- Health check: http://127.0.0.1:8000/health
- Database status: http://127.0.0.1:8000/api/database/status
- API docs: http://127.0.0.1:8000/docs

## Environment Configuration

The backend uses environment variables for application and DynamoDB configuration.

Example values are provided in `.env.example`:

```text
APP_NAME=CoursePilot API
ENVIRONMENT=development
ALLOWED_ORIGINS=http://localhost:5173

AWS_REGION=us-east-1
DYNAMODB_COURSES_TABLE=CoursePilotCourses
```

Do not commit real AWS access keys, secret keys, session tokens, or a real `.env` file to GitHub.

## DynamoDB Table Setup

The backend includes a setup script for creating the DynamoDB course table.

To preview the table setup without creating any table, run:

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.create_tables --dry-run
```

To create the course table in DynamoDB, make sure AWS credentials are configured locally, then run:

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.create_tables
```

The setup script creates the `CoursePilotCourses` table with `course_id` as the partition key.

## DynamoDB Seed Data

The backend includes a seed script for loading sample course records into DynamoDB.

The seed data includes courses from different departments, semesters, instructors, capacities, available-seat values, prerequisite examples, and schedule information.

To validate the sample course records without writing to DynamoDB, run:

```powershell
cd backend
.\.venv\Scripts\python.exe -c "from app.seed_courses import get_validated_courses; print(len(get_validated_courses()), 'seed courses validated successfully')"
```

To load the sample course records into DynamoDB, make sure the `CoursePilotCourses` table exists and AWS credentials are configured locally, then run:

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.seed_courses
```

The seed script uses the `DYNAMODB_COURSES_TABLE` environment variable to identify the course table.

Do not commit AWS access keys, secret keys, session tokens, or a real `.env` file to GitHub.

## Current Backend Endpoints

| Endpoint | Purpose |
| --- | --- |
| `/` | API root information |
| `/health` | Backend health check |
| `/api/database/status` | DynamoDB configuration status |
| `/docs` | FastAPI Swagger documentation |