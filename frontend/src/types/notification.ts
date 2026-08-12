export type NotificationItem = {
  id: string
  notification_type: string
  title: string
  message: string
  is_read: boolean
  created_at: string
}

export type NotificationPagination = {
  page: number
  page_size: number
  total_items: number
  total_pages: number
}

export type NotificationListData = {
  notifications: NotificationItem[]
  unread_count: number
  pagination: NotificationPagination
}
