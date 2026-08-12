import { useAuth } from '../../context/AuthContext'

const ROLE_COPY: Record<string, { title: string; description: string }> = {
  'department-admin': {
    title: 'Department administration',
    description:
      'Your department administrator account is active. Academic management and staff-access controls are available from the administration workspace.',
  },
  'system-admin': {
    title: 'System administration',
    description:
      'Your system administrator account is active. Platform-wide access and account controls are available from the administration workspace.',
  },
}

export default function RoleWorkspacePage() {
  const { user } = useAuth()
  const copy = ROLE_COPY[user?.role || ''] || {
    title: 'CoursePilot workspace',
    description:
      'This account is authenticated, but no workspace is configured for its role.',
  }

  return (
    <main className="app-main">
      <section className="role-workspace-card">
        <span className="page-eyebrow">Role-aware access</span>
        <h1>{copy.title}</h1>
        <p>{copy.description}</p>
        <div className="inline-alert info">
          <strong>Access protected</strong>
          <span>
            CoursePilot will not expose the student workspace to this account.
            The administration interface is completed in the department
            administration feature.
          </span>
        </div>
      </section>
    </main>
  )
}
