import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import ApprovedSchedule from '../components/ApprovedSchedule'
import type { StudentRegistration } from '../types/dashboard'

const approvedRegistration: StudentRegistration = {
  registration_id: 'registration-approved-1',
  registration_status: 'approved',
  submitted_at: '2026-08-10T09:00:00Z',
  reviewed_at: '2026-08-11T09:00:00Z',
  reviewed_by_advisor_id: 'advisor-1',
  advisor_comment: 'Approved for the semester.',
  updated_at: '2026-08-11T09:00:00Z',
  course: {
    course_id: 'cse-201',
    code: 'CSE 201',
    title: 'Data Structures',
    department: 'CSE',
    semester: 'Fall 2026',
    instructor: 'Dr. Ahmed',
    credits: 3,
    capacity: 35,
    available_seats: 8,
    is_mandatory: true,
    section: 'A',
    schedule: [
      {
        day: 'Monday',
        start_time: '09:00',
        end_time: '10:30',
        room: 'CSE-301',
      },
    ],
  },
  drop_eligibility: {
    eligible: true,
    drop_deadline: '2026-10-15',
    reason: 'eligible',
    message: 'This approved registration can be dropped.',
  },
}

const pendingRegistration: StudentRegistration = {
  ...approvedRegistration,
  registration_id: 'registration-pending-1',
  registration_status: 'pending',
  course: {
    ...approvedRegistration.course,
    course_id: 'cse-315',
    code: 'CSE 315',
    title: 'Operating Systems',
  },
  drop_eligibility: {
    eligible: false,
    drop_deadline: '2026-10-15',
    reason: 'registration_not_approved',
    message: 'Only an approved registration can be dropped.',
  },
}

describe('ApprovedSchedule', () => {
  it('shows only approved current-semester courses in the weekly timetable', () => {
    render(
      <ApprovedSchedule
        registrations={[approvedRegistration, pendingRegistration]}
        loading={false}
        activeSemester="Fall 2026"
      />,
    )

    const schedule = screen.getByRole('region', { name: 'Weekly timetable' })
    const monday = within(schedule).getByText('Monday').closest('article')

    expect(within(monday!).getByText('CSE 201')).toBeVisible()
    expect(within(monday!).getByText('Data Structures')).toBeVisible()
    expect(within(monday!).getByText('09:00–10:30 · CSE-301')).toBeVisible()
    expect(screen.queryByText('Operating Systems')).not.toBeInTheDocument()
  })

  it('switches to a complete approved-course list view', async () => {
    const user = userEvent.setup()

    render(
      <ApprovedSchedule
        registrations={[approvedRegistration]}
        loading={false}
        activeSemester="Fall 2026"
      />,
    )

    await user.click(screen.getByRole('button', { name: 'List view' }))

    expect(screen.getByText('Data Structures')).toBeVisible()
    expect(screen.getByText('Approved')).toBeVisible()
    expect(
      screen.getByText('Monday · 09:00–10:30 · CSE-301'),
    ).toBeVisible()
  })

  it('keeps approved courses visible when a meeting time is not announced', () => {
    const unscheduledRegistration: StudentRegistration = {
      ...approvedRegistration,
      registration_id: 'registration-approved-2',
      course: {
        ...approvedRegistration.course,
        course_id: 'mat-101',
        code: 'MAT 101',
        title: 'Calculus I',
        instructor: 'Dr. Chowdhury',
        schedule: [],
      },
    }

    render(
      <ApprovedSchedule
        registrations={[unscheduledRegistration]}
        loading={false}
        activeSemester="Fall 2026"
      />,
    )

    expect(screen.getByText('Schedule not announced')).toBeVisible()
    expect(screen.getByText('MAT 101')).toBeVisible()
  })

  it('shows a clear empty state before any course is approved', () => {
    render(
      <ApprovedSchedule
        registrations={[pendingRegistration]}
        loading={false}
        activeSemester="Fall 2026"
      />,
    )

    expect(screen.getByText('No approved courses yet')).toBeVisible()
  })
})
