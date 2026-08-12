import { useState } from 'react'
import type { FormEvent } from 'react'

import { useAuth } from '../../context/AuthContext'

import './LoginPage.css'

type AuthMode = 'login' | 'register'

export default function LoginPage() {
  const { login, register } = useAuth()

  const [mode, setMode] = useState<AuthMode>('login')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const isRegisterMode = mode === 'register'

  const resetFormMessage = () => {
    setError('')
  }

  const switchMode = () => {
    resetFormMessage()
    setMode((currentMode) =>
      currentMode === 'login' ? 'register' : 'login',
    )
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    resetFormMessage()

    const trimmedEmail = email.trim()
    const trimmedName = name.trim()

    if (!trimmedEmail || !password) {
      setError('Please enter your email and password.')
      return
    }

    if (isRegisterMode && !trimmedName) {
      setError('Please enter your full name.')
      return
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters long.')
      return
    }

    try {
      setLoading(true)

      if (isRegisterMode) {
        await register({
          name: trimmedName,
          email: trimmedEmail,
          password,
        })
      } else {
        await login({
          email: trimmedEmail,
          password,
        })
      }
    } catch (requestError) {
      const message =
        requestError instanceof Error
          ? requestError.message
          : 'Authentication failed. Please try again.'

      setError(message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="auth-shell">
      <section className="auth-card">
        <div className="auth-brand">
          <span className="auth-logo">C</span>
          <div>
            <h1>CoursePilot</h1>
            <p>Academic Registration Portal</p>
          </div>
        </div>

        <div className="auth-heading">
          <span className="auth-eyebrow">
            {isRegisterMode ? 'Student sign-up' : 'Account access'}
          </span>
          <h2>
            {isRegisterMode ? 'Create your student account' : 'Welcome back'}
          </h2>
          <p>
            {isRegisterMode
              ? 'Student accounts can be created here. Faculty and administrative access is provisioned by the university.'
              : 'Sign in once and CoursePilot will open the workspace assigned to your account role.'}
          </p>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          {isRegisterMode && (
            <label className="auth-field">
              <span>Full name</span>
              <input
                type="text"
                value={name}
                placeholder="Enter your full name"
                autoComplete="name"
                onChange={(event) => setName(event.target.value)}
              />
            </label>
          )}

          <label className="auth-field">
            <span>Email address</span>
            <input
              type="email"
              value={email}
              placeholder="you@example.com"
              autoComplete="email"
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>

          <label className="auth-field">
            <span>Password</span>
            <input
              type="password"
              value={password}
              placeholder="At least 6 characters"
              autoComplete={isRegisterMode ? 'new-password' : 'current-password'}
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>

          {error && (
            <p className="auth-error" role="alert">
              {error}
            </p>
          )}

          <button className="auth-submit" type="submit" disabled={loading}>
            {loading
              ? 'Please wait...'
              : isRegisterMode
                ? 'Create student account'
                : 'Log in'}
          </button>
        </form>

        <div className="auth-switch">
          <span>
            {isRegisterMode
              ? 'Already have an account?'
              : 'Student without an account?'}
          </span>
          <button type="button" onClick={switchMode}>
            {isRegisterMode ? 'Log in' : 'Create student account'}
          </button>
        </div>

        <p className="auth-staff-note">
          Faculty, advisors, and administrators use the same login. Staff
          accounts must be provisioned and activated by administration.
        </p>
      </section>

      <section className="auth-preview">
        <div className="preview-card">
          <span className="preview-label">One secure portal</span>
          <h2>Role-based workspaces for every registration step</h2>
          <p>
            Your account role determines what you can see and do after sign-in.
            Student, advisor, and administrative workflows stay separated.
          </p>

          <div className="preview-role-list">
            <article>
              <span>Student</span>
              <strong>Plan and submit</strong>
              <p>Browse courses, build a selection, track status, and view your timetable.</p>
            </article>
            <article>
              <span>Advisor</span>
              <strong>Review and decide</strong>
              <p>Inspect assigned registration requests and approve or reject with comments.</p>
            </article>
            <article>
              <span>Administration</span>
              <strong>Control and oversee</strong>
              <p>Manage academic setup, staff access, and system oversight.</p>
            </article>
          </div>
        </div>
      </section>
    </main>
  )
}
