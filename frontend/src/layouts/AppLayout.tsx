import type { ReactNode } from 'react'
import { useTheme } from '../context/ThemeContext'

type AppLayoutProps = {
  children: ReactNode
}

function AppLayout({ children }: AppLayoutProps) {
  const { theme, toggleTheme } = useTheme()

  return (
    <main className="page">
      <header className="topbar">
        <div className="brand-block">
          <span className="brand-mark">C</span>
          <div className="brand-text">
            <div className="brand">CoursePilot</div>
            <p>Student Registration Portal</p>
          </div>
        </div>

        <div className="topbar-actions">
          <span className="topbar-chip">Student View</span>
          <span className="topbar-chip">Fall 2026</span>
          <button type="button" className="theme-toggle" onClick={toggleTheme}>
            {theme === 'light' ? 'Dark mode' : 'Day mode'}
          </button>
        </div>
      </header>

      {children}
    </main>
  )
}

export default AppLayout