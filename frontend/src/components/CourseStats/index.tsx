import type { Course } from '../../types/course'

type CourseStatsProps = {
  courses: Course[]
}

function CourseStats({ courses }: CourseStatsProps) {
  const totalAvailableSeats = courses.reduce(
    (total, course) => total + course.available_seats,
    0,
  )

  const mandatoryCount = courses.filter((course) => course.is_mandatory).length
  const fullCount = courses.filter((course) => course.available_seats === 0).length

  return (
    <section className="ledger">
      <div className="ledger-row">
        <span className="label">Total courses</span>
        <span className="value">{courses.length}</span>
      </div>

      <div className="ledger-row">
        <span className="label">Open seats</span>
        <span className="value">{totalAvailableSeats}</span>
      </div>

      <div className="ledger-row">
        <span className="label">Mandatory</span>
        <span className="value">{mandatoryCount}</span>
      </div>

      <div className="ledger-row">
        <span className="label">Full</span>
        <span className="value">{fullCount}</span>
      </div>
    </section>
  )
}

export default CourseStats