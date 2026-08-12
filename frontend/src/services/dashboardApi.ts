import type {
  CurrentRegistrationPeriod,
  CurrentRegistrationPeriodResponse,
  RegistrationOverview,
  RegistrationOverviewResponse,
  RegistrationSummary,
} from '../types/dashboard'
import { ApiRequestError, requestJson } from './apiClient'

export { ApiRequestError }

export async function fetchCurrentRegistrationPeriod(
  token: string,
): Promise<CurrentRegistrationPeriod> {
  const response = await requestJson<CurrentRegistrationPeriodResponse>(
    '/api/registration-periods/current',
    {
      token,
      fallbackMessage: 'Registration-period status could not be loaded.',
      fallbackCode: 'REGISTRATION_PERIOD_REQUEST_FAILED',
    },
  )
  return response.data
}

export async function fetchRegistrationOverview(
  token: string,
): Promise<RegistrationOverview> {
  const response = await requestJson<RegistrationOverviewResponse>(
    '/api/registrations',
    {
      token,
      fallbackMessage: 'Registration summary could not be loaded.',
      fallbackCode: 'REGISTRATION_OVERVIEW_REQUEST_FAILED',
    },
  )
  return response.data
}

export function summarizeRegistrations(
  overview: RegistrationOverview,
): RegistrationSummary {
  const activeCreditStates = new Set(['draft', 'pending', 'approved'])

  return overview.registrations.reduce<RegistrationSummary>(
    (summary, registration) => {
      if (registration.registration_status === 'draft') {
        summary.selected += 1
      }

      if (registration.registration_status === 'pending') {
        summary.pending += 1
      }

      if (registration.registration_status === 'approved') {
        summary.approved += 1
      }

      if (registration.registration_status === 'rejected') {
        summary.rejected += 1
      }

      if (activeCreditStates.has(registration.registration_status)) {
        summary.selectedCredits += registration.course.credits
      }

      return summary
    },
    {
      selected: 0,
      pending: 0,
      approved: 0,
      rejected: 0,
      waitlisted: overview.waitlist_entries.length,
      selectedCredits: 0,
    },
  )
}
