import { useMemo, useState } from 'react'

import type { CourseSchedule } from '../../types/course'
import type { StudentRegistration } from '../../types/dashboard'

type ApprovedScheduleProps = {
  registrations: StudentRegistration[]
  loading: boolean
  activeSemester: string | null
}

type ScheduleView = 'week' | 'list'

type ScheduledMeeting = {
  registration: StudentRegistration
  meeting: CourseSchedule
}

const WEEK_DAYS = [
  'Sunday',
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday',
]

function scheduleLabel(meeting: CourseSchedule): string {
  const room = meeting.room ? ` · ${meeting.room}` : ''
  return `${meeting.day} · ${meeting.start_time}–${meeting.end_time}${room}`
}

export default function ApprovedSchedule({
  registrations,
  loading,
  activeSemester,
}: ApprovedScheduleProps) {
  const [view, setView] = useState<ScheduleView>('week')

  const approvedRegistrations = useMemo(
    () =>
      registrations
        .filter(
          (registration) =>
            registration.registration_status === 'approved' &&
            (!activeSemester || registration.course.semester === activeSemester),
        )
        .sort((left, right) =>
          `${left.course.code}-${left.course.section || ''}`.localeCompare(
            `${right.course.code}-${right.course.section || ''}`,
          ),
        ),
    [activeSemester, registrations],
  )

  const meetingsByDay = useMemo(() => {
    const map = new Map<string, ScheduledMeeting[]>()

    approvedRegistrations.forEach((registration) => {
      registration.course.schedule?.forEach((meeting) => {
        const meetings = map.get(meeting.day) || []
        meetings.push({ registration, meeting })
        map.set(meeting.day, meetings)
      })
    })

    map.forEach((meetings) => {
      meetings.sort((left, right) =>
        left.meeting.start_time.localeCompare(right.meeting.start_time),
      )
    })

    return map
  }, [approvedRegistrations])

  const unscheduledRegistrations = approvedRegistrations.filter(
    (registration) => !registration.course.schedule?.length,
  )

  if (loading) {
    return (
      <section
        className="approved-schedule-section"
        id="timetable"
        aria-labelledby="approved-schedule-title"
      >
        <div className="section-heading">
          <div>
            <span className="section-eyebrow">Approved courses</span>
            <h2 id="approved-schedule-title">Weekly timetable</h2>
          </div>
        </div>
        <div className="schedule-panel-loading" role="status">
          Loading your approved schedule…
        </div>
      </section>
    )
  }

  return (
    <section
      className="approved-schedule-section"
      id="timetable"
      aria-labelledby="approved-schedule-title"
    >
      <div className="section-heading schedule-heading">
        <div>
          <span className="section-eyebrow">Approved courses</span>
          <h2 id="approved-schedule-title">Weekly timetable</h2>
          <p>
            {activeSemester
              ? `Your confirmed ${activeSemester} classes in weekly and list views.`
              : 'Your confirmed classes in weekly and list views.'}
          </p>
        </div>

        <div className="schedule-view-toggle" aria-label="Schedule view">
          <button
            type="button"
            className={view === 'week' ? 'is-active' : ''}
            aria-pressed={view === 'week'}
            onClick={() => setView('week')}
          >
            Weekly timetable
          </button>
          <button
            type="button"
            className={view === 'list' ? 'is-active' : ''}
            aria-pressed={view === 'list'}
            onClick={() => setView('list')}
          >
            List view
          </button>
        </div>
      </div>

      {approvedRegistrations.length === 0 ? (
        <div className="schedule-panel-empty">
          <span aria-hidden="true">□</span>
          <div>
            <h3>No approved courses yet</h3>
            <p>
              Courses will appear here after your advisor approves the registration.
            </p>
          </div>
        </div>
      ) : view === 'week' ? (
        <>
          <div className="weekly-timetable" aria-label="Approved weekly timetable">
            {WEEK_DAYS.map((day) => {
              const meetings = meetingsByDay.get(day) || []

              return (
                <article className="timetable-day" key={day}>
                  <div className="timetable-day-heading">
                    <strong>{day}</strong>
                    <span>{meetings.length} class{meetings.length === 1 ? '' : 'es'}</span>
                  </div>

                  {meetings.length > 0 ? (
                    <div className="timetable-meetings">
                      {meetings.map(({ registration, meeting }, index) => (
                        <div
                          className="timetable-meeting"
                          key={`${registration.registration_id}-${meeting.day}-${meeting.start_time}-${index}`}
                        >
                          <span className="code-stamp">{registration.course.code}</span>
                          <h3>{registration.course.title}</h3>
                          <p>
                            {meeting.start_time}–{meeting.end_time}
                            {meeting.room ? ` · ${meeting.room}` : ''}
                          </p>
                          <small>
                            Section {registration.course.section || 'N/A'} · {registration.course.instructor}
                          </small>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="timetable-empty-day">No approved classes</p>
                  )}
                </article>
              )
            })}
          </div>

          {unscheduledRegistrations.length > 0 && (
            <div className="unscheduled-courses" role="note">
              <strong>Schedule not announced</strong>
              <span>
                {unscheduledRegistrations
                  .map((registration) => registration.course.code)
                  .join(', ')}
              </span>
            </div>
          )}
        </>
      ) : (
        <div className="approved-course-list">
          {approvedRegistrations.map((registration) => {
            const { course } = registration
            const schedules = course.schedule || []

            return (
              <article className="approved-course-row" key={registration.registration_id}>
                <div className="approved-course-main">
                  <div className="approved-course-title">
                    <span className="code-stamp">{course.code}</span>
                    <span className="registration-badge status-approved">Approved</span>
                  </div>
                  <h3>{course.title}</h3>
                  <p>
                    Section {course.section || 'N/A'} · {course.credits} credits · {course.instructor}
                  </p>
                </div>

                <div className="approved-course-times">
                  {schedules.length > 0 ? (
                    schedules.map((meeting, index) => (
                      <span key={`${meeting.day}-${meeting.start_time}-${index}`}>
                        {scheduleLabel(meeting)}
                      </span>
                    ))
                  ) : (
                    <span className="schedule-missing">Schedule not announced</span>
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
