export type AdminAccountStatus =
  | 'pending'
  | 'active'
  | 'suspended'
  | 'rejected'

export type AdminUser = {
  id: string
  name: string
  email: string
  role: string
  account_status: AdminAccountStatus | string
  profile_status: 'linked' | 'missing' | 'not-required'
  created_at: string
}

export type AdminOverview = {
  total_users: number
  active_students: number
  active_advisors: number
  pending_staff: number
  suspended_accounts: number
  department_admins: number
  unlinked_students: number
}

export type ProgramOption = {
  id: string
  department_id: string
  department_code: string
  code: string
  name: string
  minimum_credit: number
  maximum_credit: number
}

export type AdvisorOption = {
  id: string
  user_id: string
  name: string
  email: string
  employee_number: string
  department_id: string
  department_code: string
}

export type DepartmentOption = {
  id: string
  code: string
  name: string
}

export type PaginationMeta = {
  page: number
  page_size: number
  total_items: number
  total_pages: number
}

export type AdminUserListResult = {
  users: AdminUser[]
  pagination: PaginationMeta
}

export type CreateStaffPayload = {
  name: string
  email: string
  password: string
  role: 'advisor' | 'department-admin'
  account_status: 'pending' | 'active'
  department_id?: string
  employee_number?: string
}
