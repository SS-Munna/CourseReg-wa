import type { Course } from '../../types/course'

type CourseCardProps = {
  course: Course
}

function CourseCard({ course }: CourseCardProps) {
  return (
    <article className="course-card">
      <span className="code-stamp">{course.code}</span>

      <div className="course-top">
        <div>
          <h3>{course.title}</h3>
          {course.is_mandatory && <span className="mandatory-tag">Mandatory</span>}
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

      <div className="info-grid">
        <div>
          <span>Department</span>
          <strong>{course.department}</strong>
        </div>
        <div>
          <span>Semester</span>
          <strong>{course.semester}</strong>
        </div>
        <div>
          <span>Credits</span>
          <strong>{course.credits}</strong>
        </div>
        <div>
          <span>Seats</span>
          <strong>
            {course.available_seats}/{course.capacity}
          </strong>
        </div>
      </div>

      <div className="course-footer">
        <p>
          <strong>Instructor:</strong> {course.instructor}
        </p>
        <p>
          <strong>Section:</strong> {course.section || 'N/A'}
        </p>
        <p>
          <strong>Prerequisite:</strong>{' '}
          {course.prerequisites && course.prerequisites.length > 0
            ? course.prerequisites.join(', ')
            : 'None'}
        </p>
      </div>

      {course.schedule && course.schedule.length > 0 && (
        <div className="schedule">
          <span>Schedule</span>
          {course.schedule.map((item) => (
            <p key={`${course.course_id}-${item.day}-${item.start_time}`}>
              {item.day} · {item.start_time}–{item.end_time}
              {item.room ? ` · ${item.room}` : ''}
            </p>
          ))}
        </div>
      )}
    </article>
  )
}

export default CourseCard