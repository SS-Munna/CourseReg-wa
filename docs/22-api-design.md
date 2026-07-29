# API Design

## Overview

The CoursePilot API connects the React frontend with the FastAPI backend and SQLAlchemy database layer.

## Course Catalogue API

GET /api/courses

## Query Parameters

| Parameter | Type | Description |
|---|---|---|
| search | string | Search by course code or title |
| department | string | Filter by department |
| semester | string | Filter by semester |
| is_mandatory | boolean | Filter mandatory or elective courses |
| available_only | boolean | Show only courses with available seats |

## Example Request

GET /api/courses?search=CSE&department=CSE&available_only=true

## Example Response

{
  "success": true,
  "data": [
    {
      "course_id": "cse-101",
      "code": "CSE 101",
      "title": "Introduction to Computer Science",
      "department": "CSE",
      "semester": "Fall 2026",
      "instructor": "Dr. Rahman",
      "credits": 3,
      "capacity": 40,
      "available_seats": 12,
      "is_mandatory": true,
      "level": "Undergraduate",
      "description": "Introductory programming and computing concepts.",
      "prerequisites": [],
      "section": "A",
      "schedule": []
    }
  ]
}

## Status Codes

| Status Code | Meaning |
|---|---|
| 200 | Request successful |
| 422 | Invalid query parameter type |
| 500 | Database operation failed |
