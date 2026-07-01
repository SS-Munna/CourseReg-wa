# CoursePilot Backend

This folder contains the base FastAPI backend setup for CoursePilot.

## Setup

Create a virtual environment:

py -m venv .venv

Install dependencies:

.\.venv\Scripts\python.exe -m pip install -r requirements.txt

Run the backend server:

.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload

## Local URLs

- API root: http://127.0.0.1:8000
- Health check: http://127.0.0.1:8000/health
- API docs: http://127.0.0.1:8000/docs
