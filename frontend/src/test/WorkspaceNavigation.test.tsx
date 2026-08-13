import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { AuthProvider } from '../context/AuthContext'
import { ThemeProvider } from '../context/ThemeContext'
import { useWorkspaceNavigation } from '../context/WorkspaceNavigationContext'
import AppLayout from '../layouts/AppLayout'

vi.mock('../components/NotificationCenter', () => ({
  default: vi.fn(() => null),
}))

function storeSession(role: string) {
  localStorage.setItem(
    'coursepilot_user',
    JSON.stringify({
      id: `${role}-1`,
      name: 'Workspace Test User',
      email: `${role}@example.com`,
      role,
    }),
  )
  localStorage.setItem('coursepilot_token', 'workspace-token')
}

function ActiveSectionProbe() {
  const { activeSection } = useWorkspaceNavigation()
  return <div data-testid="active-section">{activeSection}</div>
}

function renderLayout(role: string) {
  storeSession(role)

  return render(
    <ThemeProvider>
      <AuthProvider>
        <AppLayout>
          <ActiveSectionProbe />
        </AppLayout>
      </AuthProvider>
    </ThemeProvider>,
  )
}

beforeEach(() => {
  vi.clearAllMocks()
  vi.stubGlobal('scrollTo', vi.fn())
})

describe('role workspace navigation', () => {
  it('gives students focused registration workspaces and changes the active view', async () => {
    const user = userEvent.setup()
    renderLayout('student')

    expect(await screen.findByTestId('active-section')).toHaveTextContent(
      'student-overview',
    )
    expect(screen.getByRole('button', { name: /Browse courses/i })).toBeVisible()
    expect(screen.queryByRole('button', { name: /Provision staff/i })).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /Browse courses/i }))

    expect(screen.getByTestId('active-section')).toHaveTextContent(
      'student-courses',
    )
  })

  it('keeps advisor navigation limited to advisor review work', async () => {
    renderLayout('advisor')

    expect(await screen.findByTestId('active-section')).toHaveTextContent(
      'advisor-overview',
    )
    expect(screen.getByRole('button', { name: /Review requests/i })).toBeVisible()
    expect(screen.queryByRole('button', { name: /Users & access/i })).not.toBeInTheDocument()
  })

  it('shows system administrators the full administration menu', async () => {
    renderLayout('system-admin')

    expect(await screen.findByTestId('active-section')).toHaveTextContent(
      'admin-overview',
    )
    expect(screen.getByRole('button', { name: /Users & access/i })).toBeVisible()
    expect(screen.getByRole('button', { name: /Academic setup/i })).toBeVisible()
    expect(screen.getByRole('button', { name: /Audit log/i })).toBeVisible()
  })

  it('does not expose system-level setup or audit navigation to department admins', async () => {
    renderLayout('department-admin')

    expect(await screen.findByTestId('active-section')).toHaveTextContent(
      'admin-overview',
    )
    expect(screen.getByRole('button', { name: /Provision staff/i })).toBeVisible()
    expect(screen.queryByRole('button', { name: /Academic setup/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Audit log/i })).not.toBeInTheDocument()
  })
})
