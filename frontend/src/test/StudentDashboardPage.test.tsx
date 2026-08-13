import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { AuthProvider } from '../context/AuthContext'
import StudentDashboardPage from '../pages/StudentDashboardPage'
import { fetchCourses } from '../services/courseApi'
import {
  ApiRequestError,
  fetchCurrentRegistrationPeriod,
  fetchRegistrationOverview,
} from '../services/dashboardApi'
import {
  addDraftSelection,
  fetchDraftSelections,
  removeDraftSelection,
  submitRegistration,
  validateFinalCreditLoad,
  validateFinalSchedule,
} from '../services/selectionApi'
import { joinWaitlist, leaveWaitlist } from '../services/waitlistApi'
import type { Course } from '../types/course'
import type {
  CreditLoadValidation,
  DraftSelection,
  ScheduleConflictValidation,
} from '../types/selection'

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

vi.mock('../services/selectionApi', () => ({
  addDraftSelection: vi.fn(),
  fetchDraftSelections: vi.fn(),
  removeDraftSelection: vi.fn(),
  submitRegistration: vi.fn(),
  validateFinalCreditLoad: vi.fn(),
  validateFinalSchedule: vi.fn(),
}))

vi.mock('../services/waitlistApi', () => ({
  joinWaitlist: vi.fn(),
  leaveWaitlist: vi.fn(),
}))

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

const fullCourse: Course = {
  ...course,
  course_id: 'cse-410-a',
  code: 'CSE 410',
  title: 'Distributed Systems',
  capacity: 40,
  available_seats: 0,
}

const pendingRegistration = {
  registration_id: 'registration-1',
  registration_status: 'pending' as const,
  submitted_at: '2026-08-12T10:00:00Z',
  reviewed_at: null,
  reviewed_by_advisor_id: null,
  advisor_comment: null,
  updated_at: '2026-08-12T10:00:00Z',
  course,
  drop_eligibility: {
    eligible: false,
    drop_deadline: '2026-10-15',
    reason: 'registration_not_approved' as const,
    message: 'Only an approved registration can be dropped.',
  },
}

const waitlistEntry = {
  waitlist_entry_id: 'waitlist-1',
  waitlist_status: 'active' as const,
  registration_status: 'waitlisted' as const,
  joined_at: '2026-08-12T10:30:00Z',
  queue_position: 2,
  total_waiting: 5,
  course: fullCourse,
}

const belowMinimumCredit: CreditLoadValidation = {
  selected_credits: 0,
  minimum_credit: 9,
  maximum_credit: 18,
  validation_status: 'below_minimum',
  is_valid: false,
  minimum_shortfall: 9,
  maximum_excess: 0,
  message: 'Final submission requires at least 9 credits.',
}

const validCredit: CreditLoadValidation = {
  selected_credits: 3,
  minimum_credit: 3,
  maximum_credit: 18,
  validation_status: 'within_range',
  is_valid: true,
  minimum_shortfall: 0,
  maximum_excess: 0,
  message: 'The selected credit load is within the allowed range.',
}

const scheduleValidation: ScheduleConflictValidation = {
  has_conflicts: false,
  conflict_count: 0,
  conflicts: [],
  message: 'No schedule conflicts were found.',
}

const draftSelection: DraftSelection = {
  registration_id: 'draft-registration-1',
  registration_status: 'draft',
  course,
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
      registrations: [pendingRegistration],
      waitlist_entries: [waitlistEntry],
    })
    vi.mocked(fetchDraftSelections).mockResolvedValue({
      selections: [],
      creditValidation: belowMinimumCredit,
    })
    vi.mocked(addDraftSelection).mockResolvedValue({
      selection: draftSelection,
      creditValidation: {
        ...belowMinimumCredit,
        selected_credits: 3,
        minimum_shortfall: 6,
      },
    })
    vi.mocked(removeDraftSelection).mockResolvedValue(belowMinimumCredit)
    vi.mocked(validateFinalCreditLoad).mockResolvedValue(validCredit)
    vi.mocked(validateFinalSchedule).mockResolvedValue(scheduleValidation)
    vi.mocked(submitRegistration).mockResolvedValue({
      registration_status: 'pending',
      submitted_count: 1,
      submitted_at: '2026-08-12T12:00:00Z',
      registrations: [
        {
          ...draftSelection,
          registration_status: 'pending',
          submitted_at: '2026-08-12T12:00:00Z',
        },
      ],
      credit_validation: validCredit,
      schedule_validation: scheduleValidation,
      message: 'Registration submitted for advisor review.',
    })
    vi.mocked(joinWaitlist).mockResolvedValue(waitlistEntry)
    vi.mocked(leaveWaitlist).mockResolvedValue({
      waitlist_entry_id: waitlistEntry.waitlist_entry_id,
      course_id: waitlistEntry.course.course_id,
      waitlist_status: 'removed',
      removed_at: '2026-08-12T11:00:00Z',
      previous_queue_position: 2,
      remaining_waiting: 4,
    })
  })

  it('renders the authenticated dashboard, summary, period, and catalogue', async () => {
    render(
      <AuthProvider>
        <StudentDashboardPage />
      </AuthProvider>,
    )

    expect(await screen.findByText('Welcome back, Samira')).toBeVisible()
    expect(screen.getByRole('button', { name: 'Browse & add courses' })).toBeVisible()
    expect(await screen.findByText('Registration open')).toBeVisible()
    const catalogueSection = await screen.findByRole('region', {
      name: 'Course catalogue',
    })
    expect(within(catalogueSection).getByText('Operating Systems')).toBeVisible()

    const summarySection = await screen.findByRole('region', {
      name: 'Registration summary',
    })
    const pendingCard = within(summarySection)
      .getByText('Pending review')
      .closest('article')
    const waitlistCard = within(summarySection)
      .getByText('Waitlisted')
      .closest('article')
    const creditsCard = within(summarySection)
      .getByText('Selected credits')
      .closest('article')

    expect(within(pendingCard!).getByText('1')).toBeVisible()
    expect(within(waitlistCard!).getByText('1')).toBeVisible()
    expect(within(creditsCard!).getByText('3')).toBeVisible()
    expect(fetchCurrentRegistrationPeriod).toHaveBeenCalledWith('student-token')
  })

  it('keeps course browsing available while a student profile is being linked', async () => {
    const profileError = new ApiRequestError(
      'The authenticated account has no student profile.',
      'STUDENT_PROFILE_NOT_FOUND',
      404,
    )
    vi.mocked(fetchRegistrationOverview).mockRejectedValue(profileError)
    vi.mocked(fetchDraftSelections).mockRejectedValue(profileError)

    render(
      <AuthProvider>
        <StudentDashboardPage />
      </AuthProvider>,
    )

    expect(
      await screen.findByText(/the academic profile is still being set up/i),
    ).toBeVisible()
    const catalogueSection = await screen.findByRole('region', {
      name: 'Course catalogue',
    })
    expect(within(catalogueSection).getByText('Operating Systems')).toBeVisible()
    expect(screen.getByRole('button', { name: 'View section details' })).toBeEnabled()
    expect(screen.getByRole('button', { name: 'Add to selection' })).toBeDisabled()
  })

  it('adds an available course as a draft and updates the selection workspace', async () => {
    const user = userEvent.setup()

    render(
      <AuthProvider>
        <StudentDashboardPage />
      </AuthProvider>,
    )

    const addButton = await screen.findByRole('button', {
      name: 'Add to selection',
    })
    await waitFor(() => expect(addButton).toBeEnabled())
    await user.click(addButton)

    expect(addDraftSelection).toHaveBeenCalledWith(
      'student-token',
      'cse-315-a',
    )
    expect(await screen.findByRole('button', { name: 'Selected' })).toBeDisabled()
    expect(
      screen.getByRole('button', {
        name: 'Remove CSE 315 from selection',
      }),
    ).toBeEnabled()
    expect(screen.getByText(/was added as a draft/i)).toBeVisible()
  })

  it('removes an owned draft course from the registration workspace', async () => {
    const user = userEvent.setup()
    vi.mocked(fetchDraftSelections).mockResolvedValue({
      selections: [draftSelection],
      creditValidation: validCredit,
    })

    render(
      <AuthProvider>
        <StudentDashboardPage />
      </AuthProvider>,
    )

    const removeButton = await screen.findByRole('button', {
      name: 'Remove CSE 315 from selection',
    })
    await user.click(removeButton)

    expect(removeDraftSelection).toHaveBeenCalledWith(
      'student-token',
      'cse-315-a',
    )
    await waitFor(() => {
      expect(
        screen.queryByRole('button', {
          name: 'Remove CSE 315 from selection',
        }),
      ).not.toBeInTheDocument()
    })
    expect(screen.getByText(/was removed from your draft selection/i)).toBeVisible()
  })

  it('keeps registration actions locked outside the open period', async () => {
    vi.mocked(fetchCurrentRegistrationPeriod).mockResolvedValue({
      effective_status: 'closed',
      registration_enabled: false,
      semester: 'Fall 2026',
      opening_time: '2026-06-01T00:00:00Z',
      closing_time: '2026-07-01T00:00:00Z',
      drop_deadline: '2026-08-01',
      minimum_credit: 9,
      maximum_credit: 18,
      message: 'Course registration is closed for this semester.',
    })

    render(
      <AuthProvider>
        <StudentDashboardPage />
      </AuthProvider>,
    )

    expect(await screen.findByText('Registration closed')).toBeVisible()
    expect(
      await screen.findByRole('button', { name: 'Add to selection' }),
    ).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Review registration' })).toBeDisabled()
  })

  it('validates, reviews, and submits draft courses for advisor review', async () => {
    const user = userEvent.setup()
    vi.mocked(fetchDraftSelections).mockResolvedValue({
      selections: [draftSelection],
      creditValidation: validCredit,
    })

    render(
      <AuthProvider>
        <StudentDashboardPage />
      </AuthProvider>,
    )

    const reviewButton = await screen.findByRole('button', {
      name: 'Review registration',
    })
    await waitFor(() => expect(reviewButton).toBeEnabled())
    await user.click(reviewButton)

    expect(validateFinalCreditLoad).toHaveBeenCalledWith('student-token')
    expect(validateFinalSchedule).toHaveBeenCalledWith('student-token')
    expect(
      await screen.findByRole('dialog', { name: 'Review your registration' }),
    ).toBeVisible()

    await user.click(
      screen.getByRole('button', { name: 'Submit for advisor review' }),
    )

    await waitFor(() => {
      expect(submitRegistration).toHaveBeenCalledWith('student-token')
    })
    expect(
      await screen.findByText(/1 course submitted for advisor review/i),
    ).toBeVisible()
  })

  it('shows registration outcomes, advisor comments, and live waitlist position', async () => {
    vi.mocked(fetchRegistrationOverview).mockResolvedValue({
      registrations: [
        {
          ...pendingRegistration,
          registration_id: 'registration-rejected',
          registration_status: 'rejected',
          reviewed_at: '2026-08-12T12:30:00Z',
          advisor_comment: 'Please choose the section that fits your study plan.',
        },
      ],
      waitlist_entries: [waitlistEntry],
    })

    render(
      <AuthProvider>
        <StudentDashboardPage />
      </AuthProvider>,
    )

    const statusSection = await screen.findByRole('region', {
      name: 'Registration status',
    })
    expect(within(statusSection).getByText('Rejected')).toBeVisible()
    expect(
      within(statusSection).getByText(
        'Please choose the section that fits your study plan.',
      ),
    ).toBeVisible()
    expect(within(statusSection).getByText(/Position #2 of 5/)).toBeVisible()
    expect(
      screen.getByRole('button', {
        name: 'Leave waiting list for CSE 410',
      }),
    ).toBeEnabled()
  })

  it('joins a full section waitlist and can leave it from the dashboard', async () => {
    const user = userEvent.setup()

    vi.mocked(fetchCourses).mockResolvedValue([fullCourse])
    vi.mocked(fetchRegistrationOverview)
      .mockResolvedValueOnce({
        registrations: [],
        waitlist_entries: [],
      })
      .mockResolvedValueOnce({
        registrations: [],
        waitlist_entries: [waitlistEntry],
      })
      .mockResolvedValueOnce({
        registrations: [],
        waitlist_entries: [],
      })

    render(
      <AuthProvider>
        <StudentDashboardPage />
      </AuthProvider>,
    )

    const joinButton = await screen.findByRole('button', {
      name: 'Join waitlist',
    })
    await waitFor(() => expect(joinButton).toBeEnabled())
    await user.click(joinButton)

    expect(joinWaitlist).toHaveBeenCalledWith('student-token', 'cse-410-a')
    expect(await screen.findByText('#2')).toBeVisible()

    const leaveButton = screen.getByRole('button', {
      name: 'Leave waiting list for CSE 410',
    })
    await user.click(leaveButton)

    expect(leaveWaitlist).toHaveBeenCalledWith('student-token', 'cse-410-a')
    await waitFor(() => {
      expect(
        screen.queryByRole('button', {
          name: 'Leave waiting list for CSE 410',
        }),
      ).not.toBeInTheDocument()
    })
  })

  it('shows missing prerequisite details returned by the backend', async () => {
    const user = userEvent.setup()
    vi.mocked(addDraftSelection).mockRejectedValue(
      new ApiRequestError(
        'The course section cannot be selected because prerequisite requirements are not met.',
        'PREREQUISITES_NOT_MET',
        422,
        {
          missing_prerequisites: [
            { code: 'CSE 201', minimum_grade: 'C' },
          ],
        },
      ),
    )

    render(
      <AuthProvider>
        <StudentDashboardPage />
      </AuthProvider>,
    )

    const addButton = await screen.findByRole('button', {
      name: 'Add to selection',
    })
    await waitFor(() => expect(addButton).toBeEnabled())
    await user.click(addButton)

    expect(
      await screen.findByText(/Missing: CSE 201 \(minimum C\)/i),
    ).toBeVisible()
  })
})
