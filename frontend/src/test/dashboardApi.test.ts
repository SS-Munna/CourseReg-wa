import { afterEach, describe, expect, it, vi } from 'vitest'

import {
  ApiRequestError,
  fetchRegistrationOverview,
  summarizeRegistrations,
} from '../services/dashboardApi'
import type { Course } from '../types/course'
import type { RegistrationOverview } from '../types/dashboard'

const course: Course = {
  course_id: 'cse-201-a',
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
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('dashboard API', () => {
  it('summarizes every visible registration state and active credits', () => {
    const baseRegistration = {
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
    const waitlistCourse = {
      ...course,
      available_seats: 0,
    }
    const overview: RegistrationOverview = {
      registrations: [
        { ...baseRegistration, registration_id: '1', registration_status: 'draft' },
        { ...baseRegistration, registration_id: '2', registration_status: 'pending' },
        { ...baseRegistration, registration_id: '3', registration_status: 'approved' },
        { ...baseRegistration, registration_id: '4', registration_status: 'rejected' },
        { ...baseRegistration, registration_id: '5', registration_status: 'dropped' },
      ],
      waitlist_entries: [
        {
          waitlist_entry_id: 'waitlist-1',
          waitlist_status: 'active',
          registration_status: 'waitlisted',
          joined_at: '2026-08-12T11:00:00Z',
          queue_position: 1,
          total_waiting: 2,
          course: waitlistCourse,
        },
        {
          waitlist_entry_id: 'waitlist-2',
          waitlist_status: 'active',
          registration_status: 'waitlisted',
          joined_at: '2026-08-12T11:01:00Z',
          queue_position: 2,
          total_waiting: 2,
          course: waitlistCourse,
        },
      ],
    }

    expect(summarizeRegistrations(overview)).toEqual({
      selected: 1,
      pending: 1,
      approved: 1,
      rejected: 1,
      waitlisted: 2,
      selectedCredits: 9,
    })
  })

  it('keeps the shared backend error code for profile-aware handling', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            success: false,
            error: {
              code: 'STUDENT_PROFILE_NOT_FOUND',
              message: 'The authenticated account has no student profile.',
            },
          }),
          {
            status: 404,
            headers: { 'Content-Type': 'application/json' },
          },
        ),
      ),
    )

    const request = fetchRegistrationOverview('student-token')

    await expect(request).rejects.toBeInstanceOf(ApiRequestError)
    await expect(request).rejects.toMatchObject({
      code: 'STUDENT_PROFILE_NOT_FOUND',
      status: 404,
    })
  })
})
