import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { AuthProvider } from '../context/AuthContext'
import AdminDashboardPage from '../pages/AdminDashboardPage'
import {
  createDepartment,
  createProgram,
  createStaffAccount,
  createStudentProfile,
  fetchAdminOverview,
  fetchAdminUsers,
  fetchAdvisorOptions,
  fetchDepartments,
  fetchPrograms,
  updateAccountAccess,
} from '../services/adminApi'

vi.mock('../services/adminApi', () => ({
  createDepartment: vi.fn(),
  createProgram: vi.fn(),
  createStaffAccount: vi.fn(),
  createStudentProfile: vi.fn(),
  fetchAdminOverview: vi.fn(),
  fetchAdminUsers: vi.fn(),
  fetchAdvisorOptions: vi.fn(),
  fetchDepartments: vi.fn(),
  fetchPrograms: vi.fn(),
  updateAccountAccess: vi.fn(),
}))

const overview = {
  total_users: 3,
  active_students: 1,
  active_advisors: 1,
  pending_staff: 0,
  suspended_accounts: 0,
  department_admins: 0,
  unlinked_students: 1,
}

const adminUser = {
  id: 'system-admin-1',
  name: 'System Admin',
  email: 'admin@example.com',
  role: 'system-admin',
  account_status: 'active',
  profile_status: 'not-required' as const,
  created_at: '2026-08-13T00:00:00Z',
}

const studentUser = {
  id: 'student-1',
  name: 'Samira Rahman',
  email: 'samira@example.com',
  role: 'student',
  account_status: 'active',
  profile_status: 'missing' as const,
  created_at: '2026-08-12T00:00:00Z',
}

beforeEach(() => {
  localStorage.setItem(
    'coursepilot_user',
    JSON.stringify({
      id: 'system-admin-1',
      name: 'System Admin',
      email: 'admin@example.com',
      role: 'system-admin',
    }),
  )
  localStorage.setItem('coursepilot_token', 'admin-token')

  vi.mocked(fetchAdminOverview).mockResolvedValue(overview)
  vi.mocked(fetchAdminUsers).mockResolvedValue({
    users: [adminUser, studentUser],
    pagination: {
      page: 1,
      page_size: 25,
      total_items: 2,
      total_pages: 1,
    },
  })
  vi.mocked(fetchDepartments).mockResolvedValue([
    {
      id: 'department-1',
      code: 'CSE',
      name: 'Computer Science',
    },
  ])
  vi.mocked(fetchPrograms).mockResolvedValue([
    {
      id: 'program-1',
      department_id: 'department-1',
      department_code: 'CSE',
      code: 'BSC-CSE',
      name: 'BSc in CSE',
      minimum_credit: 9,
      maximum_credit: 18,
    },
  ])
  vi.mocked(fetchAdvisorOptions).mockResolvedValue([
    {
      id: 'advisor-profile-1',
      user_id: 'advisor-user-1',
      name: 'Dr. Nadia',
      email: 'nadia@example.com',
      employee_number: 'FAC-001',
      department_id: 'department-1',
      department_code: 'CSE',
    },
  ])
  vi.mocked(createStaffAccount).mockResolvedValue({
    id: 'advisor-1',
    name: 'Dr. Nadia',
    email: 'nadia@example.com',
    role: 'advisor',
    account_status: 'active',
    profile_status: 'linked',
    created_at: '2026-08-13T00:00:00Z',
  })
  vi.mocked(updateAccountAccess).mockResolvedValue({
    ...studentUser,
    account_status: 'suspended',
  })
  vi.mocked(createStudentProfile).mockResolvedValue()
  vi.mocked(createDepartment).mockResolvedValue({
    id: 'department-2',
    code: 'EEE',
    name: 'Electrical and Electronic Engineering',
  })
  vi.mocked(createProgram).mockResolvedValue({
    id: 'program-2',
    department_id: 'department-2',
    department_code: 'EEE',
    code: 'BSC-EEE',
    name: 'BSc in EEE',
    minimum_credit: 9,
    maximum_credit: 18,
  })
})

describe('AdminDashboardPage', () => {
  it('shows account oversight and protects the signed-in system admin', async () => {
    render(
      <AuthProvider>
        <AdminDashboardPage />
      </AuthProvider>,
    )

    expect(
      await screen.findByRole('heading', { name: 'Account administration' }),
    ).toBeVisible()
    expect(screen.getByText('Samira Rahman')).toBeVisible()
    expect(screen.getByText('Protected account')).toBeVisible()
    expect(screen.getByText('Active students')).toBeVisible()
  })

  it('provisions a complete advisor account from the admin workspace', async () => {
    const user = userEvent.setup()

    render(
      <AuthProvider>
        <AdminDashboardPage />
      </AuthProvider>,
    )

    await screen.findByRole('heading', { name: 'Create staff account' })

    await user.type(screen.getByLabelText('Full name'), 'Dr. Nadia')
    await user.type(screen.getByLabelText('Email'), 'nadia@example.com')
    await user.type(
      screen.getByLabelText('Temporary password'),
      'TemporaryPass123!',
    )
    const staffForm = screen
      .getByRole('button', { name: 'Create staff account' })
      .closest('form')

    if (!staffForm) {
      throw new Error('Create staff account form was not found')
    }

    await user.selectOptions(
      within(staffForm).getByLabelText('Department'),
      'department-1',
    )
    await user.type(screen.getByLabelText('Employee number'), 'FAC-001')
    await user.click(
      screen.getByRole('button', { name: 'Create staff account' }),
    )

    await waitFor(() => {
      expect(createStaffAccount).toHaveBeenCalledWith(
        'admin-token',
        expect.objectContaining({
          name: 'Dr. Nadia',
          email: 'nadia@example.com',
          role: 'advisor',
          department_id: 'department-1',
          employee_number: 'FAC-001',
        }),
      )
    })
  })

  it('suspends a manageable account through the access API', async () => {
    const user = userEvent.setup()

    render(
      <AuthProvider>
        <AdminDashboardPage />
      </AuthProvider>,
    )

    await screen.findByText('Samira Rahman')
    await user.click(screen.getByRole('button', { name: 'Suspend' }))

    await waitFor(() => {
      expect(updateAccountAccess).toHaveBeenCalledWith(
        'admin-token',
        'student-1',
        'suspended',
      )
    })
  })
  it('links a self-registered student to an academic profile', async () => {
    const user = userEvent.setup()

    render(
      <AuthProvider>
        <AdminDashboardPage />
      </AuthProvider>,
    )

    await screen.findByText('Samira Rahman')
    await user.click(screen.getByRole('button', { name: 'Link profile' }))

    await user.type(screen.getByLabelText('Student number'), 'STU-001')
    await user.selectOptions(
      screen.getByLabelText('Program'),
      'program-1',
    )
    await user.selectOptions(
      screen.getByLabelText('Advisor'),
      'advisor-profile-1',
    )
    await user.click(
      screen.getByRole('button', { name: 'Link student profile' }),
    )

    await waitFor(() => {
      expect(createStudentProfile).toHaveBeenCalledWith(
        'admin-token',
        'student-1',
        {
          program_id: 'program-1',
          advisor_id: 'advisor-profile-1',
          student_number: 'STU-001',
          current_trimester: 1,
        },
      )
    })
  })

})
