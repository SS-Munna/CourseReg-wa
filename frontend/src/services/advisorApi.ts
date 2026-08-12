import type {
  AdvisorDecision,
  AdvisorDecisionResponse,
  AdvisorRegistrationRequestDetails,
  AdvisorRegistrationRequestSummary,
  AdvisorRequestDetailsResponse,
  AdvisorRequestListResponse,
  AdvisorRequestStatus,
  PaginationMeta,
} from '../types/advisor'
import { requestJson } from './apiClient'

export type AdvisorRequestListResult = {
  requests: AdvisorRegistrationRequestSummary[]
  pagination: PaginationMeta
}

export async function fetchAdvisorRequests(
  token: string,
  status: AdvisorRequestStatus = 'pending',
  page = 1,
  pageSize = 20,
): Promise<AdvisorRequestListResult> {
  const params = new URLSearchParams({
    status,
    page: String(page),
    page_size: String(pageSize),
  })

  const response = await requestJson<AdvisorRequestListResponse>(
    `/api/advisor/registration-requests?${params.toString()}`,
    {
      token,
      fallbackMessage: 'Advisor registration requests could not be loaded.',
      fallbackCode: 'ADVISOR_REQUESTS_LOAD_FAILED',
    },
  )

  return {
    requests: response.data,
    pagination: response.pagination,
  }
}

export async function fetchAdvisorRequest(
  token: string,
  requestId: string,
): Promise<AdvisorRegistrationRequestDetails> {
  const response = await requestJson<AdvisorRequestDetailsResponse>(
    `/api/advisor/registration-requests/${requestId}`,
    {
      token,
      fallbackMessage: 'The registration request details could not be loaded.',
      fallbackCode: 'ADVISOR_REQUEST_DETAILS_FAILED',
    },
  )

  return response.data
}

export async function submitAdvisorDecision(
  token: string,
  requestId: string,
  decision: AdvisorDecision,
  comment: string | null,
): Promise<AdvisorDecisionResponse['data']> {
  const response = await requestJson<AdvisorDecisionResponse>(
    `/api/advisor/registration-requests/${requestId}/decision`,
    {
      token,
      method: 'POST',
      body: {
        decision,
        comment,
      },
      fallbackMessage: 'The advisor decision could not be saved.',
      fallbackCode: 'ADVISOR_DECISION_FAILED',
    },
  )

  return response.data
}
