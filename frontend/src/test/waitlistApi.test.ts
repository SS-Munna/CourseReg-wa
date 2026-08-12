import { afterEach, describe, expect, it, vi } from 'vitest'

import { ApiRequestError } from '../services/apiClient'
import { joinWaitlist, leaveWaitlist } from '../services/waitlistApi'

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('waitlist API', () => {
  it('joins a full section and returns the live queue position', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          success: true,
          data: {
            waitlist_entry_id: 'waitlist-1',
            waitlist_status: 'active',
            joined_at: '2026-08-12T10:30:00Z',
            queue_position: 2,
            total_waiting: 5,
            course: {
              course_id: 'cse-410/a',
              code: 'CSE 410',
              title: 'Distributed Systems',
              department: 'CSE',
              semester: 'Fall 2026',
              instructor: 'Dr. Karim',
              credits: 3,
              capacity: 40,
              available_seats: 0,
              is_mandatory: false,
              section: 'A',
            },
          },
        }),
        { status: 201, headers: { 'Content-Type': 'application/json' } },
      ),
    )
    vi.stubGlobal('fetch', fetchMock)

    const result = await joinWaitlist('student-token', 'cse-410/a')

    expect(result.queue_position).toBe(2)
    expect(fetchMock).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/api/waitlists',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ course_id: 'cse-410/a' }),
        headers: {
          Authorization: 'Bearer student-token',
          'Content-Type': 'application/json',
        },
      }),
    )
  })

  it('leaves an encoded waiting-list section using the student token', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          success: true,
          data: {
            waitlist_entry_id: 'waitlist-1',
            course_id: 'cse-410/a',
            waitlist_status: 'removed',
            removed_at: '2026-08-12T11:00:00Z',
            previous_queue_position: 2,
            remaining_waiting: 4,
          },
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    )
    vi.stubGlobal('fetch', fetchMock)

    await leaveWaitlist('student-token', 'cse-410/a')

    expect(fetchMock).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/api/waitlists/cse-410%2Fa',
      expect.objectContaining({
        method: 'DELETE',
        headers: { Authorization: 'Bearer student-token' },
      }),
    )
  })

  it('preserves backend waitlist validation errors for the UI', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            success: false,
            error: {
              code: 'PREREQUISITES_NOT_MET',
              message: 'The waiting list cannot be joined.',
              details: {
                missing_prerequisites: [{ code: 'CSE 301' }],
              },
            },
          }),
          { status: 422, headers: { 'Content-Type': 'application/json' } },
        ),
      ),
    )

    const request = joinWaitlist('student-token', 'cse-410-a')

    await expect(request).rejects.toBeInstanceOf(ApiRequestError)
    await expect(request).rejects.toMatchObject({
      code: 'PREREQUISITES_NOT_MET',
      status: 422,
      details: {
        missing_prerequisites: [{ code: 'CSE 301' }],
      },
    })
  })
})
