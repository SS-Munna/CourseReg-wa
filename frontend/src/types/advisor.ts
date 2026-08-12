import type { Course } from './course'

export type AdvisorRequestStatus = 'pending' | 'approved' | 'rejected' | 'all'
export type AdvisorDecision = 'approved' | 'rejected'

export type PaginationMeta = {
  page: number
  page_size: number
  total_items: number
  total_pages: number
}

export type AdvisorReviewStudent = {
  student_id: string
  student_number: string
  full_name: string
  email: string
  program_code: string
  program_name: string
  current_trimester: number
  academic_status: string
}

export type AdvisorReviewCourseSummary = {
  registration_id: string
  course_id: string
  code: string
  title: string
  semester: string
  section: string
  credits: number
}

export type AdvisorRegistrationRequestSummary = {
  request_id: string
  request_status: Exclude<AdvisorRequestStatus, 'all'>
  submitted_at: string
  reviewed_at: string | null
  advisor_comment: string | null
  student: AdvisorReviewStudent
  course_count: number
  total_credits: number
  courses: AdvisorReviewCourseSummary[]
}

export type PrerequisiteRequirement = {
  course_id: string | null
  code: string
  title: string | null
  minimum_grade: string | null
  earned_grade: string | null
  satisfied: boolean
  reason: 'not_completed' | 'minimum_grade_not_met' | null
}

export type PrerequisiteValidation = {
  course_id: string
  code: string
  eligible: boolean
  requirements: PrerequisiteRequirement[]
  missing_prerequisites: PrerequisiteRequirement[]
}

export type AdvisorReviewCourseDetails = {
  registration_id: string
  registration_status: Exclude<AdvisorRequestStatus, 'all'>
  course: Course
  prerequisite_validation: PrerequisiteValidation
}

export type CreditLoadValidation = {
  selected_credits: number
  minimum_credit: number
  maximum_credit: number
  validation_status: 'below_minimum' | 'within_range' | 'above_maximum'
  is_valid: boolean
  minimum_shortfall: number
  maximum_excess: number
  message: string
}

export type ScheduleConflictValidation = {
  has_conflicts: boolean
  conflict_count: number
  conflicts: unknown[]
  message: string
}

export type AdvisorRegistrationRequestDetails = Omit<
  AdvisorRegistrationRequestSummary,
  'courses'
> & {
  reviewed_by_advisor_id: string | null
  courses: AdvisorReviewCourseDetails[]
  credit_validation: CreditLoadValidation
  schedule_validation: ScheduleConflictValidation
  waitlist_entries: unknown[]
}

export type AdvisorRequestListResponse = {
  success: boolean
  data: AdvisorRegistrationRequestSummary[]
  pagination: PaginationMeta
}

export type AdvisorRequestDetailsResponse = {
  success: boolean
  data: AdvisorRegistrationRequestDetails
}

export type AdvisorDecisionResponse = {
  success: boolean
  data: {
    request_id: string
    request_status: AdvisorDecision
    registration_ids: string[]
    reviewed_at: string
    reviewed_by_advisor_id: string
    advisor_comment: string | null
    notification_id: string
    audit_log_id: string
    message: string
  }
}
