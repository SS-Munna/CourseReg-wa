import { useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'

import NotificationCenter from '../components/NotificationCenter'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'
import {
  WorkspaceNavigationProvider,
  type WorkspaceSection,
} from '../context/WorkspaceNavigationContext'

type AppLayoutProps = {
  children: ReactNode
}

type NavigationItem = {
  id: WorkspaceSection
  label: string
  hint: string
}

const ROLE_LABELS: Record<string, string> = {
  student: 'Student account',
  advisor: 'Advisor account',
  'department-admin': 'Department admin',
  'system-admin': 'System admin',
}

const STUDENT_NAVIGATION: NavigationItem[] = [
  { id: 'student-overview', label: 'Dashboard', hint: 'Registration overview' },
  { id: 'student-courses', label: 'Browse courses', hint: 'Find available sections' },
  { id: 'student-selection', label: 'My selection', hint: 'Review draft courses' },
  { id: 'student-status', label: 'Registration status', hint: 'Track advisor decisions' },
  { id: 'student-waitlist', label: 'Waitlist', hint: 'Monitor queue positions' },
  { id: 'student-timetable', label: 'Weekly timetable', hint: 'Approved course schedule' },
]

const ADVISOR_NAVIGATION: NavigationItem[] = [
  { id: 'advisor-overview', label: 'Dashboard', hint: 'Review queue overview' },
  { id: 'advisor-reviews', label: 'Review requests', hint: 'Approve or reject' },
]

const ADMIN_NAVIGATION: NavigationItem[] = [
  { id: 'admin-overview', label: 'Dashboard', hint: 'Administration overview' },
  { id: 'admin-users', label: 'Users & access', hint: 'Search and control access' },
  { id: 'admin-staff', label: 'Provision staff', hint: 'Create staff accounts' },
  { id: 'admin-students', label: 'Student setup', hint: 'Link academic profiles' },
  { id: 'admin-academic', label: 'Academic setup', hint: 'Departments & programs' },
]

const SYSTEM_ADMIN_NAVIGATION: NavigationItem[] = [
  ...ADMIN_NAVIGATION,
  { id: 'admin-audit', label: 'Audit log', hint: 'Security and activity history' },
]

function navigationForRole(role: string | undefined): NavigationItem[] {
  if (role === 'student') {
    return STUDENT_NAVIGATION
  }

  if (role === 'advisor') {
    return ADVISOR_NAVIGATION
  }

  if (role === 'system-admin') {
    return SYSTEM_ADMIN_NAVIGATION
  }

  if (role === 'department-admin') {
    return ADMIN_NAVIGATION.filter((item) => item.id !== 'admin-academic')
  }

  return []
}

export default function AppLayout({ children }: AppLayoutProps) {
  const { user, logout } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const role = user?.role
  const navigation = useMemo(() => navigationForRole(role), [role])
  const [activeSection, setActiveSection] = useState<WorkspaceSection>(
    navigation[0]?.id ?? 'all',
  )
  const [mobileNavigationOpen, setMobileNavigationOpen] = useState(false)

  useEffect(() => {
    const defaultSection = navigation[0]?.id ?? 'all'
    const sectionStillAvailable = navigation.some(
      (item) => item.id === activeSection,
    )

    if (!sectionStillAvailable) {
      setActiveSection(defaultSection)
    }
  }, [activeSection, navigation])

  const userInitial = user?.name.trim().charAt(0).toUpperCase() || 'C'

  const chooseSection = (section: WorkspaceSection) => {
    setActiveSection(section)
    setMobileNavigationOpen(false)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <WorkspaceNavigationProvider value={{ activeSection, setActiveSection }}>
      <div className="app-shell">
        <header className="topbar">
          <div className="topbar-brand-area">
            <button
              className="workspace-menu-button"
              type="button"
              aria-label="Open workspace navigation"
              aria-expanded={mobileNavigationOpen}
              onClick={() => setMobileNavigationOpen((current) => !current)}
            >
              <span aria-hidden="true">☰</span>
            </button>

            <div className="brand-block">
              <div className="brand-mark" aria-hidden="true">C</div>
              <div className="brand-text">
                <strong>CoursePilot</strong>
                <span>Academic registration</span>
              </div>
            </div>
          </div>

          <div className="topbar-actions">
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

        <div className="workspace-frame">
          {mobileNavigationOpen && (
            <button
              className="workspace-sidebar-backdrop"
              type="button"
              aria-label="Close workspace navigation"
              onClick={() => setMobileNavigationOpen(false)}
            />
          )}

          <aside
            className={`workspace-sidebar${mobileNavigationOpen ? ' is-open' : ''}`}
            aria-label="Workspace navigation"
          >
            <div className="workspace-sidebar-heading">
              <span>Workspace</span>
              <strong>{ROLE_LABELS[role || ''] || 'CoursePilot'}</strong>
            </div>

            <nav className="workspace-navigation">
              {navigation.map((item) => (
                <button
                  key={item.id}
                  className={activeSection === item.id ? 'active' : ''}
                  type="button"
                  aria-current={activeSection === item.id ? 'page' : undefined}
                  onClick={() => chooseSection(item.id)}
                >
                  <span>{item.label}</span>
                  <small>{item.hint}</small>
                </button>
              ))}
            </nav>

            <div className="workspace-sidebar-footer">
              <span>Signed in as</span>
              <strong>{user?.email}</strong>
            </div>
          </aside>

          <div className="workspace-content">{children}</div>
        </div>
      </div>
    </WorkspaceNavigationProvider>
  )
}
