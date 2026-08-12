import { requestJson } from './apiClient'
import type {
  AdminAccountStatus,
  AdminOverview,
  AdminUser,
  AdvisorOption,
  AdminUserListResult,
  CreateStaffPayload,
  DepartmentOption,
  PaginationMeta,
  ProgramOption,
} from '../types/admin'

type SuccessResponse<Data> = {
  success: true
  data: Data
}

type PaginatedUsersResponse = {
  success: true
  data: AdminUser[]
  pagination: PaginationMeta
}

export async function fetchAdminOverview(
  token: string,
): Promise<AdminOverview> {
  const response = await requestJson<SuccessResponse<AdminOverview>>(
    '/api/admin/overview',
    {
      token,
      fallbackMessage: 'Administration overview could not be loaded.',
      fallbackCode: 'ADMIN_OVERVIEW_FAILED',
    },
  )

  return response.data
}

export async function fetchAdminUsers(
  token: string,
  search = '',
  page = 1,
): Promise<AdminUserListResult> {
  const params = new URLSearchParams({
    page: String(page),
    page_size: '25',
  })

  if (search.trim()) {
    params.set('search', search.trim())
  }

  const response = await requestJson<PaginatedUsersResponse>(
    `/api/admin/users?${params.toString()}`,
    {
      token,
      fallbackMessage: 'User access records could not be loaded.',
      fallbackCode: 'ADMIN_USERS_FAILED',
    },
  )

  return {
    users: response.data,
    pagination: response.pagination,
  }
}

export async function fetchDepartments(
  token: string,
): Promise<DepartmentOption[]> {
  const response = await requestJson<SuccessResponse<DepartmentOption[]>>(
    '/api/admin/departments',
    {
      token,
      fallbackMessage: 'Departments could not be loaded.',
      fallbackCode: 'ADMIN_DEPARTMENTS_FAILED',
    },
  )

  return response.data
}

export async function createStaffAccount(
  token: string,
  payload: CreateStaffPayload,
): Promise<AdminUser> {
  const response = await requestJson<SuccessResponse<AdminUser>>(
    '/api/admin/staff',
    {
      token,
      method: 'POST',
      body: payload,
      fallbackMessage: 'The staff account could not be created.',
      fallbackCode: 'ADMIN_CREATE_STAFF_FAILED',
    },
  )

  return response.data
}

export async function updateAccountAccess(
  token: string,
  userId: string,
  accountStatus: AdminAccountStatus,
): Promise<AdminUser> {
  const response = await requestJson<SuccessResponse<AdminUser>>(
    `/api/admin/users/${encodeURIComponent(userId)}/access`,
    {
      token,
      method: 'PATCH',
      body: {
        account_status: accountStatus,
      },
      fallbackMessage: 'The account access state could not be updated.',
      fallbackCode: 'ADMIN_UPDATE_ACCESS_FAILED',
    },
  )

  return response.data
}
export async function fetchPrograms(
  token: string,
): Promise<ProgramOption[]> {
  const response = await requestJson<SuccessResponse<ProgramOption[]>>(
    '/api/admin/programs',
    {
      token,
      fallbackMessage: 'Academic programs could not be loaded.',
      fallbackCode: 'ADMIN_PROGRAMS_FAILED',
    },
  )

  return response.data
}

export async function fetchAdvisorOptions(
  token: string,
): Promise<AdvisorOption[]> {
  const response = await requestJson<SuccessResponse<AdvisorOption[]>>(
    '/api/admin/advisors',
    {
      token,
      fallbackMessage: 'Advisor options could not be loaded.',
      fallbackCode: 'ADMIN_ADVISORS_FAILED',
    },
  )

  return response.data
}

export async function createStudentProfile(
  token: string,
  userId: string,
  payload: {
    program_id: string
    advisor_id: string
    student_number: string
    current_trimester: number
  },
): Promise<void> {
  await requestJson<SuccessResponse<unknown>>(
    `/api/admin/students/${encodeURIComponent(userId)}/profile`,
    {
      token,
      method: 'POST',
      body: payload,
      fallbackMessage: 'The student academic profile could not be linked.',
      fallbackCode: 'ADMIN_STUDENT_PROFILE_FAILED',
    },
  )
}

export async function createDepartment(
  token: string,
  payload: { code: string; name: string },
): Promise<DepartmentOption> {
  const response = await requestJson<SuccessResponse<DepartmentOption>>(
    '/api/admin/departments',
    {
      token,
      method: 'POST',
      body: payload,
      fallbackMessage: 'The department could not be created.',
      fallbackCode: 'ADMIN_CREATE_DEPARTMENT_FAILED',
    },
  )

  return response.data
}

export async function createProgram(
  token: string,
  payload: {
    department_id: string
    code: string
    name: string
    minimum_credit: number
    maximum_credit: number
  },
): Promise<ProgramOption> {
  const response = await requestJson<SuccessResponse<ProgramOption>>(
    '/api/admin/programs',
    {
      token,
      method: 'POST',
      body: payload,
      fallbackMessage: 'The academic program could not be created.',
      fallbackCode: 'ADMIN_CREATE_PROGRAM_FAILED',
    },
  )

  return response.data
}
