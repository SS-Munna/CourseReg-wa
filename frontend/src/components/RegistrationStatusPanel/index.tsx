import type {
  RegistrationOverview,
  RegistrationState,
  StudentRegistration,
} from '../../types/dashboard'
import type { WaitlistEntry } from '../../types/waitlist'

type RegistrationStatusPanelProps = {
  overview: RegistrationOverview
  loading: boolean
}

const statusLabels: Record<RegistrationState | 'waitlisted', string> = {
  draft: 'Draft',
  pending: 'Pending',
  approved: 'Approved',
  rejected: 'Rejected',
  dropped: 'Dropped',
  waitlisted: 'Waitlisted',
}

function formatDate(value: string | null | undefined): string {
  if (!value) {
    return 'Not recorded'
  }

  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(new Date(value))
}

function RegistrationRecord({ registration }: { registration: StudentRegistration }) {
  const status = registration.registration_status
  const eventDate =
    status === 'approved' || status === 'rejected'
      ? registration.reviewed_at
      : status === 'draft' || status === 'dropped'
        ? registration.updated_at
        : registration.submitted_at || registration.updated_at

  return (
    <article className="status-record">
      <div className="status-record-main">
        <div>
          <div className="status-record-title">
            <span className="code-stamp">{registration.course.code}</span>
            <span className={`registration-badge status-${status}`}>
              {statusLabels[status]}
            </span>
          </div>
          <h3>{registration.course.title}</h3>
          <p>
            Section {registration.course.section || 'N/A'} · {registration.course.credits}{' '}
            credits · {registration.course.semester}
          </p>
        </div>
        <div className="status-record-date">
          <span>
            {status === 'approved' || status === 'rejected'
              ? 'Reviewed'
              : status === 'draft' || status === 'dropped'
                ? 'Updated'
                : 'Submitted'}
          </span>
          <strong>{formatDate(eventDate)}</strong>
        </div>
      </div>

      {registration.advisor_comment && (
        <div className="advisor-comment">
          <span>Advisor comment</span>
          <p>{registration.advisor_comment}</p>
        </div>
      )}

      {status === 'rejected' && !registration.advisor_comment && (
        <div className="advisor-comment is-empty">
          <span>Advisor comment</span>
          <p>No advisor comment was provided.</p>
        </div>
      )}
    </article>
  )
}

function WaitlistedRecord({ entry }: { entry: WaitlistEntry }) {
  return (
    <article className="status-record">
      <div className="status-record-main">
        <div>
          <div className="status-record-title">
            <span className="code-stamp">{entry.course.code}</span>
            <span className="registration-badge status-waitlisted">Waitlisted</span>
          </div>
          <h3>{entry.course.title}</h3>
          <p>{`Section ${entry.course.section || 'N/A'} · Position #${entry.queue_position} of ${entry.total_waiting}`}</p>
        </div>
        <div className="status-record-date">
          <span>Joined</span>
          <strong>{formatDate(entry.joined_at)}</strong>
        </div>
      </div>
    </article>
  )
}

export default function RegistrationStatusPanel({
  overview,
  loading,
}: RegistrationStatusPanelProps) {
  const totalRecords = overview.registrations.length + overview.waitlist_entries.length

  return (
    <section
      className="registration-status-section"
      id="registration-status"
      aria-labelledby="registration-status-title"
    >
      <div className="section-heading">
        <div>
          <span className="section-eyebrow">Registration tracking</span>
          <h2 id="registration-status-title">Registration status</h2>
          <p>Monitor submitted courses, advisor decisions, and waiting-list outcomes.</p>
        </div>
        <span className="summary-note">
          {loading ? 'Updating…' : `${totalRecords} records`}
        </span>
      </div>

      {loading ? (
        <div className="status-panel-loading" role="status">
          Loading registration outcomes…
        </div>
      ) : totalRecords === 0 ? (
        <div className="status-panel-empty">
          <span aria-hidden="true">◎</span>
          <div>
            <h3>No registration outcomes yet</h3>
            <p>
              Draft, pending, approved, rejected, dropped, and waitlisted courses will
              appear here.
            </p>
          </div>
        </div>
      ) : (
        <div className="status-record-list">
          {overview.registrations.map((registration) => (
            <RegistrationRecord
              key={registration.registration_id}
              registration={registration}
            />
          ))}
          {overview.waitlist_entries.map((entry) => (
            <WaitlistedRecord key={entry.waitlist_entry_id} entry={entry} />
          ))}
        </div>
      )}
    </section>
  )
}
