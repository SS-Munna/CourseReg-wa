import { useCallback, useEffect, useState } from 'react'

import { useAuth } from '../../context/AuthContext'
import { fetchAuditLogs } from '../../services/auditApi'
import type { AuditLogItem } from '../../types/audit'

function formatAuditTime(value: string): string {
  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return value
  }

  return new Intl.DateTimeFormat('en', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}

function humanize(value: string): string {
  return value.replaceAll('_', ' ').replace(/\b\w/g, (match) => match.toUpperCase())
}

export default function AuditLogPanel() {
  const { token } = useAuth()
  const [logs, setLogs] = useState<AuditLogItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    if (!token) {
      return
    }

    setLoading(true)
    setError('')

    try {
      const result = await fetchAuditLogs(token)
      setLogs(result.logs)
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'Audit activity could not be loaded.',
      )
    } finally {
      setLoading(false)
    }
  }, [token])

  useEffect(() => {
    void load()
  }, [load])

  return (
    <section className="audit-section" id="audit-log" aria-labelledby="audit-log-title">
      <div className="section-heading">
        <div>
          <span className="section-eyebrow">Security & accountability</span>
          <h2 id="audit-log-title">Audit activity</h2>
          <p>Review recent privileged and registration events recorded by CoursePilot.</p>
        </div>
        <button className="refresh-button" type="button" onClick={() => void load()}>
          <span aria-hidden="true">↻</span>
          Refresh activity
        </button>
      </div>

      {loading && <div className="audit-state">Loading audit activity…</div>}
      {error && <div className="audit-state audit-error">{error}</div>}
      {!loading && !error && logs.length === 0 && (
        <div className="audit-state">No audit activity has been recorded yet.</div>
      )}

      {!loading && logs.length > 0 && (
        <div className="audit-table-wrap">
          <table className="audit-table">
            <thead>
              <tr>
                <th>When</th>
                <th>Actor</th>
                <th>Action</th>
                <th>Entity</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td>{formatAuditTime(log.created_at)}</td>
                  <td>
                    <strong>{log.actor_name}</strong>
                    <span>{log.actor_email}</span>
                  </td>
                  <td>{humanize(log.action_type)}</td>
                  <td>
                    <strong>{humanize(log.entity_type)}</strong>
                    <span>{log.entity_id.slice(0, 8)}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
