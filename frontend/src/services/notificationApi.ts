import { requestJson } from './apiClient'
import type {
  NotificationItem,
  NotificationListData,
} from '../types/notification'

type SuccessResponse<T> = {
  success: true
  data: T
}

export async function fetchNotifications(
  token: string,
  unreadOnly = false,
): Promise<NotificationListData> {
  const query = new URLSearchParams({
    page: '1',
    page_size: '10',
    unread_only: String(unreadOnly),
  })
  const response = await requestJson<SuccessResponse<NotificationListData>>(
    `/api/notifications?${query.toString()}`,
    {
      token,
      fallbackMessage: 'Notifications could not be loaded.',
      fallbackCode: 'NOTIFICATIONS_LOAD_FAILED',
    },
  )

  return response.data
}

export async function markNotificationRead(
  token: string,
  notificationId: string,
): Promise<NotificationItem> {
  const response = await requestJson<SuccessResponse<NotificationItem>>(
    `/api/notifications/${notificationId}/read`,
    {
      token,
      method: 'PATCH',
      fallbackMessage: 'The notification could not be updated.',
      fallbackCode: 'NOTIFICATION_UPDATE_FAILED',
    },
  )

  return response.data
}

export async function markAllNotificationsRead(
  token: string,
): Promise<{ updated_count: number; unread_count: number }> {
  const response = await requestJson<
    SuccessResponse<{ updated_count: number; unread_count: number }>
  >('/api/notifications/read-all', {
    token,
    method: 'POST',
    fallbackMessage: 'Notifications could not be marked as read.',
    fallbackCode: 'NOTIFICATIONS_UPDATE_FAILED',
  })

  return response.data
}
