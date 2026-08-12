import type {
  CreditLoadValidation,
  DraftSelection,
} from '../../types/selection'

type RegistrationWorkspaceProps = {
  selections: DraftSelection[]
  creditValidation: CreditLoadValidation | null
  loading: boolean
  mutationCourseId: string | null
  validatingReview: boolean
  actionsEnabled: boolean
  unavailableReason: string
  reviewUnavailableReason: string
  onRemove: (courseId: string) => void
  onReview: () => void
}

function formatSchedule(selection: DraftSelection): string {
  const meetings = selection.course.schedule || []

  if (meetings.length === 0) {
    return 'Schedule to be announced'
  }

  return meetings
    .map(
      (meeting) =>
        `${meeting.day} ${meeting.start_time}–${meeting.end_time}`,
    )
    .join(' · ')
}

function creditStatusLabel(validation: CreditLoadValidation): string {
  if (validation.validation_status === 'below_minimum') {
    return `${validation.minimum_shortfall} more credits needed`
  }

  if (validation.validation_status === 'above_maximum') {
    return `${validation.maximum_excess} credits over the limit`
  }

  return 'Credit load ready'
}

function RegistrationWorkspace({
  selections,
  creditValidation,
  loading,
  mutationCourseId,
  validatingReview,
  actionsEnabled,
  unavailableReason,
  reviewUnavailableReason,
  onRemove,
  onReview,
}: RegistrationWorkspaceProps) {
  const creditProgress = creditValidation
    ? Math.min(
        100,
        (creditValidation.selected_credits /
          Math.max(creditValidation.maximum_credit, 1)) *
          100,
      )
    : 0
  const canReview =
    actionsEnabled &&
    selections.length > 0 &&
    Boolean(creditValidation?.is_valid) &&
    !reviewUnavailableReason &&
    !loading &&
    !mutationCourseId

  return (
    <section
      className="registration-workspace"
      id="course-selection"
      aria-labelledby="selection-title"
    >
      <div className="section-heading selection-heading">
        <div>
          <span className="section-eyebrow">Registration workspace</span>
          <h2 id="selection-title">Your course selection</h2>
          <p>Add sections from the catalogue, check your load, then review once.</p>
        </div>
        <span className="selection-count">
          {loading
            ? 'Loading…'
            : `${selections.length} draft${selections.length === 1 ? '' : 's'}`}
        </span>
      </div>

      <div className="selection-layout">
        <div className="selected-course-panel">
          {loading && (
            <div className="selection-empty" role="status">
              <span className="spinner" aria-hidden="true" />
              Loading your draft selections…
            </div>
          )}

          {!loading && selections.length === 0 && (
            <div className="selection-empty">
              <span className="selection-empty-icon" aria-hidden="true">
                +
              </span>
              <div>
                <h3>No draft courses yet</h3>
                <p>
                  Choose an open section below to start building your registration.
                </p>
              </div>
            </div>
          )}

          {!loading && selections.length > 0 && (
            <div className="selected-course-list">
              {selections.map((selection) => (
                <article
                  className="selected-course-row"
                  key={selection.registration_id}
                >
                  <div className="selected-course-code">
                    <span>{selection.course.code}</span>
                    <small>Section {selection.course.section || 'N/A'}</small>
                  </div>
                  <div className="selected-course-copy">
                    <strong>{selection.course.title}</strong>
                    <span>{formatSchedule(selection)}</span>
                    <small>{selection.course.instructor}</small>
                  </div>
                  <div className="selected-course-actions">
                    <strong>{selection.course.credits} cr</strong>
                    <button
                      type="button"
                      onClick={() => onRemove(selection.course.course_id)}
                      disabled={
                        !actionsEnabled ||
                        Boolean(mutationCourseId)
                      }
                      aria-label={`Remove ${selection.course.code} from selection`}
                    >
                      {mutationCourseId === selection.course.course_id
                        ? 'Removing…'
                        : 'Remove'}
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>

        <aside className="credit-summary" aria-label="Credit load summary">
          <div className="credit-summary-top">
            <div>
              <span>Active credit load</span>
              <strong>
                {creditValidation?.selected_credits ?? '—'}
                <small> credits</small>
              </strong>
            </div>
            {creditValidation && (
              <span
                className={`credit-status credit-${creditValidation.validation_status}`}
              >
                {creditStatusLabel(creditValidation)}
              </span>
            )}
          </div>

          <div className="credit-progress" aria-hidden="true">
            <span style={{ width: `${creditProgress}%` }} />
          </div>

          <div className="credit-range">
            <span>
              Minimum <strong>{creditValidation?.minimum_credit ?? '—'}</strong>
            </span>
            <span>
              Maximum <strong>{creditValidation?.maximum_credit ?? '—'}</strong>
            </span>
          </div>

          <p>
            {creditValidation?.message ||
              'Credit limits will appear when your selections finish loading.'}
          </p>
          <small className="credit-context">
            Active load includes draft, pending, and approved courses.
          </small>

          {!actionsEnabled && unavailableReason && (
            <div className="selection-locked" role="status">
              <strong>Registration actions unavailable</strong>
              <span>{unavailableReason}</span>
            </div>
          )}

          <button
            className="review-selection-button"
            type="button"
            onClick={onReview}
            disabled={!canReview || validatingReview}
          >
            {validatingReview ? 'Validating selection…' : 'Review registration'}
          </button>

          {actionsEnabled && selections.length > 0 && !creditValidation?.is_valid && (
            <small className="review-help">
              Adjust your credit load before final review.
            </small>
          )}
          {actionsEnabled && reviewUnavailableReason && (
            <small className="review-help">{reviewUnavailableReason}</small>
          )}
        </aside>
      </div>
    </section>
  )
}

export default RegistrationWorkspace
