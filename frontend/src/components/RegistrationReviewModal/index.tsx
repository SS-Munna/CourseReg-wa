import { useEffect } from 'react'

import type {
  CreditLoadValidation,
  DraftSelection,
  ScheduleConflictValidation,
} from '../../types/selection'

type RegistrationReviewModalProps = {
  selections: DraftSelection[]
  creditValidation: CreditLoadValidation
  scheduleValidation: ScheduleConflictValidation
  submitting: boolean
  error: string
  onClose: () => void
  onSubmit: () => void
}

function RegistrationReviewModal({
  selections,
  creditValidation,
  scheduleValidation,
  submitting,
  error,
  onClose,
  onSubmit,
}: RegistrationReviewModalProps) {
  useEffect(() => {
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && !submitting) {
        onClose()
      }
    }

    window.addEventListener('keydown', handleKeyDown)

    return () => {
      document.body.style.overflow = previousOverflow
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [onClose, submitting])

  return (
    <div
      className="modal-backdrop"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget && !submitting) {
          onClose()
        }
      }}
    >
      <section
        className="course-modal registration-review-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="registration-review-title"
      >
        <header className="modal-header">
          <div>
            <span className="section-eyebrow">Final review</span>
            <h2 id="registration-review-title">Review your registration</h2>
            <p>Confirm every section before sending it to your advisor.</p>
          </div>
          <button
            className="modal-close"
            type="button"
            onClick={onClose}
            disabled={submitting}
            aria-label="Close registration review"
            autoFocus
          >
            ×
          </button>
        </header>

        <div className="modal-body">
          <div className="review-checks" aria-label="Registration validation results">
            <div>
              <span aria-hidden="true">✓</span>
              <div>
                <strong>Credit load validated</strong>
                <small>
                  {creditValidation.selected_credits} active credits within the{' '}
                  {creditValidation.minimum_credit}–{creditValidation.maximum_credit}{' '}
                  range
                </small>
              </div>
            </div>
            <div>
              <span aria-hidden="true">✓</span>
              <div>
                <strong>No schedule conflicts</strong>
                <small>{scheduleValidation.message}</small>
              </div>
            </div>
          </div>

          <div className="review-course-list">
            {selections.map((selection) => (
              <article key={selection.registration_id}>
                <div>
                  <span>{selection.course.code}</span>
                  <strong>{selection.course.title}</strong>
                  <small>
                    Section {selection.course.section || 'N/A'} ·{' '}
                    {selection.course.instructor}
                  </small>
                </div>
                <strong>{selection.course.credits} credits</strong>
              </article>
            ))}
          </div>

          <div className="submission-note">
            <strong>What happens next?</strong>
            <p>
              These {selections.length} draft course
              {selections.length === 1 ? '' : 's'} will move to pending status for
              advisor review.
            </p>
          </div>

          {error && (
            <div className="review-error" role="alert">
              <strong>Submission needs attention</strong>
              <span>{error}</span>
            </div>
          )}

          <div className="review-modal-actions">
            <button
              className="secondary-action"
              type="button"
              onClick={onClose}
              disabled={submitting}
            >
              Back to selection
            </button>
            <button
              className="primary-action"
              type="button"
              onClick={onSubmit}
              disabled={submitting}
            >
              {submitting ? 'Submitting…' : 'Submit for advisor review'}
            </button>
          </div>
        </div>
      </section>
    </div>
  )
}

export default RegistrationReviewModal
