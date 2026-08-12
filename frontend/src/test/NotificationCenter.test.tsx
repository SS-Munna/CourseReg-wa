import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import NotificationCenter from '../components/NotificationCenter'
import {
  fetchNotifications,
  markNotificationRead,
} from '../services/notificationApi'

vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({ token: 'student-token' }),
}))

vi.mock('../services/notificationApi', () => ({
  fetchNotifications: vi.fn(),
  markNotificationRead: vi.fn(),
  markAllNotificationsRead: vi.fn(),
}))

const mockedFetchNotifications = vi.mocked(fetchNotifications)
const mockedMarkNotificationRead = vi.mocked(markNotificationRead)

describe('NotificationCenter', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockedFetchNotifications.mockResolvedValue({
      notifications: [
        {
          id: 'notification-1',
          notification_type: 'registration_approved',
          title: 'Registration approved',
          message: 'Your registration was approved.',
          is_read: false,
          created_at: '2026-08-13T00:00:00Z',
        },
      ],
      unread_count: 1,
      pagination: {
        page: 1,
        page_size: 10,
        total_items: 1,
        total_pages: 1,
      },
    })
  })

  it('shows the unread badge and opens the notification panel', async () => {
    render(<NotificationCenter />)

    const trigger = await screen.findByRole('button', {
      name: 'Notifications, 1 unread',
    })
    expect(trigger).toBeVisible()

    fireEvent.click(trigger)

    expect(await screen.findByText('Registration approved')).toBeVisible()
    expect(screen.getByText('Your registration was approved.')).toBeVisible()
  })

  it('marks an owned unread notification as read', async () => {
    mockedMarkNotificationRead.mockResolvedValue({
      id: 'notification-1',
      notification_type: 'registration_approved',
      title: 'Registration approved',
      message: 'Your registration was approved.',
      is_read: true,
      created_at: '2026-08-13T00:00:00Z',
    })

    render(<NotificationCenter />)

    fireEvent.click(
      await screen.findByRole('button', {
        name: 'Notifications, 1 unread',
      }),
    )
    fireEvent.click(await screen.findByRole('button', { name: 'Mark read' }))

    await waitFor(() => {
      expect(mockedMarkNotificationRead).toHaveBeenCalledWith(
        'student-token',
        'notification-1',
      )
    })
    expect(screen.getByRole('button', { name: 'Notifications' })).toBeVisible()
  })
})
