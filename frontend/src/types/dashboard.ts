import type { Course } from './course'

export type RegistrationState =
  | 'draft'
  | 'pending'
  | 'approved'
  | 'rejected'
  | 'dropped'

export type StudentRegistration = {
  registration_id: string
  registration_status: RegistrationState
  course: Course
}

export type RegistrationOverview = {
  registrations: StudentRegistration[]
  waitlist_entries: Array<{
    registration_status: 'waitlisted'
  }>
}

export type RegistrationOverviewResponse = {
  success: boolean
  data: RegistrationOverview
}

export type RegistrationPeriodStatus =
  | 'open'
  | 'closed'
  | 'upcoming'
  | 'not_configured'

export type CurrentRegistrationPeriod = {
  effective_status: RegistrationPeriodStatus
  registration_enabled: boolean
  semester: string | null
  opening_time: string | null
  closing_time: string | null
  drop_deadline: string | null
  minimum_credit: number | null
  maximum_credit: number | null
  message: string
}

export type CurrentRegistrationPeriodResponse = {
  success: boolean
  data: CurrentRegistrationPeriod
}

export type RegistrationSummary = {
  selected: number
  pending: number
  approved: number
  rejected: number
  waitlisted: number
  selectedCredits: number
}
