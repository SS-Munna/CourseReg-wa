import type { Course, CourseApiResponse, CourseFilters } from '../types/course'

const API_BASE_URL = 'http://127.0.0.1:8000'

export const courseApiBaseUrl = API_BASE_URL

export async function fetchCourses(filters: CourseFilters = {}): Promise<Course[]> {
  const params = new URLSearchParams()

  if (filters.search?.trim()) {
    params.append('search', filters.search.trim())
  }

  if (filters.department) {
    params.append('department', filters.department)
  }

  if (filters.semester) {
    params.append('semester', filters.semester)
  }

  if (filters.availableOnly) {
    params.append('available_only', 'true')
  }

  if (filters.mandatoryOnly) {
    params.append('is_mandatory', 'true')
  }

  const queryString = params.toString()
  const url = `${API_BASE_URL}/api/courses${queryString ? `?${queryString}` : ''}`

  const response = await fetch(url)

  if (!response.ok) {
    throw new Error('The course catalog API is not available right now.')
  }

  const result: CourseApiResponse = await response.json()
  return result.data
}