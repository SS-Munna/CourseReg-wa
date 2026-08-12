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
            <p>Student Registration Portal</p>
          </div>
        </div>

        <div className="auth-heading">
          <span className="auth-eyebrow">Student Access</span>
          <h2>{isRegisterMode ? 'Create your account' : 'Welcome back'}</h2>
          <p>
            {isRegisterMode
              ? 'Create a student account to access your dashboard and course catalogue.'
              : 'Log in to review registration progress and explore available courses.'}
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
                onChange={(event) => setName(event.target.value)}
              />
            </label>
          )}

          <label className="auth-field">
            <span>Email address</span>
            <input
              type="email"
              value={email}
              placeholder="student@example.com"
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>

          <label className="auth-field">
            <span>Password</span>
            <input
              type="password"
              value={password}
              placeholder="At least 6 characters"
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>

          {error && <p className="auth-error">{error}</p>}

          <button className="auth-submit" type="submit" disabled={loading}>
            {loading
              ? 'Please wait...'
              : isRegisterMode
                ? 'Create account'
                : 'Log in'}
          </button>
        </form>

        <div className="auth-switch">
          <span>
            {isRegisterMode
              ? 'Already have an account?'
              : "Don't have an account?"}
          </span>
          <button type="button" onClick={switchMode}>
            {isRegisterMode ? 'Log in' : 'Create account'}
          </button>
        </div>
      </section>

      <section className="auth-preview">
        <div className="preview-card">
          <span className="preview-label">After login</span>
          <h2>Plan registration with confidence</h2>
          <p>
            See registration status, compare course sections, and check live
            seat availability before building your academic plan.
          </p>

          <div className="preview-list">
            <span>Registration summary</span>
            <span>Period status</span>
            <span>Advanced filters</span>
            <span>Section details</span>
          </div>
        </div>
      </section>
    </main>
  )
}
