import { afterEach, describe, expect, it, vi } from 'vitest'

import {
  fetchNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from '../services/notificationApi'

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('notification API', () => {
  it('loads the signed-in users recent notifications', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          success: true,
          data: {
            notifications: [],
            unread_count: 2,
            pagination: {
              page: 1,
              page_size: 10,
              total_items: 0,
              total_pages: 0,
            },
          },
        }),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        },
      ),
    )
    vi.stubGlobal('fetch', fetchMock)

    const data = await fetchNotifications('student-token')

    expect(data.unread_count).toBe(2)
    expect(fetchMock).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/api/notifications?page=1&page_size=10&unread_only=false',
      expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({
          Authorization: 'Bearer student-token',
        }),
      }),
    )
  })

  it('marks one notification and all notifications as read', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            success: true,
            data: {
              id: 'notification-1',
              notification_type: 'registration_approved',
              title: 'Approved',
              message: 'Your registration was approved.',
              is_read: true,
              created_at: '2026-08-13T00:00:00Z',
            },
          }),
          {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            success: true,
            data: { updated_count: 3, unread_count: 0 },
          }),
          {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          },
        ),
      )

    vi.stubGlobal('fetch', fetchMock)

    await markNotificationRead('token', 'notification-1')
    await markAllNotificationsRead('token')

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      'http://127.0.0.1:8000/api/notifications/notification-1/read',
      expect.objectContaining({ method: 'PATCH' }),
    )
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      'http://127.0.0.1:8000/api/notifications/read-all',
      expect.objectContaining({ method: 'POST' }),
    )
  })
})
