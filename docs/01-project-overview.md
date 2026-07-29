# Project Overview

CoursePilot is a course registration and course catalogue system for students.

The current implementation focuses on an end-to-end course catalogue feature. Students can browse courses, search courses, filter by department or semester, and view available seats.

## Architecture

React frontend -> FastAPI backend -> SQLAlchemy repository layer -> relational database tables

## Database Direction

The project uses a SQLAlchemy-based relational database layer. SQLite is used for local development and demonstration. The same database layer can later be connected to PostgreSQL through DATABASE_URL.
