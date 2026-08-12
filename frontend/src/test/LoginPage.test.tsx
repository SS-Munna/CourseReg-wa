import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import { AuthProvider } from '../context/AuthContext'
import LoginPage from '../pages/LoginPage'

describe('LoginPage', () => {
  it('presents one role-neutral login for CoursePilot users', () => {
    render(
      <AuthProvider>
        <LoginPage />
      </AuthProvider>,
    )

    expect(screen.getByText('Academic Registration Portal')).toBeVisible()
    expect(screen.getByText('Account access')).toBeVisible()
    expect(screen.getByText('Student')).toBeVisible()
    expect(screen.getByText('Advisor')).toBeVisible()
    expect(screen.getByText('Administration')).toBeVisible()
    expect(
      screen.getByText(/Faculty, advisors, and administrators use the same login/i),
    ).toBeVisible()
  })

  it('keeps public self-registration explicitly student-only', async () => {
    const user = userEvent.setup()

    render(
      <AuthProvider>
        <LoginPage />
      </AuthProvider>,
    )

    await user.click(
      screen.getByRole('button', { name: 'Create student account' }),
    )

    expect(screen.getByText('Student sign-up')).toBeVisible()
    expect(
      screen.getByRole('heading', { name: 'Create your student account' }),
    ).toBeVisible()
    expect(
      screen.getByText(/Faculty and administrative access is provisioned/i),
    ).toBeVisible()
  })

  it('blocks malformed email before authentication is requested', async () => {
    const user = userEvent.setup()

    render(
      <AuthProvider>
        <LoginPage />
      </AuthProvider>,
    )

    await user.type(screen.getByLabelText('Email address'), 'not-an-email')
    await user.type(screen.getByLabelText('Password'), 'secret1')
    await user.click(screen.getByRole('button', { name: 'Log in' }))

    expect(screen.getByRole('alert')).toHaveTextContent(
      'Enter a valid email address.',
    )
  })

  it('validates student name length before public registration', async () => {
    const user = userEvent.setup()

    render(
      <AuthProvider>
        <LoginPage />
      </AuthProvider>,
    )

    await user.click(
      screen.getByRole('button', { name: 'Create student account' }),
    )
    await user.type(screen.getByLabelText('Full name'), 'A')
    await user.type(screen.getByLabelText('Email address'), 'a@example.com')
    await user.type(screen.getByLabelText('Password'), 'secret1')
    await user.click(
      screen.getByRole('button', { name: 'Create student account' }),
    )

    expect(screen.getByRole('alert')).toHaveTextContent(
      'Full name must be between 2 and 255 characters.',
    )
  })

})
