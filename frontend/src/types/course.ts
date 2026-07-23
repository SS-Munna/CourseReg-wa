export type CourseSchedule = {
  day: string
  start_time: string
  end_time: string
  room?: string
}

export type Course = {
  course_id: string
  code: string
  title: string
  department: string
  semester: string
  instructor: string
  credits: number
  capacity: number
  available_seats: number
  is_mandatory: boolean
  level?: string
  description?: string
  prerequisites?: string[]
  section?: string
  schedule?: CourseSchedule[]
}

export type CourseApiResponse = {
  success: boolean
  data: Course[]
}

export type CourseFilters = {
  search?: string
  department?: string
  semester?: string
  availableOnly?: boolean
  mandatoryOnly?: boolean
}