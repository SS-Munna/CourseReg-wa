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
    const overview: RegistrationOverview = {
      registrations: [
        { registration_id: '1', registration_status: 'draft', course },
        { registration_id: '2', registration_status: 'pending', course },
        { registration_id: '3', registration_status: 'approved', course },
        { registration_id: '4', registration_status: 'rejected', course },
        { registration_id: '5', registration_status: 'dropped', course },
      ],
      waitlist_entries: [
        { registration_status: 'waitlisted' },
        { registration_status: 'waitlisted' },
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
