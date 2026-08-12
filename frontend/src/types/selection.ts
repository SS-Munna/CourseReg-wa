import type { Course } from './course'

export type CreditLoadStatus =
  | 'below_minimum'
  | 'within_range'
  | 'above_maximum'

export type CreditLoadValidation = {
  selected_credits: number
  minimum_credit: number
  maximum_credit: number
  validation_status: CreditLoadStatus
  is_valid: boolean
  minimum_shortfall: number
  maximum_excess: number
  message: string
}

export type DraftSelection = {
  registration_id: string
  registration_status: 'draft'
  course: Course
}

export type SelectionSnapshot = {
  selections: DraftSelection[]
  creditValidation: CreditLoadValidation
}

export type AddedSelectionResult = {
  selection: DraftSelection
  creditValidation: CreditLoadValidation
}

export type DraftSelectionListResponse = {
  success: boolean
  data: DraftSelection[]
  credit_validation: CreditLoadValidation
}

export type DraftSelectionResponse = {
  success: boolean
  data: DraftSelection
  credit_validation: CreditLoadValidation
}

export type DraftSelectionRemovedResponse = {
  success: boolean
  data: {
    registration_id: string
    course_id: string
  }
  credit_validation: CreditLoadValidation
}

export type ScheduleConflictCourse = {
  course_id: string
  code: string
  title: string
  section: string
  registration_status: 'draft' | 'pending' | 'approved'
  start_time: string
  end_time: string
}

export type ScheduleConflict = {
  selected_course: ScheduleConflictCourse
  conflicting_course: ScheduleConflictCourse
  day: string
  overlap_start_time: string
  overlap_end_time: string
  message: string
}

export type ScheduleConflictValidation = {
  has_conflicts: boolean
  conflict_count: number
  conflicts: ScheduleConflict[]
  message: string
}

export type ScheduleConflictValidationResponse = {
  success: boolean
  data: ScheduleConflictValidation
}

export type CreditLoadValidationResponse = {
  success: boolean
  data: CreditLoadValidation
}

export type FinalRegistrationSubmission = {
  registration_status: 'pending'
  submitted_count: number
  submitted_at: string
  registrations: Array<{
    registration_id: string
    registration_status: 'pending'
    submitted_at: string
    course: Course
  }>
  credit_validation: CreditLoadValidation
  schedule_validation: ScheduleConflictValidation
  message: string
}

export type FinalRegistrationSubmissionResponse = {
  success: boolean
  data: FinalRegistrationSubmission
}
