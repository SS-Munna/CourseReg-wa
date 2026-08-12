import type { WaitlistEntry } from '../../types/waitlist'

type WaitlistPanelProps = {
  entries: WaitlistEntry[]
  loading: boolean
  mutationCourseId: string | null
  actionsEnabled: boolean
  unavailableReason: string
  onLeave: (courseId: string) => void
}

function formatJoinedAt(value: string): string {
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(new Date(value))
}

export default function WaitlistPanel({
  entries,
  loading,
  mutationCourseId,
  actionsEnabled,
  unavailableReason,
  onLeave,
}: WaitlistPanelProps) {
  return (
    <section className="waitlist-section" id="waitlist" aria-labelledby="waitlist-title">
      <div className="section-heading">
        <div>
          <span className="section-eyebrow">Seat queue</span>
          <h2 id="waitlist-title">Waiting list</h2>
          <p>See your live queue position and withdraw requests you no longer need.</p>
        </div>
        <span className="summary-note">
          {loading ? 'Updating…' : `${entries.length} waiting`}
        </span>
      </div>

      {loading ? (
        <div className="status-panel-loading" role="status">
          Loading waiting-list positions…
        </div>
      ) : entries.length === 0 ? (
        <div className="status-panel-empty waitlist-empty">
          <span aria-hidden="true">#</span>
          <div>
            <h3>You are not on a waiting list</h3>
            <p>Full sections will offer a Join waitlist action in the course catalogue.</p>
          </div>
        </div>
      ) : (
        <div className="waitlist-grid">
          {entries.map((entry) => {
            const leaving = mutationCourseId === entry.course.course_id
            const actionDisabled =
              !actionsEnabled || Boolean(mutationCourseId)

            return (
              <article className="waitlist-card" key={entry.waitlist_entry_id}>
                <div className="waitlist-position">
                  <span>Position</span>
                  <strong>#{entry.queue_position}</strong>
                  <small>of {entry.total_waiting} waiting</small>
                </div>

                <div className="waitlist-course">
                  <div className="status-record-title">
                    <span className="code-stamp">{entry.course.code}</span>
                    <span className="registration-badge status-waitlisted">Active</span>
                  </div>
                  <h3>{entry.course.title}</h3>
                  <p>
                    Section {entry.course.section || 'N/A'} · {entry.course.semester}
                  </p>
                  <small>Joined {formatJoinedAt(entry.joined_at)}</small>
                </div>

                <div className="waitlist-actions">
                  <button
                    type="button"
                    onClick={() => onLeave(entry.course.course_id)}
                    disabled={actionDisabled}
                    title={!actionsEnabled ? unavailableReason : undefined}
                    aria-label={`Leave waiting list for ${entry.course.code}`}
                  >
                    {leaving ? 'Leaving…' : 'Leave waiting list'}
                  </button>
                  {!actionsEnabled && unavailableReason && (
                    <small>{unavailableReason}</small>
                  )}
                </div>
              </article>
            )
          })}
        </div>
      )}
    </section>
  )
}
