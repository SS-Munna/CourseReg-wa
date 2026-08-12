import { useCallback, useEffect, useMemo, useState } from 'react'

import CourseCard from '../../components/CourseCard'
import CourseDetailsModal from '../../components/CourseDetailsModal'
import CourseFilters from '../../components/CourseFilters'
import CourseStats from '../../components/CourseStats'
import RegistrationReviewModal from '../../components/RegistrationReviewModal'
import RegistrationStatusPanel from '../../components/RegistrationStatusPanel'
import RegistrationWorkspace from '../../components/RegistrationWorkspace'
import WaitlistPanel from '../../components/WaitlistPanel'
import { useAuth } from '../../context/AuthContext'
import { ApiRequestError } from '../../services/apiClient'
import { fetchCourses } from '../../services/courseApi'
import {
  fetchCurrentRegistrationPeriod,
  fetchRegistrationOverview,
  summarizeRegistrations,
} from '../../services/dashboardApi'
import {
  addDraftSelection,
  fetchDraftSelections,
  removeDraftSelection,
  submitRegistration,
  validateFinalCreditLoad,
  validateFinalSchedule,
} from '../../services/selectionApi'
import type { Course, CourseFilters as CourseFilterValues } from '../../types/course'
import type {
  CurrentRegistrationPeriod,
  RegistrationOverview,
  RegistrationSummary,
} from '../../types/dashboard'
import type {
  CreditLoadValidation,
  DraftSelection,
  ScheduleConflictValidation,
} from '../../types/selection'
import { joinWaitlist, leaveWaitlist } from '../../services/waitlistApi'

const EMPTY_SUMMARY: RegistrationSummary = {
  selected: 0,
  pending: 0,
  approved: 0,
  rejected: 0,
  waitlisted: 0,
  selectedCredits: 0,
}

const EMPTY_OVERVIEW: RegistrationOverview = {
  registrations: [],
  waitlist_entries: [],
}

const summaryCards: Array<{
  key: keyof RegistrationSummary
  label: string
  hint: string
}> = [
  { key: 'selected', label: 'Draft selections', hint: 'Not submitted' },
  { key: 'pending', label: 'Pending review', hint: 'With your advisor' },
  { key: 'approved', label: 'Approved', hint: 'Confirmed courses' },
  { key: 'rejected', label: 'Rejected', hint: 'Needs attention' },
  { key: 'waitlisted', label: 'Waitlisted', hint: 'Awaiting a seat' },
  { key: 'selectedCredits', label: 'Selected credits', hint: 'Active course load' },
]

type SelectionFeedback = {
  tone: 'success' | 'error'
  message: string
}

type ReviewValidation = {
  credit: CreditLoadValidation
  schedule: ScheduleConflictValidation
}

function formatDateTime(value: string | null): string {
  if (!value) {
    return 'Not set'
  }

  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(new Date(value))
}

function statusLabel(period: CurrentRegistrationPeriod | null): string {
  if (!period) {
    return 'Status unavailable'
  }

  const labels = {
    open: 'Registration open',
    closed: 'Registration closed',
    upcoming: 'Registration upcoming',
    not_configured: 'Period not configured',
  }

  return labels[period.effective_status]
}

function isProfileError(error: unknown): boolean {
  return (
    error instanceof ApiRequestError &&
    error.code === 'STUDENT_PROFILE_NOT_FOUND'
  )
}

function prerequisiteDetail(details: unknown): string {
  if (!details || typeof details !== 'object') {
    return ''
  }

  const missing = (details as { missing_prerequisites?: unknown })
    .missing_prerequisites

  if (!Array.isArray(missing)) {
    return ''
  }

  const labels = missing.flatMap((item) => {
    if (!item || typeof item !== 'object') {
      return []
    }

    const requirement = item as {
      code?: unknown
      minimum_grade?: unknown
    }

    if (typeof requirement.code !== 'string') {
      return []
    }

    return [
      typeof requirement.minimum_grade === 'string'
        ? `${requirement.code} (minimum ${requirement.minimum_grade})`
        : requirement.code,
    ]
  })

  return labels.length > 0 ? ` Missing: ${labels.join(', ')}.` : ''
}

function registrationErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof ApiRequestError) {
    if (error.code === 'PREREQUISITES_NOT_MET') {
      return `${error.message}${prerequisiteDetail(error.details)}`
    }

    return error.message
  }

  return error instanceof Error ? error.message : fallback
}

function StudentDashboardPage() {
  const { token, user } = useAuth()
  const [courses, setCourses] = useState<Course[]>([])
  const [catalogueOptions, setCatalogueOptions] = useState<Course[]>([])
  const [filters, setFilters] = useState<CourseFilterValues>({ courseType: 'all' })
  const [catalogueLoading, setCatalogueLoading] = useState(true)
  const [catalogueError, setCatalogueError] = useState('')
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null)

  const [period, setPeriod] = useState<CurrentRegistrationPeriod | null>(null)
  const [summary, setSummary] = useState<RegistrationSummary>(EMPTY_SUMMARY)
  const [registrationOverview, setRegistrationOverview] =
    useState<RegistrationOverview>(EMPTY_OVERVIEW)
  const [dashboardLoading, setDashboardLoading] = useState(true)
  const [dashboardError, setDashboardError] = useState('')
  const [profileUnavailable, setProfileUnavailable] = useState(false)

  const [draftSelections, setDraftSelections] = useState<DraftSelection[]>([])
  const [creditValidation, setCreditValidation] =
    useState<CreditLoadValidation | null>(null)
  const [selectionLoading, setSelectionLoading] = useState(true)
  const [mutationCourseId, setMutationCourseId] = useState<string | null>(null)
  const [waitlistMutationCourseId, setWaitlistMutationCourseId] =
    useState<string | null>(null)
  const [selectionFeedback, setSelectionFeedback] =
    useState<SelectionFeedback | null>(null)
  const [validatingReview, setValidatingReview] = useState(false)
  const [reviewValidation, setReviewValidation] =
    useState<ReviewValidation | null>(null)
  const [reviewOpen, setReviewOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [submissionError, setSubmissionError] = useState('')

  const departments = useMemo(
    () =>
      Array.from(
        new Set(catalogueOptions.map((course) => course.department)),
      ).sort(),
    [catalogueOptions],
  )
  const semesters = useMemo(
    () =>
      Array.from(
        new Set(catalogueOptions.map((course) => course.semester)),
      ).sort(),
    [catalogueOptions],
  )
  const levels = useMemo(
    () =>
      Array.from(
        new Set(
          catalogueOptions
            .map((course) => course.level)
            .filter((level): level is string => Boolean(level)),
        ),
      ).sort(),
    [catalogueOptions],
  )
  const selectedCourseIds = useMemo(
    () => new Set(draftSelections.map((selection) => selection.course.course_id)),
    [draftSelections],
  )
  const selectedCourseCodes = useMemo(
    () =>
      new Set(
        draftSelections.map((selection) =>
          selection.course.code.trim().toUpperCase(),
        ),
      ),
    [draftSelections],
  )

  const waitlistedCourseIds = useMemo(
    () =>
      new Set(
        registrationOverview.waitlist_entries.map(
          (entry) => entry.course.course_id,
        ),
      ),
    [registrationOverview.waitlist_entries],
  )

  const loadCourses = useCallback(
    async (
      activeFilters: CourseFilterValues,
      captureOptions = false,
    ) => {
      setCatalogueLoading(true)
      setCatalogueError('')

      try {
        const courseData = await fetchCourses(activeFilters)
        setCourses(courseData)

        if (captureOptions) {
          setCatalogueOptions(courseData)
        }
      } catch (requestError) {
        setCourses([])
        setCatalogueError(
          requestError instanceof Error
            ? requestError.message
            : 'Something went wrong while loading courses.',
        )
      } finally {
        setCatalogueLoading(false)
      }
    },
    [],
  )

  const loadDashboard = useCallback(async () => {
    if (!token) {
      setDashboardLoading(false)
      setSelectionLoading(false)
      return
    }

    setDashboardLoading(true)
    setSelectionLoading(true)
    setDashboardError('')

    const [periodResult, overviewResult, selectionResult] =
      await Promise.allSettled([
        fetchCurrentRegistrationPeriod(token),
        fetchRegistrationOverview(token),
        fetchDraftSelections(token),
      ])
    const errors: string[] = []
    let profileMissing = false

    if (periodResult.status === 'fulfilled') {
      setPeriod(periodResult.value)
    } else {
      setPeriod(null)
      errors.push(
        periodResult.reason instanceof Error
          ? periodResult.reason.message
          : 'Registration-period status could not be loaded.',
      )
    }

    if (overviewResult.status === 'fulfilled') {
      setRegistrationOverview(overviewResult.value)
      setSummary(summarizeRegistrations(overviewResult.value))
    } else if (isProfileError(overviewResult.reason)) {
      setRegistrationOverview(EMPTY_OVERVIEW)
      setSummary(EMPTY_SUMMARY)
      profileMissing = true
    } else {
      setRegistrationOverview(EMPTY_OVERVIEW)
      setSummary(EMPTY_SUMMARY)
      errors.push(
        overviewResult.reason instanceof Error
          ? overviewResult.reason.message
          : 'Registration summary could not be loaded.',
      )
    }

    if (selectionResult.status === 'fulfilled') {
      setDraftSelections(selectionResult.value.selections)
      setCreditValidation(selectionResult.value.creditValidation)
    } else if (isProfileError(selectionResult.reason)) {
      setDraftSelections([])
      setCreditValidation(null)
      profileMissing = true
    } else {
      setDraftSelections([])
      setCreditValidation(null)
      errors.push(
        selectionResult.reason instanceof Error
          ? selectionResult.reason.message
          : 'Draft course selections could not be loaded.',
      )
    }

    setProfileUnavailable(profileMissing)
    setDashboardError(Array.from(new Set(errors)).join(' '))
    setDashboardLoading(false)
    setSelectionLoading(false)
  }, [token])

  const refreshRegistrationSummary = useCallback(async () => {
    if (!token) {
      return
    }

    try {
      const overview = await fetchRegistrationOverview(token)
      setRegistrationOverview(overview)
      setSummary(summarizeRegistrations(overview))
    } catch {
      // The mutation succeeded; the next full refresh will reconcile totals.
    }
  }, [token])

  useEffect(() => {
    void loadCourses({ courseType: 'all' }, true)
    void loadDashboard()
  }, [loadCourses, loadDashboard])

  const registrationUnavailableReason = useMemo(() => {
    if (profileUnavailable) {
      return 'Your academic student profile must be linked first.'
    }

    if (dashboardLoading) {
      return 'Registration status is still loading.'
    }

    if (!period) {
      return 'Registration status is currently unavailable.'
    }

    if (!period.registration_enabled) {
      return period.message
    }

    return ''
  }, [dashboardLoading, period, profileUnavailable])

  const courseSelectionDisabledReason = useCallback(
    (course: Course): string => {
      if (registrationUnavailableReason) {
        return registrationUnavailableReason
      }

      if (period?.semester && course.semester !== period.semester) {
        return `Only ${period.semester} sections can be selected now.`
      }

      if (
        !selectedCourseIds.has(course.course_id) &&
        selectedCourseCodes.has(course.code.trim().toUpperCase())
      ) {
        return `Another section of ${course.code} is already selected.`
      }

      return ''
    },
    [
      period,
      registrationUnavailableReason,
      selectedCourseCodes,
      selectedCourseIds,
    ],
  )

  const waitlistLeaveUnavailableReason = useMemo(() => {
    if (profileUnavailable) {
      return 'Your academic student profile must be linked first.'
    }

    if (dashboardLoading) {
      return 'Waiting-list status is still loading.'
    }

    return ''
  }, [dashboardLoading, profileUnavailable])

  const waitlistDisabledReason = useCallback(
    (course: Course): string => {
      if (registrationUnavailableReason) {
        return registrationUnavailableReason
      }

      if (period?.semester && course.semester !== period.semester) {
        return `Only ${period.semester} sections can be waitlisted now.`
      }

      if (selectedCourseIds.has(course.course_id)) {
        return 'This section is already in your draft selection.'
      }

      if (selectedCourseCodes.has(course.code.trim().toUpperCase())) {
        return `Another section of ${course.code} is already selected.`
      }

      return ''
    },
    [
      period,
      registrationUnavailableReason,
      selectedCourseCodes,
      selectedCourseIds,
    ],
  )

  const reviewUnavailableReason = useMemo(() => {
    if (!period?.semester) {
      return ''
    }

    const offTermSelection = draftSelections.find(
      (selection) => selection.course.semester !== period.semester,
    )

    return offTermSelection
      ? `Remove ${offTermSelection.course.code}; it is not offered in the active ${period.semester} period.`
      : ''
  }, [draftSelections, period])

  const clearFilters = () => {
    const emptyFilters: CourseFilterValues = { courseType: 'all' }
    setFilters(emptyFilters)
    void loadCourses(emptyFilters)
  }

  const refreshDashboard = () => {
    setSelectionFeedback(null)
    void Promise.all([loadDashboard(), loadCourses(filters)])
  }

  const closeCourseDetails = useCallback(() => {
    setSelectedCourse(null)
  }, [])

  const handleAddSelection = async (course: Course) => {
    if (!token || mutationCourseId) {
      return
    }

    const disabledReason = courseSelectionDisabledReason(course)

    if (disabledReason) {
      setSelectionFeedback({ tone: 'error', message: disabledReason })
      return
    }

    setMutationCourseId(course.course_id)
    setSelectionFeedback(null)

    try {
      const result = await addDraftSelection(token, course.course_id)
      const addedSelection = result.selection

      setDraftSelections((current) =>
        [...current, addedSelection].sort((left, right) =>
          `${left.course.code}-${left.course.section}`.localeCompare(
            `${right.course.code}-${right.course.section}`,
          ),
        ),
      )
      setCreditValidation(result.creditValidation)
      setSelectionFeedback({
        tone: 'success',
        message: `${course.code} section ${course.section || 'N/A'} was added as a draft.`,
      })
      void refreshRegistrationSummary()
    } catch (requestError) {
      setSelectionFeedback({
        tone: 'error',
        message: registrationErrorMessage(
          requestError,
          'This section could not be added to your selection.',
        ),
      })
    } finally {
      setMutationCourseId(null)
    }
  }

  const handleRemoveSelection = async (courseId: string) => {
    if (!token || mutationCourseId || registrationUnavailableReason) {
      return
    }

    const selection = draftSelections.find(
      (item) => item.course.course_id === courseId,
    )
    setMutationCourseId(courseId)
    setSelectionFeedback(null)

    try {
      const validation = await removeDraftSelection(token, courseId)
      setDraftSelections((current) =>
        current.filter((item) => item.course.course_id !== courseId),
      )
      setCreditValidation(validation)
      setSelectionFeedback({
        tone: 'success',
        message: `${selection?.course.code || 'The course'} was removed from your draft selection.`,
      })
      void refreshRegistrationSummary()
    } catch (requestError) {
      setSelectionFeedback({
        tone: 'error',
        message: registrationErrorMessage(
          requestError,
          'This draft selection could not be removed.',
        ),
      })
    } finally {
      setMutationCourseId(null)
    }
  }

  const handleJoinWaitlist = async (course: Course) => {
    if (!token || mutationCourseId || waitlistMutationCourseId) {
      return
    }

    const disabledReason = waitlistDisabledReason(course)

    if (disabledReason) {
      setSelectionFeedback({ tone: 'error', message: disabledReason })
      return
    }

    setWaitlistMutationCourseId(course.course_id)
    setSelectionFeedback(null)

    try {
      const entry = await joinWaitlist(token, course.course_id)
      setSelectionFeedback({
        tone: 'success',
        message: `${course.code} joined the waiting list at position #${entry.queue_position}.`,
      })
      await loadDashboard()
    } catch (requestError) {
      setSelectionFeedback({
        tone: 'error',
        message: registrationErrorMessage(
          requestError,
          'This section could not be added to the waiting list.',
        ),
      })
    } finally {
      setWaitlistMutationCourseId(null)
    }
  }

  const handleLeaveWaitlist = async (courseId: string) => {
    if (!token || mutationCourseId || waitlistMutationCourseId) {
      return
    }

    const entry = registrationOverview.waitlist_entries.find(
      (item) => item.course.course_id === courseId,
    )

    setWaitlistMutationCourseId(courseId)
    setSelectionFeedback(null)

    try {
      await leaveWaitlist(token, courseId)
      setSelectionFeedback({
        tone: 'success',
        message: `${entry?.course.code || 'The course'} was removed from your waiting list.`,
      })
      await loadDashboard()
    } catch (requestError) {
      setSelectionFeedback({
        tone: 'error',
        message: registrationErrorMessage(
          requestError,
          'This waiting-list request could not be removed.',
        ),
      })
    } finally {
      setWaitlistMutationCourseId(null)
    }
  }

  const handleReviewSelection = async () => {
    if (
      !token ||
      validatingReview ||
      registrationUnavailableReason ||
      reviewUnavailableReason
    ) {
      return
    }

    setValidatingReview(true)
    setSelectionFeedback(null)

    try {
      const [credit, schedule] = await Promise.all([
        validateFinalCreditLoad(token),
        validateFinalSchedule(token),
      ])
      setReviewValidation({ credit, schedule })
      setSubmissionError('')
      setReviewOpen(true)
    } catch (requestError) {
      setSelectionFeedback({
        tone: 'error',
        message: registrationErrorMessage(
          requestError,
          'The selection could not be validated for final review.',
        ),
      })
    } finally {
      setValidatingReview(false)
    }
  }

  const closeRegistrationReview = useCallback(() => {
    if (!submitting) {
      setReviewOpen(false)
      setSubmissionError('')
    }
  }, [submitting])

  const handleSubmitRegistration = async () => {
    if (!token || submitting) {
      return
    }

    setSubmitting(true)
    setSubmissionError('')

    try {
      const submission = await submitRegistration(token)
      setReviewOpen(false)
      setReviewValidation(null)
      setSelectionFeedback({
        tone: 'success',
        message: `${submission.submitted_count} course${submission.submitted_count === 1 ? '' : 's'} submitted for advisor review.`,
      })
      await Promise.all([loadDashboard(), loadCourses(filters)])
    } catch (requestError) {
      setSubmissionError(
        registrationErrorMessage(
          requestError,
          'Your registration could not be submitted.',
        ),
      )
    } finally {
      setSubmitting(false)
    }
  }

  const firstName = user?.name.trim().split(/\s+/)[0] || 'Student'
  const periodClass = period?.effective_status || 'unavailable'
  const selectedModalReason = selectedCourse
    ? courseSelectionDisabledReason(selectedCourse)
    : ''
  const selectedModalWaitlistReason = selectedCourse
    ? waitlistDisabledReason(selectedCourse)
    : ''
  const courseActionBusy = Boolean(mutationCourseId || waitlistMutationCourseId)

  return (
    <main className="app-main">
      <section className="dashboard-hero">
        <div>
          <span className="page-eyebrow">Student dashboard</span>
          <h1>Welcome back, {firstName}</h1>
          <p>
            Track your registration progress, build a valid course selection,
            and submit it for advisor review from one place.
          </p>
        </div>
        <button className="refresh-button" type="button" onClick={refreshDashboard}>
          <span aria-hidden="true">↻</span>
          Refresh dashboard
        </button>
      </section>

      <section className={`period-card period-${periodClass}`}>
        <div className="period-status-icon" aria-hidden="true">
          {period?.registration_enabled ? '✓' : 'i'}
        </div>
        <div className="period-copy">
          <div className="period-title-row">
            <span>{statusLabel(period)}</span>
            {period?.semester && <strong>{period.semester}</strong>}
          </div>
          <p>
            {period?.message ||
              'The registration-period service is temporarily unavailable. Course browsing remains available.'}
          </p>
          {period && period.effective_status !== 'not_configured' && (
            <div className="period-meta">
              <span>
                <small>Opens</small>
                {formatDateTime(period.opening_time)}
              </span>
              <span>
                <small>Closes</small>
                {formatDateTime(period.closing_time)}
              </span>
              <span>
                <small>Credit range</small>
                {period.minimum_credit ?? '—'}–{period.maximum_credit ?? '—'} credits
              </span>
            </div>
          )}
        </div>
      </section>

      {dashboardError && (
        <div className="inline-alert error" role="alert">
          <strong>Some dashboard data is unavailable.</strong>
          <span>{dashboardError}</span>
        </div>
      )}

      {profileUnavailable && (
        <div className="inline-alert info" role="status">
          <strong>Your account is ready; the academic profile is still being set up.</strong>
          <span>
            Registration actions will unlock after an administrator links your
            student profile. You can browse the full catalogue now.
          </span>
        </div>
      )}

      <section className="summary-section" aria-labelledby="summary-title">
        <div className="section-heading">
          <div>
            <span className="section-eyebrow">At a glance</span>
            <h2 id="summary-title">Registration summary</h2>
          </div>
          <span className="summary-note">
            {dashboardLoading ? 'Updating…' : 'Current registration records'}
          </span>
        </div>

        <div className={`summary-grid ${dashboardLoading ? 'is-loading' : ''}`}>
          {summaryCards.map((card) => (
            <article className={`summary-card summary-${card.key}`} key={card.key}>
              <span>{card.label}</span>
              <strong>{summary[card.key]}</strong>
              <small>{card.hint}</small>
            </article>
          ))}
        </div>
      </section>

      {selectionFeedback && (
        <div
          className={`inline-alert ${selectionFeedback.tone}`}
          role={selectionFeedback.tone === 'error' ? 'alert' : 'status'}
        >
          <strong>
            {selectionFeedback.tone === 'success'
              ? 'Registration updated.'
              : 'Registration needs attention.'}
          </strong>
          <span>{selectionFeedback.message}</span>
        </div>
      )}

      <RegistrationStatusPanel
        overview={registrationOverview}
        loading={dashboardLoading}
      />

      <WaitlistPanel
        entries={registrationOverview.waitlist_entries}
        loading={dashboardLoading}
        mutationCourseId={waitlistMutationCourseId}
        actionsEnabled={!waitlistLeaveUnavailableReason}
        unavailableReason={waitlistLeaveUnavailableReason}
        onLeave={(courseId) => void handleLeaveWaitlist(courseId)}
      />

      <RegistrationWorkspace
        selections={draftSelections}
        creditValidation={creditValidation}
        loading={selectionLoading}
        mutationCourseId={mutationCourseId}
        validatingReview={validatingReview}
        actionsEnabled={!registrationUnavailableReason}
        unavailableReason={registrationUnavailableReason}
        reviewUnavailableReason={reviewUnavailableReason}
        onRemove={(courseId) => void handleRemoveSelection(courseId)}
        onReview={() => void handleReviewSelection()}
      />

      <section className="catalogue-section" id="catalogue" aria-labelledby="catalogue-title">
        <div className="section-heading catalogue-heading">
          <div>
            <span className="section-eyebrow">Course planning</span>
            <h2 id="catalogue-title">Course catalogue</h2>
            <p>Compare sections, schedules, prerequisites, and live seat availability.</p>
          </div>
          <span className="result-count">
            {catalogueLoading ? 'Loading…' : `${courses.length} results`}
          </span>
        </div>

        <CourseStats courses={courses} />

        <CourseFilters
          filters={filters}
          departments={departments}
          semesters={semesters}
          levels={levels}
          onFiltersChange={setFilters}
          onApplyFilters={() => void loadCourses(filters)}
          onClearFilters={clearFilters}
        />

        {catalogueLoading && (
          <div className="catalogue-loading" role="status">
            <span className="spinner" aria-hidden="true" />
            Loading course options…
          </div>
        )}

        {catalogueError && (
          <section className="catalogue-error" role="alert">
            <div>
              <h3>Could not load the course catalogue</h3>
              <p>{catalogueError}</p>
            </div>
            <button type="button" onClick={() => void loadCourses(filters)}>
              Try again
            </button>
          </section>
        )}

        {!catalogueLoading && !catalogueError && (
          <div className="course-grid">
            {courses.map((course) => (
              <CourseCard
                key={course.course_id}
                course={course}
                onViewDetails={setSelectedCourse}
                onAddToSelection={(item) => void handleAddSelection(item)}
                onJoinWaitlist={(item) => void handleJoinWaitlist(item)}
                isSelected={selectedCourseIds.has(course.course_id)}
                isWaitlisted={waitlistedCourseIds.has(course.course_id)}
                selectionBusy={courseActionBusy}
                selectionLoading={mutationCourseId === course.course_id}
                selectionDisabledReason={courseSelectionDisabledReason(course)}
                waitlistBusy={courseActionBusy}
                waitlistLoading={waitlistMutationCourseId === course.course_id}
                waitlistDisabledReason={waitlistDisabledReason(course)}
              />
            ))}

            {courses.length === 0 && (
              <div className="empty-state">
                <span aria-hidden="true">⌕</span>
                <h3>No courses match these filters</h3>
                <p>Clear a filter or try a different course code or title.</p>
                <button type="button" onClick={clearFilters}>
                  Clear all filters
                </button>
              </div>
            )}
          </div>
        )}
      </section>

      {selectedCourse && (
        <CourseDetailsModal
          course={selectedCourse}
          onClose={closeCourseDetails}
          onAddToSelection={(course) => void handleAddSelection(course)}
          onJoinWaitlist={(course) => void handleJoinWaitlist(course)}
          isSelected={selectedCourseIds.has(selectedCourse.course_id)}
          isWaitlisted={waitlistedCourseIds.has(selectedCourse.course_id)}
          selectionBusy={courseActionBusy}
          selectionLoading={mutationCourseId === selectedCourse.course_id}
          selectionDisabledReason={selectedModalReason}
          waitlistBusy={courseActionBusy}
          waitlistLoading={waitlistMutationCourseId === selectedCourse.course_id}
          waitlistDisabledReason={selectedModalWaitlistReason}
        />
      )}

      {reviewOpen && reviewValidation && (
        <RegistrationReviewModal
          selections={draftSelections}
          creditValidation={reviewValidation.credit}
          scheduleValidation={reviewValidation.schedule}
          submitting={submitting}
          error={submissionError}
          onClose={closeRegistrationReview}
          onSubmit={() => void handleSubmitRegistration()}
        />
      )}
    </main>
  )
}

export default StudentDashboardPage
