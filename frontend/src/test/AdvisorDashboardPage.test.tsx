import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { AuthProvider } from '../context/AuthContext'
import AdvisorDashboardPage from '../pages/AdvisorDashboardPage'
import {
  fetchAdvisorRequest,
  fetchAdvisorRequests,
  submitAdvisorDecision,
} from '../services/advisorApi'
import type {
  AdvisorRegistrationRequestDetails,
  AdvisorRegistrationRequestSummary,
} from '../types/advisor'

vi.mock('../services/advisorApi', () => ({
  fetchAdvisorRequests: vi.fn(),
  fetchAdvisorRequest: vi.fn(),
  submitAdvisorDecision: vi.fn(),
}))

const requestSummary: AdvisorRegistrationRequestSummary = {
  request_id: 'request-1',
  request_status: 'pending',
  submitted_at: '2026-08-12T10:00:00Z',
  reviewed_at: null,
  advisor_comment: null,
  student: {
    student_id: 'student-1',
    student_number: 'STU-001',
    full_name: 'Samira Rahman',
    email: 'samira@example.com',
    program_code: 'BSC-CSE',
    program_name: 'BSc in CSE',
    current_trimester: 4,
    academic_status: 'active',
  },
  course_count: 1,
  total_credits: 3,
  courses: [
    {
      registration_id: 'registration-1',
      course_id: 'cse-201',
      code: 'CSE 201',
      title: 'Data Structures',
      semester: 'Fall 2026',
      section: 'A',
      credits: 3,
    },
  ],
}

const requestDetails: AdvisorRegistrationRequestDetails = {
  ...requestSummary,
  reviewed_by_advisor_id: null,
  courses: [
    {
      registration_id: 'registration-1',
      registration_status: 'pending',
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
      prerequisite_validation: {
        course_id: 'cse-201',
        code: 'CSE 201',
        eligible: true,
        requirements: [],
        missing_prerequisites: [],
      },
    },
  ],
  credit_validation: {
    selected_credits: 3,
    minimum_credit: 3,
    maximum_credit: 18,
    validation_status: 'within_range',
    is_valid: true,
    minimum_shortfall: 0,
    maximum_excess: 0,
    message: 'Credit load is within the allowed range.',
  },
  schedule_validation: {
    has_conflicts: false,
    conflict_count: 0,
    conflicts: [],
    message: 'No schedule conflicts were found.',
  },
  waitlist_entries: [],
}

beforeEach(() => {
  localStorage.setItem(
    'coursepilot_user',
    JSON.stringify({
      id: 'advisor-user-1',
      name: 'Dr. Nadia',
      email: 'nadia@example.com',
      role: 'advisor',
    }),
  )
  localStorage.setItem('coursepilot_token', 'advisor-token')

  vi.mocked(fetchAdvisorRequests).mockResolvedValue({
    requests: [requestSummary],
    pagination: {
      page: 1,
      page_size: 20,
      total_items: 1,
      total_pages: 1,
    },
  })
  vi.mocked(fetchAdvisorRequest).mockResolvedValue(requestDetails)
  vi.mocked(submitAdvisorDecision).mockResolvedValue({
    request_id: 'request-1',
    request_status: 'approved',
    registration_ids: ['registration-1'],
    reviewed_at: '2026-08-13T00:00:00Z',
    reviewed_by_advisor_id: 'advisor-1',
    advisor_comment: 'Approved.',
    notification_id: 'notification-1',
    audit_log_id: 'audit-1',
    message: 'The registration request was approved.',
  })
})

describe('AdvisorDashboardPage', () => {
  it('shows assigned registration requests and loads review details', async () => {
    const user = userEvent.setup()

    render(
      <AuthProvider>
        <AdvisorDashboardPage />
      </AuthProvider>,
    )

    expect(await screen.findByText('Samira Rahman')).toBeVisible()
    expect(screen.getByText('STU-001')).toBeVisible()
    expect(screen.getByText('CSE 201 · A')).toBeVisible()

    await user.click(screen.getByRole('button', { name: 'Review request' }))

    expect(await screen.findByText('Credit load is within the allowed range.')).toBeVisible()
    expect(screen.getByText('No schedule conflicts were found.')).toBeVisible()
    expect(screen.getByText('Prerequisites met')).toBeVisible()
  })

  it('requires a reason before rejecting a request', async () => {
    const user = userEvent.setup()

    render(
      <AuthProvider>
        <AdvisorDashboardPage />
      </AuthProvider>,
    )

    await user.click(await screen.findByRole('button', { name: 'Review request' }))
    await screen.findByRole('button', { name: 'Reject request' })

    await user.click(screen.getByRole('button', { name: 'Reject request' }))

    expect(
      screen.getByText('Add a reason before rejecting this request.'),
    ).toBeVisible()
    expect(submitAdvisorDecision).not.toHaveBeenCalled()
  })

  it('approves a pending request through the advisor API', async () => {
    const user = userEvent.setup()

    render(
      <AuthProvider>
        <AdvisorDashboardPage />
      </AuthProvider>,
    )

    await user.click(await screen.findByRole('button', { name: 'Review request' }))

    const reviewPanel = await screen.findByRole('region', {
      name: 'Registration request for Samira Rahman',
    })

    await user.type(
      within(reviewPanel).getByLabelText('Advisor comment'),
      'Approved.',
    )
    await user.click(
      within(reviewPanel).getByRole('button', { name: 'Approve request' }),
    )

    await waitFor(() => {
      expect(submitAdvisorDecision).toHaveBeenCalledWith(
        'advisor-token',
        'request-1',
        'approved',
        'Approved.',
      )
    })
    expect(await screen.findByText('Decision saved')).toBeVisible()
  })
})
