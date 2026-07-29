import type { ReactNode } from 'react'

import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'

type AppLayoutProps = {
  children: ReactNode
}

export default function AppLayout({ children }: AppLayoutProps) {
  const { user, logout } = useAuth()
  const { theme, toggleTheme } = useTheme()

  return (
    <div className="page">
      <header className="topbar">
        <div className="brand-block">
          <div className="brand-mark">C</div>
          <div className="brand-text">
            <strong>CoursePilot</strong>
            <span>Student Registration Portal</span>
          </div>
        </div>

        <div className="topbar-actions">
          {user && (
            <span className="topbar-chip">
              {user.name}
            </span>
          )}

          <span className="topbar-chip">Student View</span>
          <span className="topbar-chip">Fall 2026</span>

          <button
            className="theme-toggle"
            type="button"
            onClick={toggleTheme}
          >
            {theme === 'dark' ? 'Light mode' : 'Dark mode'}
          </button>

          <button
            className="logout-button"
            type="button"
            onClick={logout}
          >
            Logout
          </button>
        </div>
      </header>

      {children}
    </div>
  )
}