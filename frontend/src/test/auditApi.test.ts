import { afterEach, describe, expect, it, vi } from 'vitest'

import { fetchAuditLogs } from '../services/auditApi'

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('audit log API', () => {
  it('loads paginated audit activity for a system administrator', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          success: true,
          data: [
            {
              id: 'audit-1',
              actor_user_id: 'admin-1',
              actor_name: 'System Admin',
              actor_email: 'admin@example.com',
              action_type: 'account_access_updated',
              entity_type: 'user',
              entity_id: 'user-1',
              action_details: null,
              created_at: '2026-08-13T00:00:00Z',
            },
          ],
          pagination: {
            page: 1,
            page_size: 25,
            total_items: 1,
            total_pages: 1,
          },
        }),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        },
      ),
    )
    vi.stubGlobal('fetch', fetchMock)

    const result = await fetchAuditLogs('admin-token')

    expect(result.logs).toHaveLength(1)
    expect(result.logs[0].action_type).toBe('account_access_updated')
    expect(fetchMock).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/api/admin/audit-logs?page=1&page_size=25',
      expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({
          Authorization: 'Bearer admin-token',
        }),
      }),
    )
  })
})
