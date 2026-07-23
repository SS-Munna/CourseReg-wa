import type { CourseFilters as CourseFilterValues } from '../../types/course'

type CourseFiltersProps = {
  filters: CourseFilterValues
  departments: string[]
  semesters: string[]
  onFiltersChange: (filters: CourseFilterValues) => void
  onApplyFilters: () => void
  onClearFilters: () => void
}

function CourseFilters({
  filters,
  departments,
  semesters,
  onFiltersChange,
  onApplyFilters,
  onClearFilters,
}: CourseFiltersProps) {
  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Search and filters</h2>
        <p>Narrow the list by department, semester, or seat availability.</p>
      </div>

      <div className="filters">
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

        <label className="check-field">
          <input
            type="checkbox"
            checked={Boolean(filters.mandatoryOnly)}
            onChange={(event) =>
              onFiltersChange({ ...filters, mandatoryOnly: event.target.checked })
            }
          />
          Mandatory only
        </label>

        <div className="actions">
          <button type="button" className="primary" onClick={onApplyFilters}>
            Apply filters
          </button>
          <button type="button" className="secondary" onClick={onClearFilters}>
            Clear
          </button>
        </div>
      </div>
    </section>
  )
}

export default CourseFilters