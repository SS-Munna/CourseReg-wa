# Final Security and Regression Review

Issue #42 is the final release gate for CoursePilot. The review focuses on role isolation, account-state enforcement, critical registration workflows, and responsive presentation.

## Security boundaries verified

- Public self-registration creates student accounts only; privileged roles cannot be self-assigned.
- Pending, suspended, and rejected accounts cannot reuse authenticated routes.
- Students cannot enter advisor or administration APIs.
- Advisors cannot enter student selection, administration, or global audit APIs.
- Department administrators cannot enter student/advisor workflows, create higher-privilege access, or read the global audit history.
- System administrators retain administration access but do not receive student registration permissions.
- Global audit history remains system-admin only.
- Authentication failures use the shared error contract without exposing password hashes or stored credential material.

## Final UI regression scope

- One shared login is used for every role; public account creation remains explicitly student-only.
- Student, advisor, department-admin, and system-admin accounts receive separate workspace navigation.
- Only the selected workspace tool is rendered in the main content area in the authenticated application shell.
- System-level navigation is not shown to department administrators.
- The login information panel is compact on desktop and removed from phone layouts.
- The authenticated sidebar becomes a drawer on narrow screens.

## Release checks

Run before final merge:

```bash
cd backend
python -m unittest discover -s tests

cd ../frontend
npm test
npm run lint
npm run build
```

Also verify `git diff --check` from the repository root.

## Recommended manual production smoke test

Use one active account for each role after deployment:

1. Student: sign in, browse courses, add a draft selection, review status/waitlist/timetable.
2. Advisor: sign in, open the assigned review queue, inspect one request, and verify decision controls.
3. Department admin: sign in, confirm scoped user/staff tools and absence of system-only setup/audit navigation.
4. System admin: sign in, confirm users/access, staff provisioning, student profile linking, academic setup, and audit history.
5. Suspend or use a pending test account and confirm login/protected access is blocked.
6. Check the login and each role workspace at approximately 375 px, 390 px, 430 px, and 768 px widths for overflow or clipped controls.
