import type { Course } from './course'
import type { WaitlistEntry } from './waitlist'

export type RegistrationState =
  | 'draft'
  | 'pending'
  | 'approved'
  | 'rejected'
  | 'dropped'

export type DropEligibilityReason =
  | 'eligible'
  | 'registration_not_approved'
  | 'drop_period_not_configured'
  | 'drop_deadline_passed'

export type DropEligibility = {
  eligible: boolean
  drop_deadline: string | null
  reason: DropEligibilityReason
  message: string
}

export type StudentRegistration = {
  registration_id: string
  registration_status: RegistrationState
  submitted_at: string | null
  reviewed_at: string | null
  reviewed_by_advisor_id: string | null
  advisor_comment: string | null
  updated_at: string
  course: Course
  drop_eligibility: DropEligibility
}

export type RegistrationOverview = {
  registrations: StudentRegistration[]
  waitlist_entries: WaitlistEntry[]
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
