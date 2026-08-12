import { render, screen, within } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { AuthProvider } from '../context/AuthContext'
import StudentDashboardPage from '../pages/StudentDashboardPage'
import { fetchCourses } from '../services/courseApi'
import {
  ApiRequestError,
  fetchCurrentRegistrationPeriod,
  fetchRegistrationOverview,
} from '../services/dashboardApi'
import type { Course } from '../types/course'

vi.mock('../services/courseApi', () => ({
  fetchCourses: vi.fn(),
  fetchSectionAvailability: vi.fn(),
}))

vi.mock('../services/dashboardApi', async () => {
  const actual = await vi.importActual<typeof import('../services/dashboardApi')>(
    '../services/dashboardApi',
  )

  return {
    ...actual,
    fetchCurrentRegistrationPeriod: vi.fn(),
    fetchRegistrationOverview: vi.fn(),
  }
})

const course: Course = {
  course_id: 'cse-315-a',
  code: 'CSE 315',
  title: 'Operating Systems',
  department: 'CSE',
  semester: 'Fall 2026',
  instructor: 'Dr. Karim',
  credits: 3,
  capacity: 35,
  available_seats: 9,
  is_mandatory: true,
  level: 'Undergraduate',
  section: 'A',
}

describe('StudentDashboardPage', () => {
  beforeEach(() => {
    localStorage.setItem(
      'coursepilot_user',
      JSON.stringify({
        id: 'student-user',
        name: 'Samira Khan',
        email: 'samira@example.com',
        role: 'student',
      }),
    )
    localStorage.setItem('coursepilot_token', 'student-token')

    vi.mocked(fetchCourses).mockResolvedValue([course])
    vi.mocked(fetchCurrentRegistrationPeriod).mockResolvedValue({
      effective_status: 'open',
      registration_enabled: true,
      semester: 'Fall 2026',
      opening_time: '2026-08-01T00:00:00Z',
      closing_time: '2026-09-15T23:59:00Z',
      drop_deadline: '2026-10-15',
      minimum_credit: 9,
      maximum_credit: 18,
      message: 'Course registration is open for this semester.',
    })
    vi.mocked(fetchRegistrationOverview).mockResolvedValue({
      registrations: [
        {
          registration_id: 'registration-1',
          registration_status: 'pending',
          course,
        },
      ],
      waitlist_entries: [{ registration_status: 'waitlisted' }],
    })
  })

  it('renders the authenticated dashboard, summary, period, and catalogue', async () => {
    render(
      <AuthProvider>
        <StudentDashboardPage />
      </AuthProvider>,
    )

    expect(await screen.findByText('Welcome back, Samira')).toBeVisible()
    expect(await screen.findByText('Registration open')).toBeVisible()
    expect(await screen.findByText('Operating Systems')).toBeVisible()

    const pendingCard = screen.getByText('Pending review').closest('article')
    const waitlistCard = screen.getByText('Waitlisted').closest('article')
    const creditsCard = screen.getByText('Selected credits').closest('article')

    expect(within(pendingCard!).getByText('1')).toBeVisible()
    expect(within(waitlistCard!).getByText('1')).toBeVisible()
    expect(within(creditsCard!).getByText('3')).toBeVisible()
    expect(fetchCurrentRegistrationPeriod).toHaveBeenCalledWith('student-token')
  })

  it('keeps course browsing available while a student profile is being linked', async () => {
    vi.mocked(fetchRegistrationOverview).mockRejectedValue(
      new ApiRequestError(
        'The authenticated account has no student profile.',
        'STUDENT_PROFILE_NOT_FOUND',
        404,
      ),
    )

    render(
      <AuthProvider>
        <StudentDashboardPage />
      </AuthProvider>,
    )

    expect(
      await screen.findByText(/the academic profile is still being set up/i),
    ).toBeVisible()
    expect(await screen.findByText('Operating Systems')).toBeVisible()
    expect(screen.getByRole('button', { name: 'View section details' })).toBeEnabled()
  })
})
