import type { Course } from '../../types/course'

type CourseCardProps = {
  course: Course
  onViewDetails: (course: Course) => void
  onAddToSelection: (course: Course) => void
  onJoinWaitlist?: (course: Course) => void
  isSelected: boolean
  isWaitlisted?: boolean
  selectionBusy: boolean
  selectionLoading: boolean
  selectionDisabledReason: string
  waitlistBusy?: boolean
  waitlistLoading?: boolean
  waitlistDisabledReason?: string
}

function CourseCard({
  course,
  onViewDetails,
  onAddToSelection,
  onJoinWaitlist,
  isSelected,
  isWaitlisted = false,
  selectionBusy,
  selectionLoading,
  selectionDisabledReason,
  waitlistBusy = false,
  waitlistLoading = false,
  waitlistDisabledReason = '',
}: CourseCardProps) {
  const seatPercentage = Math.max(
    0,
    Math.min(100, (course.available_seats / course.capacity) * 100),
  )
  const waitlistMode =
    course.available_seats === 0 && !isSelected && Boolean(onJoinWaitlist)
  const actionReason = waitlistMode
    ? waitlistDisabledReason
    : selectionDisabledReason
  const actionBusy = waitlistMode ? waitlistBusy : selectionBusy
  const actionLoading = waitlistMode ? waitlistLoading : selectionLoading
  const actionDisabled = waitlistMode
    ? isWaitlisted || actionBusy || Boolean(actionReason)
    : isSelected || isWaitlisted || actionBusy || Boolean(actionReason)

  const actionLabel = isWaitlisted
    ? 'Waitlisted'
    : waitlistMode
      ? actionLoading
        ? 'Joining…'
        : 'Join waitlist'
      : isSelected
        ? 'Selected'
        : actionLoading
          ? 'Adding…'
          : 'Add to selection'

  return (
    <article className="course-card">
      <div className="course-top">
        <div>
          <div className="course-tags">
            <span className="code-stamp">{course.code}</span>
            <span className="course-type-tag">
              {course.is_mandatory ? 'Mandatory' : 'Elective'}
            </span>
          </div>
          <h3>{course.title}</h3>
          <p className="course-subtitle">
            {course.department} · {course.level || 'Undergraduate'}
          </p>
        </div>

        <span
          className={
            course.available_seats > 0
              ? 'seat-status available'
              : 'seat-status full'
          }
        >
          {course.available_seats > 0 ? 'Open' : 'Full'}
        </span>
      </div>

      <p className="description">
        {course.description || 'No description available.'}
      </p>

      <div className="course-facts">
        <div>
          <span>Credits</span>
          <strong>{course.credits}</strong>
        </div>
        <div>
          <span>Section</span>
          <strong>{course.section || 'N/A'}</strong>
        </div>
        <div>
          <span>Instructor</span>
          <strong>{course.instructor}</strong>
        </div>
      </div>

      <div className="seat-meter" aria-label={`${course.available_seats} seats available`}>
        <div className="seat-meter-copy">
          <span>Seat availability</span>
          <strong>
            {course.available_seats} of {course.capacity}
          </strong>
        </div>
        <div className="seat-meter-track" aria-hidden="true">
          <span style={{ width: `${seatPercentage}%` }} />
        </div>
      </div>

      <div className="course-card-footer">
        <div>
          <span>{course.semester}</span>
          <button
            className="details-button"
            type="button"
            onClick={() => onViewDetails(course)}
          >
            View section details
          </button>
        </div>
        <button
          className={waitlistMode ? 'selection-button waitlist-button' : 'selection-button'}
          type="button"
          onClick={() =>
            waitlistMode && onJoinWaitlist
              ? onJoinWaitlist(course)
              : onAddToSelection(course)
          }
          disabled={actionDisabled}
          title={
            actionReason ||
            (actionBusy ? 'Another registration update is in progress.' : undefined)
          }
        >
          {actionLabel}
        </button>
      </div>

      {!isSelected && !isWaitlisted && actionReason && (
        <small className="selection-help">{actionReason}</small>
      )}
    </article>
  )
}

export default CourseCard
