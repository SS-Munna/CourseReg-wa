import { useCallback, useEffect, useRef, useState } from 'react'

import { useAuth } from '../../context/AuthContext'
import {
  fetchNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from '../../services/notificationApi'
import type { NotificationItem } from '../../types/notification'

function formatNotificationTime(value: string): string {
  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return value
  }

  return new Intl.DateTimeFormat('en', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}

export default function NotificationCenter() {
  const { token } = useAuth()
  const [items, setItems] = useState<NotificationItem[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const rootRef = useRef<HTMLDivElement>(null)

  const load = useCallback(async () => {
    if (!token) {
      return
    }

    setLoading(true)
    setError('')

    try {
      const data = await fetchNotifications(token)
      setItems(data.notifications)
      setUnreadCount(data.unread_count)
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'Notifications could not be loaded.',
      )
    } finally {
      setLoading(false)
    }
  }, [token])

  useEffect(() => {
    void load()
  }, [load])

  useEffect(() => {
    const closeOnOutsideClick = (event: MouseEvent) => {
      if (
        open &&
        rootRef.current &&
        !rootRef.current.contains(event.target as Node)
      ) {
        setOpen(false)
      }
    }

    document.addEventListener('mousedown', closeOnOutsideClick)
    return () => document.removeEventListener('mousedown', closeOnOutsideClick)
  }, [open])

  const markRead = async (notification: NotificationItem) => {
    if (!token || notification.is_read) {
      return
    }

    try {
      const updated = await markNotificationRead(token, notification.id)
      setItems((current) =>
        current.map((item) => (item.id === updated.id ? updated : item)),
      )
      setUnreadCount((current) => Math.max(0, current - 1))
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'The notification could not be updated.',
      )
    }
  }

  const markAllRead = async () => {
    if (!token || unreadCount === 0) {
      return
    }

    try {
      await markAllNotificationsRead(token)
      setItems((current) =>
        current.map((item) => ({ ...item, is_read: true })),
      )
      setUnreadCount(0)
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'Notifications could not be updated.',
      )
    }
  }

  return (
    <div className="notification-center" ref={rootRef}>
      <button
        className="notification-trigger"
        type="button"
        aria-label={`Notifications${unreadCount ? `, ${unreadCount} unread` : ''}`}
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
      >
        <span aria-hidden="true">🔔</span>
        {unreadCount > 0 && (
          <span className="notification-badge">{Math.min(unreadCount, 99)}</span>
        )}
      </button>

      {open && (
        <section className="notification-panel" aria-label="Notifications panel">
          <div className="notification-panel-header">
            <div>
              <strong>Notifications</strong>
              <span>{unreadCount} unread</span>
            </div>
            <button
              type="button"
              disabled={unreadCount === 0}
              onClick={() => void markAllRead()}
            >
              Mark all read
            </button>
          </div>

          {loading && <p className="notification-state">Loading notifications…</p>}
          {error && <p className="notification-state notification-error">{error}</p>}

          {!loading && !error && items.length === 0 && (
            <p className="notification-state">No notifications yet.</p>
          )}

          {!loading && items.length > 0 && (
            <div className="notification-list">
              {items.map((item) => (
                <article
                  className={`notification-item ${item.is_read ? 'is-read' : 'is-unread'}`}
                  key={item.id}
                >
                  <div className="notification-item-heading">
                    <strong>{item.title}</strong>
                    {!item.is_read && <span>New</span>}
                  </div>
                  <p>{item.message}</p>
                  <div className="notification-item-footer">
                    <time>{formatNotificationTime(item.created_at)}</time>
                    {!item.is_read && (
                      <button
                        type="button"
                        onClick={() => void markRead(item)}
                      >
                        Mark read
                      </button>
                    )}
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      )}
    </div>
  )
}
