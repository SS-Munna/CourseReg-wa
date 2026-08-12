# Frontend testing and validation

CoursePilot uses Vitest and Testing Library for frontend regression coverage. Run the complete frontend quality gate from `frontend/`:

```bash
npm test
npm run lint
npm run build
```

## Validation strategy

Client-side validation mirrors the important backend field boundaries so users receive actionable feedback before an API request is sent. The backend remains authoritative and validates every request again.

Current guarded inputs include:

- shared login and student sign-up email, name, and password fields;
- staff provisioning email, password, department, and employee number;
- student academic-profile number and trimester;
- department and program text lengths;
- program credit limits and minimum/maximum ordering;
- advisor rejection comments and existing registration validation flows.

## Test coverage

The frontend suite covers role routing, authentication entry points, student registration flows, approved schedules, advisor review, administration, notifications, API clients, form validation, and error states. Tests should prefer user-visible behavior and accessible queries over implementation details.
