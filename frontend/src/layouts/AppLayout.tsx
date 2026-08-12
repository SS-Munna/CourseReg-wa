import type { ReactNode } from 'react'

import NotificationCenter from '../components/NotificationCenter'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'

type AppLayoutProps = {
  children: ReactNode
}

const ROLE_LABELS: Record<string, string> = {
  student: 'Student account',
  advisor: 'Advisor account',
  'department-admin': 'Department admin',
  'system-admin': 'System admin',
}

export default function AppLayout({ children }: AppLayoutProps) {
  const { user, logout } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const userInitial = user?.name.trim().charAt(0).toUpperCase() || 'C'
  const role = user?.role

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-block">
          <div className="brand-mark" aria-hidden="true">C</div>
          <div className="brand-text">
            <strong>CoursePilot</strong>
            <span>Academic registration</span>
          </div>
        </div>

        <div className="topbar-actions">
          {role === 'student' && (
            <nav className="topbar-nav" aria-label="Student dashboard sections">
              <a className="catalogue-link" href="#registration-status">
                Status
              </a>
              <a className="catalogue-link" href="#timetable">
                Timetable
              </a>
              <a className="catalogue-link" href="#waitlist">
                Waitlist
              </a>
              <a className="catalogue-link" href="#catalogue">
                Browse courses
              </a>
            </nav>
          )}

          {role === 'advisor' && (
            <nav className="topbar-nav" aria-label="Advisor dashboard sections">
              <a className="catalogue-link" href="#advisor-review-queue">
                Review queue
              </a>
            </nav>
          )}

          {(role === 'department-admin' || role === 'system-admin') && (
            <nav className="topbar-nav" aria-label="Administration sections">
              <a className="catalogue-link" href="#admin-users">
                Users & access
              </a>
              <a className="catalogue-link" href="#admin-create-staff">
                Provision staff
              </a>
              {role === 'system-admin' && (
                <a className="catalogue-link" href="#audit-log">
                  Audit log
                </a>
              )}
            </nav>
          )}

          {user && <NotificationCenter />}

          <button
            className="theme-toggle"
            type="button"
            onClick={toggleTheme}
            aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          >
            <span aria-hidden="true">{theme === 'dark' ? '☀' : '☾'}</span>
          </button>

          {user && (
            <div className="user-block">
              <span className="user-avatar" aria-hidden="true">{userInitial}</span>
              <span>
                <strong>{user.name}</strong>
                <small>{ROLE_LABELS[user.role] || 'CoursePilot account'}</small>
              </span>
            </div>
          )}

          <button
            className="logout-button"
            type="button"
            onClick={logout}
          >
            Log out
          </button>
        </div>
      </header>

      {children}
    </div>
  )
}
