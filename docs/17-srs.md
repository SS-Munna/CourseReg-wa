# Software Requirements Specification

## System Overview

CoursePilot provides a student-facing course catalogue and registration workflow.

## Functional Requirements

### Course Catalogue

The system shall allow students to view course offerings.

The system shall allow students to search courses by code or title.

The system shall allow students to filter courses by department, semester, mandatory status, and seat availability.

### Backend API

The system shall provide a REST API endpoint for retrieving course data.

GET /api/courses

### Database

The system shall store course and user data using SQLAlchemy models and relational database tables.

## Non-Functional Requirements

- The frontend should be responsive and easy to use.
- The backend should validate API input and output.
- The backend should keep API routes separate from database-access logic.
- Local database files should not be committed to Git.
