import { useEffect, useMemo, useState } from 'react'

import CourseCard from '../../components/CourseCard'
import CourseFilters from '../../components/CourseFilters'
import CourseStats from '../../components/CourseStats'
import { courseApiBaseUrl, fetchCourses } from '../../services/courseApi'
import type { Course, CourseFilters as CourseFilterValues } from '../../types/course'

function CourseCatalogPage() {
  const [courses, setCourses] = useState<Course[]>([])
  const [filters, setFilters] = useState<CourseFilterValues>({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const departments = useMemo(() => {
    return Array.from(new Set(courses.map((course) => course.department))).sort()
  }, [courses])

  const semesters = useMemo(() => {
    return Array.from(new Set(courses.map((course) => course.semester))).sort()
  }, [courses])

  const loadCourses = async (activeFilters: CourseFilterValues = filters) => {
    setLoading(true)
    setError('')

    try {
      const courseData = await fetchCourses(activeFilters)
      setCourses(courseData)
    } catch (err) {
      setCourses([])
      setError(
        err instanceof Error
          ? err.message
          : 'Something went wrong while loading courses.',
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadCourses({})
  }, [])

  const clearFilters = () => {
    const emptyFilters: CourseFilterValues = {}
    setFilters(emptyFilters)
    loadCourses(emptyFilters)
  }

  return (
    <>
      <section className="hero">
        <div className="hero-copy">
          <h1>Course Catalog</h1>
          <p>
            Search current course offerings, check available seats, review
            prerequisites, and prepare a registration plan.
          </p>
        </div>

        <button type="button" className="refresh-btn" onClick={() => loadCourses()}>
          Refresh catalog
        </button>
      </section>

      <CourseStats courses={courses} />

      <CourseFilters
        filters={filters}
        departments={departments}
        semesters={semesters}
        onFiltersChange={setFilters}
        onApplyFilters={() => loadCourses()}
        onClearFilters={clearFilters}
      />

      {loading && <div className="notice">Loading the course catalog...</div>}

      {error && (
        <section className="error-panel">
          <h2>Could not load the course catalog</h2>
          <p>{error}</p>
          <p>
            Start the FastAPI backend and confirm the course data source is
            reachable. For local development, the backend can return validated
            seed data when AWS credentials are not configured.
          </p>
          <code>{courseApiBaseUrl}/api/courses</code>
        </section>
      )}

      {!loading && !error && (
        <section className="course-section">
          <div className="section-title-row">
            <h2>Course list</h2>
            <p>{courses.length} course records returned from the backend API.</p>
          </div>

          <div className="course-grid">
            {courses.map((course) => (
              <CourseCard key={course.course_id} course={course} />
            ))}

            {courses.length === 0 && (
              <div className="empty-state">
                <h2>No courses match these filters</h2>
                <p>Clear a filter or try a different search term.</p>
              </div>
            )}
          </div>
        </section>
      )}
    </>
  )
}

export default CourseCatalogPage