import type {
  WaitlistEntry,
  WaitlistEntryResponse,
  WaitlistLeaveResponse,
  WaitlistLeaveResult,
} from '../types/waitlist'
import { requestJson } from './apiClient'

const waitlistRequest = {
  fallbackMessage: 'The waiting list could not be updated.',
  fallbackCode: 'WAITLIST_REQUEST_FAILED',
}

export async function joinWaitlist(
  token: string,
  courseId: string,
): Promise<WaitlistEntry> {
  const response = await requestJson<WaitlistEntryResponse>('/api/waitlists', {
    token,
    method: 'POST',
    body: { course_id: courseId },
    ...waitlistRequest,
  })

  return response.data
}

export async function leaveWaitlist(
  token: string,
  courseId: string,
): Promise<WaitlistLeaveResult> {
  const response = await requestJson<WaitlistLeaveResponse>(
    `/api/waitlists/${encodeURIComponent(courseId)}`,
    {
      token,
      method: 'DELETE',
      ...waitlistRequest,
    },
  )

  return response.data
}
