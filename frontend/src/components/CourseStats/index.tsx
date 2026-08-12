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
  const openCount = courses.filter((course) => course.available_seats > 0).length

  return (
    <section className="catalogue-stats" aria-label="Catalogue totals">
      <div className="ledger-row">
        <span className="label">Total courses</span>
        <span className="value">{courses.length}</span>
      </div>

      <div className="ledger-row">
        <span className="label">Seats available</span>
        <span className="value">{totalAvailableSeats}</span>
      </div>

      <div className="ledger-row">
        <span className="label">Mandatory</span>
        <span className="value">{mandatoryCount}</span>
      </div>

      <div className="ledger-row">
        <span className="label">Open sections</span>
        <span className="value">{openCount}</span>
      </div>
    </section>
  )
}

export default CourseStats
