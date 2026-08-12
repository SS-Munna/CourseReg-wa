import { afterEach, describe, expect, it, vi } from 'vitest'

import {
  fetchAdvisorRequest,
  fetchAdvisorRequests,
  submitAdvisorDecision,
} from '../services/advisorApi'

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('advisor API', () => {
  it('loads the authenticated advisor review queue with status and pagination', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          success: true,
          data: [],
          pagination: {
            page: 2,
            page_size: 20,
            total_items: 21,
            total_pages: 2,
          },
        }),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        },
      ),
    )
    vi.stubGlobal('fetch', fetchMock)

    const result = await fetchAdvisorRequests(
      'advisor-token',
      'approved',
      2,
      20,
    )

    expect(result.pagination.total_items).toBe(21)
    expect(fetchMock).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/api/advisor/registration-requests?status=approved&page=2&page_size=20',
      expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({
          Authorization: 'Bearer advisor-token',
        }),
      }),
    )
  })

  it('loads one advisor registration request', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          success: true,
          data: {
            request_id: 'request-1',
          },
        }),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        },
      ),
    )
    vi.stubGlobal('fetch', fetchMock)

    const result = await fetchAdvisorRequest('advisor-token', 'request-1')

    expect(result.request_id).toBe('request-1')
    expect(fetchMock).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/api/advisor/registration-requests/request-1',
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer advisor-token',
        }),
      }),
    )
  })

  it('submits an advisor decision using the backend review contract', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          success: true,
          data: {
            request_id: 'request-1',
            request_status: 'rejected',
            registration_ids: ['registration-1'],
            reviewed_at: '2026-08-13T00:00:00Z',
            reviewed_by_advisor_id: 'advisor-1',
            advisor_comment: 'Revise the selection.',
            notification_id: 'notification-1',
            audit_log_id: 'audit-1',
            message: 'The registration request was rejected.',
          },
        }),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        },
      ),
    )
    vi.stubGlobal('fetch', fetchMock)

    const result = await submitAdvisorDecision(
      'advisor-token',
      'request-1',
      'rejected',
      'Revise the selection.',
    )

    expect(result.request_status).toBe('rejected')
    expect(fetchMock).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/api/advisor/registration-requests/request-1/decision',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          Authorization: 'Bearer advisor-token',
          'Content-Type': 'application/json',
        }),
        body: JSON.stringify({
          decision: 'rejected',
          comment: 'Revise the selection.',
        }),
      }),
    )
  })
})
