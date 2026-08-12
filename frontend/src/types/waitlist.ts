import type { Course } from './course'

export type WaitlistEntry = {
  waitlist_entry_id: string
  waitlist_status: 'active'
  joined_at: string
  queue_position: number
  total_waiting: number
  course: Course
  registration_status?: 'waitlisted'
}

export type WaitlistEntryResponse = {
  success: boolean
  data: WaitlistEntry
}

export type WaitlistLeaveResult = {
  waitlist_entry_id: string
  course_id: string
  waitlist_status: 'removed'
  removed_at: string
  previous_queue_position: number
  remaining_waiting: number
}

export type WaitlistLeaveResponse = {
  success: boolean
  data: WaitlistLeaveResult
}
