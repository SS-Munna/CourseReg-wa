import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import App from '../App'

vi.mock('../pages/StudentDashboardPage', () => ({
  default: () => <div>Student workspace loaded</div>,
}))

vi.mock('../pages/AdvisorDashboardPage', () => ({
  default: () => <div>Advisor workspace loaded</div>,
}))

vi.mock('../pages/AdminDashboardPage', () => ({
  default: () => <div>Administration workspace loaded</div>,
}))

function storeSession(role: string) {
  localStorage.setItem(
    'coursepilot_user',
    JSON.stringify({
      id: `${role}-1`,
      name: 'Role Test User',
      email: `${role}@example.com`,
      role,
    }),
  )
  localStorage.setItem('coursepilot_token', 'role-token')
}

describe('role-aware app routing', () => {
  it('routes student accounts to the student workspace', async () => {
    storeSession('student')

    render(<App />)

    expect(await screen.findByText('Student workspace loaded')).toBeVisible()
  })

  it('routes advisor accounts to the advisor workspace', async () => {
    storeSession('advisor')

    render(<App />)

    expect(await screen.findByText('Advisor workspace loaded')).toBeVisible()
  })

  it('routes system administrators to the administration workspace', async () => {
    storeSession('system-admin')

    render(<App />)

    expect(
      await screen.findByText('Administration workspace loaded'),
    ).toBeVisible()
    expect(screen.queryByText('Student workspace loaded')).not.toBeInTheDocument()
  })

  it('routes department administrators to the administration workspace', async () => {
    storeSession('department-admin')

    render(<App />)

    expect(
      await screen.findByText('Administration workspace loaded'),
    ).toBeVisible()
  })
})
