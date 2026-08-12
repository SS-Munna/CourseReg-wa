import type {
  AddedSelectionResult,
  CreditLoadValidation,
  CreditLoadValidationResponse,
  DraftSelectionListResponse,
  DraftSelectionRemovedResponse,
  DraftSelectionResponse,
  FinalRegistrationSubmission,
  FinalRegistrationSubmissionResponse,
  ScheduleConflictValidation,
  ScheduleConflictValidationResponse,
  SelectionSnapshot,
} from '../types/selection'
import { requestJson } from './apiClient'

const selectionRequest = {
  fallbackMessage: 'Course selections could not be updated.',
  fallbackCode: 'SELECTION_REQUEST_FAILED',
}

export async function fetchDraftSelections(
  token: string,
): Promise<SelectionSnapshot> {
  const response = await requestJson<DraftSelectionListResponse>(
    '/api/selections',
    { token, ...selectionRequest },
  )

  return {
    selections: response.data,
    creditValidation: response.credit_validation,
  }
}

export async function addDraftSelection(
  token: string,
  courseId: string,
): Promise<AddedSelectionResult> {
  const response = await requestJson<DraftSelectionResponse>('/api/selections', {
    token,
    method: 'POST',
    body: { course_id: courseId },
    ...selectionRequest,
  })

  return {
    selection: response.data,
    creditValidation: response.credit_validation,
  }
}

export async function removeDraftSelection(
  token: string,
  courseId: string,
): Promise<CreditLoadValidation> {
  const response = await requestJson<DraftSelectionRemovedResponse>(
    `/api/selections/${encodeURIComponent(courseId)}`,
    { token, method: 'DELETE', ...selectionRequest },
  )

  return response.credit_validation
}

export async function validateFinalCreditLoad(
  token: string,
): Promise<CreditLoadValidation> {
  const response = await requestJson<CreditLoadValidationResponse>(
    '/api/selections/credit-validation',
    {
      token,
      method: 'POST',
      fallbackMessage: 'The selected credit load could not be validated.',
      fallbackCode: 'CREDIT_VALIDATION_FAILED',
    },
  )

  return response.data
}

export async function validateFinalSchedule(
  token: string,
): Promise<ScheduleConflictValidation> {
  const response = await requestJson<ScheduleConflictValidationResponse>(
    '/api/selections/schedule-conflict-validation',
    {
      token,
      method: 'POST',
      fallbackMessage: 'The selected class schedule could not be validated.',
      fallbackCode: 'SCHEDULE_VALIDATION_FAILED',
    },
  )

  return response.data
}

export async function submitRegistration(
  token: string,
): Promise<FinalRegistrationSubmission> {
  const response = await requestJson<FinalRegistrationSubmissionResponse>(
    '/api/registrations/submit',
    {
      token,
      method: 'POST',
      fallbackMessage: 'The registration request could not be submitted.',
      fallbackCode: 'REGISTRATION_SUBMISSION_FAILED',
    },
  )

  return response.data
}
