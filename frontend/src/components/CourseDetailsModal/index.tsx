import { useEffect, useState } from 'react'

import { fetchSectionAvailability } from '../../services/courseApi'
import type { Course, SectionAvailability } from '../../types/course'

type CourseDetailsModalProps = {
  course: Course
  onClose: () => void
}

function CourseDetailsModal({ course, onClose }: CourseDetailsModalProps) {
  const [details, setDetails] = useState<Course | SectionAvailability>(course)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let isActive = true

    fetchSectionAvailability(course.course_id)
      .then((section) => {
        if (isActive) {
          setDetails(section)
        }
      })
      .catch((requestError: unknown) => {
        if (isActive) {
          setError(
            requestError instanceof Error
              ? requestError.message
              : 'Live availability could not be refreshed.',
          )
        }
      })
      .finally(() => {
        if (isActive) {
          setLoading(false)
        }
      })

    return () => {
      isActive = false
    }
  }, [course])

  useEffect(() => {
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose()
      }
    }

    window.addEventListener('keydown', handleKeyDown)

    return () => {
      document.body.style.overflow = previousOverflow
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [onClose])

  const isFull =
    'is_full' in details ? details.is_full : details.available_seats === 0
  const enrollment =
    'enrollment' in details
      ? details.enrollment
      : Math.max(details.capacity - details.available_seats, 0)

  return (
    <div
      className="modal-backdrop"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          onClose()
        }
      }}
    >
      <section
        className="course-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="course-modal-title"
      >
        <header className="modal-header">
          <div>
            <div className="course-tags">
              <span className="code-stamp">{details.code}</span>
              <span className="course-type-tag">
                {details.is_mandatory ? 'Mandatory' : 'Elective'}
              </span>
            </div>
            <h2 id="course-modal-title">{details.title}</h2>
            <p>
              {details.department} · {details.semester}
            </p>
          </div>
          <button
            className="modal-close"
            type="button"
            onClick={onClose}
            aria-label="Close section details"
            autoFocus
          >
            ×
          </button>
        </header>

        <div className="modal-body">
          <section className="availability-callout">
            <div>
              <span className={`status-dot ${isFull ? 'full' : 'open'}`} />
              <div>
                <strong>{isFull ? 'Section full' : 'Seats available'}</strong>
                <p>
                  {details.available_seats} available · {enrollment} enrolled ·{' '}
                  {details.capacity} capacity
                </p>
              </div>
            </div>
            <span className="live-label">
              {loading ? 'Refreshing…' : error ? 'Last known' : 'Live data'}
            </span>
          </section>

          {error && <p className="inline-warning">{error} Showing catalogue data.</p>}

          <p className="modal-description">
            {details.description || 'No course description is available.'}
          </p>

          <div className="detail-grid">
            <div>
              <span>Section</span>
              <strong>{details.section || 'N/A'}</strong>
            </div>
            <div>
              <span>Instructor</span>
              <strong>{details.instructor}</strong>
            </div>
            <div>
              <span>Credits</span>
              <strong>{details.credits}</strong>
            </div>
            <div>
              <span>Level</span>
              <strong>{details.level || 'Undergraduate'}</strong>
            </div>
          </div>

          <section className="detail-section">
            <h3>Class schedule</h3>
            {details.schedule && details.schedule.length > 0 ? (
              <div className="schedule-list">
                {details.schedule.map((meeting) => (
                  <div
                    key={`${meeting.day}-${meeting.start_time}-${meeting.room || ''}`}
                  >
                    <strong>{meeting.day}</strong>
                    <span>
                      {meeting.start_time}–{meeting.end_time}
                    </span>
                    <span>{meeting.room || 'Room to be announced'}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p>Schedule to be announced.</p>
            )}
          </section>

          <section className="detail-section">
            <h3>Prerequisites</h3>
            <p>
              {details.prerequisites && details.prerequisites.length > 0
                ? details.prerequisites.join(', ')
                : 'No prerequisites required.'}
            </p>
          </section>
        </div>
      </section>
    </div>
  )
}

export default CourseDetailsModal
