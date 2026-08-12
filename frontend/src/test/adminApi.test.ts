import { afterEach, describe, expect, it, vi } from 'vitest'

import {
  createStaffAccount,
  fetchAdminOverview,
  fetchAdminUsers,
  updateAccountAccess,
} from '../services/adminApi'

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('administration API', () => {
  it('loads the administration overview with bearer authentication', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          success: true,
          data: {
            total_users: 8,
            active_students: 5,
            active_advisors: 2,
            pending_staff: 1,
            suspended_accounts: 0,
            department_admins: 1,
          },
        }),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        },
      ),
    )
    vi.stubGlobal('fetch', fetchMock)

    const overview = await fetchAdminOverview('admin-token')

    expect(overview.pending_staff).toBe(1)
    expect(fetchMock).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/api/admin/overview',
      expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({
          Authorization: 'Bearer admin-token',
        }),
      }),
    )
  })

  it('searches user access records using the administration contract', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          success: true,
          data: [],
          pagination: {
            page: 1,
            page_size: 25,
            total_items: 0,
            total_pages: 0,
          },
        }),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        },
      ),
    )
    vi.stubGlobal('fetch', fetchMock)

    await fetchAdminUsers('admin-token', 'nadia', 1)

    expect(fetchMock).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/api/admin/users?page=1&page_size=25&search=nadia',
      expect.objectContaining({
        method: 'GET',
      }),
    )
  })

  it('provisions staff and updates access through protected admin endpoints', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            success: true,
            data: {
              id: 'advisor-1',
              name: 'Dr. Nadia',
              email: 'nadia@example.com',
              role: 'advisor',
              account_status: 'active',
              created_at: '2026-08-13T00:00:00Z',
            },
          }),
          {
            status: 201,
            headers: { 'Content-Type': 'application/json' },
          },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            success: true,
            data: {
              id: 'advisor-1',
              name: 'Dr. Nadia',
              email: 'nadia@example.com',
              role: 'advisor',
              account_status: 'suspended',
              created_at: '2026-08-13T00:00:00Z',
            },
          }),
          {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          },
        ),
      )

    vi.stubGlobal('fetch', fetchMock)

    await createStaffAccount('admin-token', {
      name: 'Dr. Nadia',
      email: 'nadia@example.com',
      password: 'TemporaryPass123!',
      role: 'advisor',
      account_status: 'active',
      department_id: 'department-1',
      employee_number: 'FAC-001',
    })
    await updateAccountAccess(
      'admin-token',
      'advisor-1',
      'suspended',
    )

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      'http://127.0.0.1:8000/api/admin/staff',
      expect.objectContaining({
        method: 'POST',
      }),
    )
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      'http://127.0.0.1:8000/api/admin/users/advisor-1/access',
      expect.objectContaining({
        method: 'PATCH',
        body: JSON.stringify({
          account_status: 'suspended',
        }),
      }),
    )
  })
})
