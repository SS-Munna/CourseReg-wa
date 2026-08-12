import type { FormEvent } from 'react'

import type { CourseFilters as CourseFilterValues } from '../../types/course'

type CourseFiltersProps = {
  filters: CourseFilterValues
  departments: string[]
  semesters: string[]
  levels: string[]
  onFiltersChange: (filters: CourseFilterValues) => void
  onApplyFilters: () => void
  onClearFilters: () => void
}

function CourseFilters({
  filters,
  departments,
  semesters,
  levels,
  onFiltersChange,
  onApplyFilters,
  onClearFilters,
}: CourseFiltersProps) {
  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    onApplyFilters()
  }

  return (
    <section className="catalogue-panel" aria-labelledby="catalogue-filters-title">
      <div className="panel-header">
        <div>
          <span className="section-eyebrow">Find your courses</span>
          <h2 id="catalogue-filters-title">Search and filters</h2>
        </div>
        <p>Search by course code or title, then refine the result.</p>
      </div>

      <form className="filters" onSubmit={handleSubmit}>
        <div className="field search-field">
          <label htmlFor="search">Search</label>
          <input
            id="search"
            type="text"
            placeholder="Course code or title"
            value={filters.search || ''}
            onChange={(event) =>
              onFiltersChange({ ...filters, search: event.target.value })
            }
          />
        </div>

        <div className="field">
          <label htmlFor="department">Department</label>
          <select
            id="department"
            value={filters.department || ''}
            onChange={(event) =>
              onFiltersChange({ ...filters, department: event.target.value })
            }
          >
            <option value="">All departments</option>
            {departments.map((department) => (
              <option key={department} value={department}>
                {department}
              </option>
            ))}
          </select>
        </div>

        <div className="field">
          <label htmlFor="semester">Semester</label>
          <select
            id="semester"
            value={filters.semester || ''}
            onChange={(event) =>
              onFiltersChange({ ...filters, semester: event.target.value })
            }
          >
            <option value="">All semesters</option>
            {semesters.map((semester) => (
              <option key={semester} value={semester}>
                {semester}
              </option>
            ))}
          </select>
        </div>

        <div className="field">
          <label htmlFor="level">Level</label>
          <select
            id="level"
            value={filters.level || ''}
            onChange={(event) =>
              onFiltersChange({ ...filters, level: event.target.value })
            }
          >
            <option value="">All levels</option>
            {levels.map((level) => (
              <option key={level} value={level}>
                {level}
              </option>
            ))}
          </select>
        </div>

        <div className="field">
          <label htmlFor="course-type">Course type</label>
          <select
            id="course-type"
            value={filters.courseType || 'all'}
            onChange={(event) =>
              onFiltersChange({
                ...filters,
                courseType: event.target.value as CourseFilterValues['courseType'],
              })
            }
          >
            <option value="all">All course types</option>
            <option value="mandatory">Mandatory</option>
            <option value="elective">Elective</option>
          </select>
        </div>

        <label className="check-field">
          <input
            type="checkbox"
            checked={Boolean(filters.availableOnly)}
            onChange={(event) =>
              onFiltersChange({ ...filters, availableOnly: event.target.checked })
            }
          />
          Available only
        </label>

        <div className="actions">
          <button type="submit" className="primary">
            Apply filters
          </button>
          <button type="button" className="secondary" onClick={onClearFilters}>
            Clear
          </button>
        </div>
      </form>
    </section>
  )
}

export default CourseFilters
