import { afterEach, describe, expect, it, vi } from 'vitest'

import { ApiRequestError } from '../services/apiClient'
import {
  addDraftSelection,
  fetchDraftSelections,
  removeDraftSelection,
  submitRegistration,
  validateFinalCreditLoad,
  validateFinalSchedule,
} from '../services/selectionApi'
import type { Course } from '../types/course'
import type {
  CreditLoadValidation,
  ScheduleConflictValidation,
} from '../types/selection'

const course: Course = {
  course_id: 'cse-315/a',
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

const creditValidation: CreditLoadValidation = {
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

const selection = {
  registration_id: 'registration-1',
  registration_status: 'draft' as const,
  course,
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('selection API', () => {
  it('loads the authenticated draft selection and credit snapshot', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          success: true,
          data: [selection],
          credit_validation: creditValidation,
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    )
    vi.stubGlobal('fetch', fetchMock)

    await expect(fetchDraftSelections('student-token')).resolves.toEqual({
      selections: [selection],
      creditValidation,
    })
    expect(fetchMock).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/api/selections',
      expect.objectContaining({
        method: 'GET',
        headers: { Authorization: 'Bearer student-token' },
      }),
    )
  })

  it('creates and removes an encoded draft section using the backend contract', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            success: true,
            data: selection,
            credit_validation: creditValidation,
          }),
          { status: 201, headers: { 'Content-Type': 'application/json' } },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            success: true,
            data: {
              registration_id: selection.registration_id,
              course_id: course.course_id,
            },
            credit_validation: creditValidation,
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } },
        ),
      )
    vi.stubGlobal('fetch', fetchMock)

    await addDraftSelection('student-token', course.course_id)
    await removeDraftSelection('student-token', course.course_id)

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      'http://127.0.0.1:8000/api/selections',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ course_id: 'cse-315/a' }),
        headers: {
          Authorization: 'Bearer student-token',
          'Content-Type': 'application/json',
        },
      }),
    )
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      'http://127.0.0.1:8000/api/selections/cse-315%2Fa',
      expect.objectContaining({ method: 'DELETE' }),
    )
  })

  it('uses explicit validation endpoints before final submission', async () => {
    const submission = {
      registration_status: 'pending',
      submitted_count: 1,
      submitted_at: '2026-08-12T12:00:00Z',
      registrations: [],
      credit_validation: creditValidation,
      schedule_validation: scheduleValidation,
      message: 'Submitted.',
    }
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({ success: true, data: creditValidation }),
          { status: 200, headers: { 'Content-Type': 'application/json' } },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({ success: true, data: scheduleValidation }),
          { status: 200, headers: { 'Content-Type': 'application/json' } },
        ),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ success: true, data: submission }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      )
    vi.stubGlobal('fetch', fetchMock)

    await validateFinalCreditLoad('student-token')
    await validateFinalSchedule('student-token')
    await submitRegistration('student-token')

    expect(
      (fetchMock.mock.calls[0][0] as string).endsWith(
        '/api/selections/credit-validation',
      ),
    ).toBe(true)
    expect(
      (fetchMock.mock.calls[1][0] as string).endsWith(
        '/api/selections/schedule-conflict-validation',
      ),
    ).toBe(true)
    expect(
      (fetchMock.mock.calls[2][0] as string).endsWith(
        '/api/registrations/submit',
      ),
    ).toBe(true)
    expect(fetchMock.mock.calls.every((call) => call[1]?.method === 'POST')).toBe(
      true,
    )
  })

  it('preserves backend validation details for actionable UI messages', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            success: false,
            error: {
              code: 'PREREQUISITES_NOT_MET',
              message: 'Prerequisite requirements are not met.',
              details: {
                missing_prerequisites: [{ code: 'CSE 201' }],
              },
            },
          }),
          { status: 422, headers: { 'Content-Type': 'application/json' } },
        ),
      ),
    )

    const request = addDraftSelection('student-token', course.course_id)

    await expect(request).rejects.toBeInstanceOf(ApiRequestError)
    await expect(request).rejects.toMatchObject({
      code: 'PREREQUISITES_NOT_MET',
      status: 422,
      details: {
        missing_prerequisites: [{ code: 'CSE 201' }],
      },
    })
  })
})
