import { useCallback, useEffect, useMemo, useState } from 'react'

import { useAuth } from '../../context/AuthContext'
import {
  sectionIsVisible,
  useWorkspaceNavigation,
} from '../../context/WorkspaceNavigationContext'
import {
  fetchAdvisorRequest,
  fetchAdvisorRequests,
  submitAdvisorDecision,
} from '../../services/advisorApi'
import { ApiRequestError } from '../../services/apiClient'
import type {
  AdvisorDecision,
  AdvisorRegistrationRequestDetails,
  AdvisorRegistrationRequestSummary,
  AdvisorRequestStatus,
  PaginationMeta,
} from '../../types/advisor'

const FILTERS: Array<{
  value: AdvisorRequestStatus
  label: string
}> = [
  { value: 'pending', label: 'Pending' },
  { value: 'approved', label: 'Approved' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'all', label: 'All requests' },
]

function formatDate(value: string | null): string {
  if (!value) {
    return 'Not reviewed'
  }

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return value
  }

  return new Intl.DateTimeFormat('en', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}

function requestErrorMessage(
  error: unknown,
  fallback: string,
): string {
  if (error instanceof ApiRequestError || error instanceof Error) {
    return error.message
  }

  return fallback
}

function statusLabel(status: string): string {
  return status.charAt(0).toUpperCase() + status.slice(1)
}

function SummaryCard({
  label,
  value,
  note,
}: {
  label: string
  value: string | number
  note: string
}) {
  return (
    <article className="advisor-summary-card">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{note}</small>
    </article>
  )
}

function RequestCard({
  request,
  selected,
  onSelect,
}: {
  request: AdvisorRegistrationRequestSummary
  selected: boolean
  onSelect: () => void
}) {
  return (
    <article
      className={`advisor-request-card${selected ? ' selected' : ''}`}
    >
      <div className="advisor-request-card-top">
        <div>
          <span className="advisor-student-number">
            {request.student.student_number}
          </span>
          <h3>{request.student.full_name}</h3>
          <p>
            {request.student.program_code} · Trimester{' '}
            {request.student.current_trimester}
          </p>
        </div>
        <span
          className={`registration-badge status-${request.request_status}`}
        >
          {statusLabel(request.request_status)}
        </span>
      </div>

      <div className="advisor-request-meta">
        <span>
          <strong>{request.course_count}</strong>
          <small>courses</small>
        </span>
        <span>
          <strong>{request.total_credits}</strong>
          <small>credits</small>
        </span>
        <span>
          <strong>{formatDate(request.submitted_at)}</strong>
          <small>submitted</small>
        </span>
      </div>

      <div className="advisor-request-courses">
        {request.courses.map((course) => (
          <span key={course.registration_id}>
            {course.code} · {course.section}
          </span>
        ))}
      </div>

      <button
        className="advisor-review-button"
        type="button"
        onClick={onSelect}
      >
        {request.request_status === 'pending'
          ? 'Review request'
          : 'View decision'}
      </button>
    </article>
  )
}

function RequestDetails({
  request,
  submitting,
  onDecision,
}: {
  request: AdvisorRegistrationRequestDetails
  submitting: boolean
  onDecision: (decision: AdvisorDecision, comment: string) => Promise<void>
}) {
  const [comment, setComment] = useState(request.advisor_comment || '')
  const [decisionError, setDecisionError] = useState('')

  useEffect(() => {
    setComment(request.advisor_comment || '')
    setDecisionError('')
  }, [request])

  const decide = async (decision: AdvisorDecision) => {
    const trimmedComment = comment.trim()

    if (decision === 'rejected' && !trimmedComment) {
      setDecisionError('Add a reason before rejecting this request.')
      return
    }

    setDecisionError('')
    await onDecision(decision, trimmedComment)
  }

  return (
    <section
      className="advisor-review-panel"
      aria-label={`Registration request for ${request.student.full_name}`}
    >
      <div className="advisor-review-heading">
        <div>
          <span className="section-eyebrow">Request review</span>
          <h2>{request.student.full_name}</h2>
          <p>
            {request.student.student_number} · {request.student.program_name}
          </p>
        </div>
        <span
          className={`registration-badge status-${request.request_status}`}
        >
          {statusLabel(request.request_status)}
        </span>
      </div>

      <div className="advisor-validation-grid">
        <article
          className={`advisor-validation-card ${
            request.credit_validation.is_valid ? 'success' : 'warning'
          }`}
        >
          <span>Credit load</span>
          <strong>
            {request.credit_validation.selected_credits} credits
          </strong>
          <small>{request.credit_validation.message}</small>
        </article>

        <article
          className={`advisor-validation-card ${
            request.schedule_validation.has_conflicts ? 'warning' : 'success'
          }`}
        >
          <span>Schedule</span>
          <strong>
            {request.schedule_validation.has_conflicts
              ? `${request.schedule_validation.conflict_count} conflict${
                  request.schedule_validation.conflict_count === 1 ? '' : 's'
                }`
              : 'No conflicts'}
          </strong>
          <small>{request.schedule_validation.message}</small>
        </article>

        <article className="advisor-validation-card">
          <span>Waiting list</span>
          <strong>{request.waitlist_entries.length}</strong>
          <small>active waiting-list entries</small>
        </article>
      </div>

      <div className="advisor-course-review-list">
        {request.courses.map((item) => {
          const schedule = item.course.schedule || []
          const prerequisites = item.prerequisite_validation

          return (
            <article
              className="advisor-course-review"
              key={item.registration_id}
            >
              <div className="advisor-course-review-main">
                <div>
                  <span className="code-stamp">{item.course.code}</span>
                  <h3>{item.course.title}</h3>
                  <p>
                    Section {item.course.section || 'N/A'} ·{' '}
                    {item.course.credits} credits · {item.course.instructor}
                  </p>
                </div>
                <span
                  className={`advisor-prerequisite-state ${
                    prerequisites.eligible ? 'success' : 'warning'
                  }`}
                >
                  {prerequisites.eligible
                    ? 'Prerequisites met'
                    : 'Prerequisite issue'}
                </span>
              </div>

              <div className="advisor-course-review-meta">
                <span>
                  Seats available
                  <strong>{item.course.available_seats}</strong>
                </span>
                <span>
                  Schedule
                  <strong>
                    {schedule.length
                      ? schedule
                          .map(
                            (meeting) =>
                              `${meeting.day} ${meeting.start_time}–${meeting.end_time}`,
                          )
                          .join(', ')
                      : 'Not announced'}
                  </strong>
                </span>
              </div>

              {!prerequisites.eligible &&
                prerequisites.missing_prerequisites.length > 0 && (
                  <p className="advisor-prerequisite-warning">
                    Missing:{' '}
                    {prerequisites.missing_prerequisites
                      .map((requirement) => requirement.code)
                      .join(', ')}
                  </p>
                )}
            </article>
          )
        })}
      </div>

      {request.request_status === 'pending' ? (
        <div className="advisor-decision-box">
          <label>
            <span>Advisor comment</span>
            <textarea
              value={comment}
              maxLength={2000}
              placeholder="Add an optional approval note or a required rejection reason."
              onChange={(event) => setComment(event.target.value)}
            />
          </label>

          {decisionError && (
            <p className="advisor-decision-error">{decisionError}</p>
          )}

          <div className="advisor-decision-actions">
            <button
              className="advisor-reject-button"
              type="button"
              disabled={submitting}
              onClick={() => void decide('rejected')}
            >
              Reject request
            </button>
            <button
              className="advisor-approve-button"
              type="button"
              disabled={submitting}
              onClick={() => void decide('approved')}
            >
              {submitting ? 'Saving decision…' : 'Approve request'}
            </button>
          </div>
        </div>
      ) : (
        <div className="advisor-reviewed-box">
          <span>Advisor comment</span>
          <p>{request.advisor_comment || 'No advisor comment was recorded.'}</p>
          <small>Reviewed {formatDate(request.reviewed_at)}</small>
        </div>
      )}
    </section>
  )
}

export default function AdvisorDashboardPage() {
  const { token, user } = useAuth()
  const { activeSection } = useWorkspaceNavigation()
  const [statusFilter, setStatusFilter] =
    useState<AdvisorRequestStatus>('pending')
  const [requests, setRequests] = useState<
    AdvisorRegistrationRequestSummary[]
  >([])
  const [pagination, setPagination] = useState<PaginationMeta>({
    page: 1,
    page_size: 20,
    total_items: 0,
    total_pages: 0,
  })
  const [selectedRequestId, setSelectedRequestId] = useState<string | null>(
    null,
  )
  const [details, setDetails] =
    useState<AdvisorRegistrationRequestDetails | null>(null)
  const [loading, setLoading] = useState(true)
  const [detailLoading, setDetailLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [detailError, setDetailError] = useState('')
  const [feedback, setFeedback] = useState('')

  const loadRequests = useCallback(
    async (nextStatus = statusFilter, page = 1) => {
      if (!token) {
        return
      }

      setLoading(true)
      setError('')

      try {
        const result = await fetchAdvisorRequests(
          token,
          nextStatus,
          page,
          20,
        )
        setRequests(result.requests)
        setPagination(result.pagination)
      } catch (requestError) {
        setError(
          requestErrorMessage(
            requestError,
            'Advisor requests could not be loaded.',
          ),
        )
      } finally {
        setLoading(false)
      }
    },
    [statusFilter, token],
  )

  useEffect(() => {
    void loadRequests()
  }, [loadRequests])

  const selectRequest = async (requestId: string) => {
    if (!token) {
      return
    }

    setSelectedRequestId(requestId)
    setDetailLoading(true)
    setDetailError('')
    setFeedback('')

    try {
      const request = await fetchAdvisorRequest(token, requestId)
      setDetails(request)
    } catch (requestError) {
      setDetails(null)
      setDetailError(
        requestErrorMessage(
          requestError,
          'The request details could not be loaded.',
        ),
      )
    } finally {
      setDetailLoading(false)
    }
  }

  const changeFilter = (nextStatus: AdvisorRequestStatus) => {
    setStatusFilter(nextStatus)
    setSelectedRequestId(null)
    setDetails(null)
    setDetailError('')
    setFeedback('')
  }

  const handleDecision = async (
    decision: AdvisorDecision,
    comment: string,
  ) => {
    if (!token || !details || submitting) {
      return
    }

    setSubmitting(true)
    setDetailError('')
    setFeedback('')

    try {
      const result = await submitAdvisorDecision(
        token,
        details.request_id,
        decision,
        comment || null,
      )
      setFeedback(result.message)
      setSelectedRequestId(null)
      setDetails(null)
      await loadRequests(statusFilter, 1)
    } catch (requestError) {
      setDetailError(
        requestErrorMessage(
          requestError,
          'The advisor decision could not be saved.',
        ),
      )
    } finally {
      setSubmitting(false)
    }
  }

  const pageLabel = useMemo(() => {
    if (!pagination.total_items) {
      return '0 requests'
    }

    const start = (pagination.page - 1) * pagination.page_size + 1
    const end = Math.min(
      pagination.page * pagination.page_size,
      pagination.total_items,
    )
    return `${start}–${end} of ${pagination.total_items}`
  }, [pagination])

  const firstName = user?.name.trim().split(/\s+/)[0] || 'Advisor'
  const showOverview = sectionIsVisible(activeSection, 'advisor-overview')
  const showReviews = sectionIsVisible(activeSection, 'advisor-reviews')

  return (
    <main className="app-main advisor-main">
      {showOverview && (
        <>
          <section className="dashboard-hero advisor-hero">
        <div>
          <span className="page-eyebrow">Advisor workspace</span>
          <h1>Good to see you, {firstName}</h1>
          <p>
            Review assigned students&apos; registration requests, confirm
            academic checks, and record approval or rejection decisions.
          </p>
        </div>

        <button
          className="refresh-button"
          type="button"
          disabled={loading}
          onClick={() => void loadRequests(statusFilter, pagination.page)}
        >
          <span aria-hidden="true">↻</span>
          Refresh queue
        </button>
      </section>

      <section className="advisor-summary-grid" aria-label="Advisor queue summary">
        <SummaryCard
          label="Current filter"
          value={FILTERS.find((item) => item.value === statusFilter)?.label || ''}
          note="registration requests"
        />
        <SummaryCard
          label="Requests"
          value={pagination.total_items}
          note="matching this view"
        />
        <SummaryCard
          label="Page"
          value={
            pagination.total_pages
              ? `${pagination.page}/${pagination.total_pages}`
              : '—'
          }
          note={pageLabel}
        />
          </section>
        </>
      )}

      {feedback && (
        <div className="inline-alert success" role="status">
          <strong>Decision saved</strong>
          <span>{feedback}</span>
        </div>
      )}

      {showReviews && (
        <section className="advisor-workspace" id="advisor-review-queue">
        <div className="advisor-queue-panel">
          <div className="section-heading advisor-queue-heading">
            <div>
              <span className="section-eyebrow">Assigned students</span>
              <h2>Registration review queue</h2>
              <p>Only requests assigned to your advisor profile are shown.</p>
            </div>
          </div>

          <div
            className="advisor-filter-tabs"
            aria-label="Registration request status"
          >
            {FILTERS.map((item) => (
              <button
                key={item.value}
                className={statusFilter === item.value ? 'active' : ''}
                type="button"
                aria-pressed={statusFilter === item.value}
                onClick={() => changeFilter(item.value)}
              >
                {item.label}
              </button>
            ))}
          </div>

          {error && (
            <div className="inline-alert error" role="alert">
              <strong>Queue unavailable</strong>
              <span>{error}</span>
            </div>
          )}

          {loading ? (
            <div className="advisor-queue-empty">Loading review queue…</div>
          ) : requests.length === 0 ? (
            <div className="advisor-queue-empty">
              <span aria-hidden="true">✓</span>
              <div>
                <h3>No {statusFilter === 'all' ? '' : statusFilter} requests</h3>
                <p>There are no registration requests in this view.</p>
              </div>
            </div>
          ) : (
            <div className="advisor-request-list">
              {requests.map((request) => (
                <RequestCard
                  key={request.request_id}
                  request={request}
                  selected={selectedRequestId === request.request_id}
                  onSelect={() => void selectRequest(request.request_id)}
                />
              ))}
            </div>
          )}

          {pagination.total_pages > 1 && (
            <div className="advisor-pagination">
              <button
                type="button"
                disabled={loading || pagination.page <= 1}
                onClick={() =>
                  void loadRequests(statusFilter, pagination.page - 1)
                }
              >
                Previous
              </button>
              <span>{pageLabel}</span>
              <button
                type="button"
                disabled={
                  loading || pagination.page >= pagination.total_pages
                }
                onClick={() =>
                  void loadRequests(statusFilter, pagination.page + 1)
                }
              >
                Next
              </button>
            </div>
          )}
        </div>

        <div className="advisor-detail-column">
          {detailError && (
            <div className="inline-alert error" role="alert">
              <strong>Review unavailable</strong>
              <span>{detailError}</span>
            </div>
          )}

          {detailLoading ? (
            <div className="advisor-detail-empty">Loading request details…</div>
          ) : details ? (
            <RequestDetails
              request={details}
              submitting={submitting}
              onDecision={handleDecision}
            />
          ) : (
            <div className="advisor-detail-empty">
              <span aria-hidden="true">⌁</span>
              <div>
                <h3>Select a registration request</h3>
                <p>
                  Open a request to inspect courses, validations, and record
                  your advisor decision.
                </p>
              </div>
            </div>
          )}
        </div>
        </section>
      )}
    </main>
  )
}
