import type {
  CurrentRegistrationPeriod,
  CurrentRegistrationPeriodResponse,
  RegistrationOverview,
  RegistrationOverviewResponse,
  RegistrationSummary,
} from '../types/dashboard'

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

type ApiErrorPayload = {
  error?: {
    code?: string
    message?: string
  }
}

export class ApiRequestError extends Error {
  code: string
  status: number

  constructor(message: string, code: string, status: number) {
    super(message)
    this.name = 'ApiRequestError'
    this.code = code
    this.status = status
  }
}

async function requestJson<ResponseData>(
  path: string,
  token: string,
): Promise<ResponseData> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })
  const payload = (await response.json()) as ResponseData & ApiErrorPayload

  if (!response.ok) {
    throw new ApiRequestError(
      payload.error?.message || 'Dashboard data could not be loaded.',
      payload.error?.code || 'DASHBOARD_REQUEST_FAILED',
      response.status,
    )
  }

  return payload
}

export async function fetchCurrentRegistrationPeriod(
  token: string,
): Promise<CurrentRegistrationPeriod> {
  const response = await requestJson<CurrentRegistrationPeriodResponse>(
    '/api/registration-periods/current',
    token,
  )
  return response.data
}

export async function fetchRegistrationOverview(
  token: string,
): Promise<RegistrationOverview> {
  const response = await requestJson<RegistrationOverviewResponse>(
    '/api/registrations',
    token,
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
