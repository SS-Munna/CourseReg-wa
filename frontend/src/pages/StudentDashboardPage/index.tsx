import { useCallback, useEffect, useMemo, useState } from 'react'

import CourseCard from '../../components/CourseCard'
import CourseDetailsModal from '../../components/CourseDetailsModal'
import CourseFilters from '../../components/CourseFilters'
import CourseStats from '../../components/CourseStats'
import { useAuth } from '../../context/AuthContext'
import {
  ApiRequestError,
  fetchCurrentRegistrationPeriod,
  fetchRegistrationOverview,
  summarizeRegistrations,
} from '../../services/dashboardApi'
import { fetchCourses } from '../../services/courseApi'
import type { Course, CourseFilters as CourseFilterValues } from '../../types/course'
import type {
  CurrentRegistrationPeriod,
  RegistrationSummary,
} from '../../types/dashboard'

const EMPTY_SUMMARY: RegistrationSummary = {
  selected: 0,
  pending: 0,
  approved: 0,
  rejected: 0,
  waitlisted: 0,
  selectedCredits: 0,
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
  const [dashboardLoading, setDashboardLoading] = useState(true)
  const [dashboardError, setDashboardError] = useState('')
  const [profileUnavailable, setProfileUnavailable] = useState(false)

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
      return
    }

    setDashboardLoading(true)
    setDashboardError('')
    setProfileUnavailable(false)

    const [periodResult, overviewResult] = await Promise.allSettled([
      fetchCurrentRegistrationPeriod(token),
      fetchRegistrationOverview(token),
    ])
    const errors: string[] = []

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
      setSummary(summarizeRegistrations(overviewResult.value))
    } else if (
      overviewResult.reason instanceof ApiRequestError &&
      overviewResult.reason.code === 'STUDENT_PROFILE_NOT_FOUND'
    ) {
      setSummary(EMPTY_SUMMARY)
      setProfileUnavailable(true)
    } else {
      setSummary(EMPTY_SUMMARY)
      errors.push(
        overviewResult.reason instanceof Error
          ? overviewResult.reason.message
          : 'Registration summary could not be loaded.',
      )
    }

    setDashboardError(errors.join(' '))
    setDashboardLoading(false)
  }, [token])

  useEffect(() => {
    void loadCourses({ courseType: 'all' }, true)
    void loadDashboard()
  }, [loadCourses, loadDashboard])

  const clearFilters = () => {
    const emptyFilters: CourseFilterValues = { courseType: 'all' }
    setFilters(emptyFilters)
    void loadCourses(emptyFilters)
  }

  const refreshDashboard = () => {
    void Promise.all([loadDashboard(), loadCourses(filters)])
  }

  const closeCourseDetails = useCallback(() => {
    setSelectedCourse(null)
  }, [])

  const firstName = user?.name.trim().split(/\s+/)[0] || 'Student'
  const periodClass = period?.effective_status || 'unavailable'

  return (
    <main className="app-main">
      <section className="dashboard-hero">
        <div>
          <span className="page-eyebrow">Student dashboard</span>
          <h1>Welcome back, {firstName}</h1>
          <p>
            Track your registration progress and explore every available course
            section from one place.
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
            Registration totals will appear after an administrator links your student
            profile. You can browse the full catalogue now.
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
        <CourseDetailsModal course={selectedCourse} onClose={closeCourseDetails} />
      )}
    </main>
  )
}

export default StudentDashboardPage
