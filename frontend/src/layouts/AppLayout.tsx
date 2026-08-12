import type { ReactNode } from 'react'

import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'

type AppLayoutProps = {
  children: ReactNode
}

export default function AppLayout({ children }: AppLayoutProps) {
  const { user, logout } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const userInitial = user?.name.trim().charAt(0).toUpperCase() || 'S'

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
          <a className="catalogue-link" href="#catalogue">
            Browse courses
          </a>

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
                <small>Student account</small>
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
