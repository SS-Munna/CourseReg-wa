import { useCallback, useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'

import AuditLogPanel from '../../components/AuditLogPanel'
import { useAuth } from '../../context/AuthContext'
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
} from '../../services/adminApi'
import { ApiRequestError } from '../../services/apiClient'
import {
  isTrimmedLengthBetween,
  isValidEmail,
  parseIntegerInRange,
} from '../../utils/validation'
import type {
  AdminAccountStatus,
  AdminOverview,
  AdminUser,
  CreateStaffPayload,
  AdvisorOption,
  DepartmentOption,
  PaginationMeta,
  ProgramOption,
} from '../../types/admin'

const EMPTY_OVERVIEW: AdminOverview = {
  total_users: 0,
  active_students: 0,
  active_advisors: 0,
  pending_staff: 0,
  suspended_accounts: 0,
  department_admins: 0,
  unlinked_students: 0,
}

const EMPTY_PAGINATION: PaginationMeta = {
  page: 1,
  page_size: 25,
  total_items: 0,
  total_pages: 0,
}

const STATUS_LABELS: Record<string, string> = {
  pending: 'Pending',
  active: 'Active',
  suspended: 'Suspended',
  rejected: 'Rejected',
}

const ROLE_LABELS: Record<string, string> = {
  student: 'Student',
  advisor: 'Advisor',
  'department-admin': 'Department admin',
  'system-admin': 'System admin',
}

function errorMessage(error: unknown, fallback: string): string {
  if (error instanceof ApiRequestError || error instanceof Error) {
    return error.message
  }

  return fallback
}

function formatDate(value: string): string {
  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return value
  }

  return new Intl.DateTimeFormat('en', {
    dateStyle: 'medium',
  }).format(date)
}

function SummaryCard({
  label,
  value,
  note,
}: {
  label: string
  value: number
  note: string
}) {
  return (
    <article className="admin-summary-card">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{note}</small>
    </article>
  )
}

export default function AdminDashboardPage() {
  const { token, user } = useAuth()
  const isSystemAdmin = user?.role === 'system-admin'

  const [overview, setOverview] = useState<AdminOverview>(EMPTY_OVERVIEW)
  const [users, setUsers] = useState<AdminUser[]>([])
  const [departments, setDepartments] = useState<DepartmentOption[]>([])
  const [programs, setPrograms] = useState<ProgramOption[]>([])
  const [advisorOptions, setAdvisorOptions] = useState<AdvisorOption[]>([])
  const [pagination, setPagination] =
    useState<PaginationMeta>(EMPTY_PAGINATION)
  const [search, setSearch] = useState('')
  const [appliedSearch, setAppliedSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [savingUserId, setSavingUserId] = useState<string | null>(null)
  const [error, setError] = useState('')
  const [feedback, setFeedback] = useState('')

  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] =
    useState<CreateStaffPayload['role']>('advisor')
  const [accountStatus, setAccountStatus] =
    useState<CreateStaffPayload['account_status']>('active')
  const [departmentId, setDepartmentId] = useState('')
  const [employeeNumber, setEmployeeNumber] = useState('')
  const [creating, setCreating] = useState(false)
  const [formError, setFormError] = useState('')

  const [selectedStudent, setSelectedStudent] = useState<AdminUser | null>(null)
  const [studentNumber, setStudentNumber] = useState('')
  const [studentTrimester, setStudentTrimester] = useState('1')
  const [studentProgramId, setStudentProgramId] = useState('')
  const [studentAdvisorId, setStudentAdvisorId] = useState('')
  const [linkingStudent, setLinkingStudent] = useState(false)
  const [studentFormError, setStudentFormError] = useState('')

  const [departmentCode, setDepartmentCode] = useState('')
  const [departmentName, setDepartmentName] = useState('')
  const [programDepartmentId, setProgramDepartmentId] = useState('')
  const [programCode, setProgramCode] = useState('')
  const [programName, setProgramName] = useState('')
  const [programMinimumCredit, setProgramMinimumCredit] = useState('9')
  const [programMaximumCredit, setProgramMaximumCredit] = useState('18')
  const [academicSetupError, setAcademicSetupError] = useState('')
  const [savingAcademicSetup, setSavingAcademicSetup] = useState(false)

  const loadDashboard = useCallback(
    async (query = appliedSearch, page = 1) => {
      if (!token) {
        return
      }

      setLoading(true)
      setError('')

      try {
        const [
          nextOverview,
          nextUsers,
          nextDepartments,
          nextPrograms,
          nextAdvisors,
        ] = await Promise.all([
          fetchAdminOverview(token),
          fetchAdminUsers(token, query, page),
          fetchDepartments(token),
          fetchPrograms(token),
          fetchAdvisorOptions(token),
        ])

        setOverview(nextOverview)
        setUsers(nextUsers.users)
        setPagination(nextUsers.pagination)
        setDepartments(nextDepartments)
        setPrograms(nextPrograms)
        setAdvisorOptions(nextAdvisors)
      } catch (requestError) {
        setError(
          errorMessage(
            requestError,
            'The administration workspace could not be loaded.',
          ),
        )
      } finally {
        setLoading(false)
      }
    },
    [appliedSearch, token],
  )

  useEffect(() => {
    void loadDashboard()
  }, [loadDashboard])

  const canManage = (target: AdminUser): boolean => {
    if (!user || target.id === user.id) {
      return false
    }

    if (user.role === 'department-admin') {
      return target.role === 'advisor'
    }

    return target.role !== 'system-admin'
  }

  const submitSearch = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const nextSearch = search.trim()
    setAppliedSearch(nextSearch)
    void loadDashboard(nextSearch, 1)
  }

  const changeAccess = async (
    target: AdminUser,
    nextStatus: AdminAccountStatus,
  ) => {
    if (!token || !canManage(target) || savingUserId) {
      return
    }

    setSavingUserId(target.id)
    setError('')
    setFeedback('')

    try {
      const updated = await updateAccountAccess(
        token,
        target.id,
        nextStatus,
      )
      setUsers((currentUsers) =>
        currentUsers.map((item) =>
          item.id === updated.id ? updated : item,
        ),
      )
      setFeedback(
        `${updated.name} is now ${STATUS_LABELS[updated.account_status]?.toLowerCase() || updated.account_status}.`,
      )
      const nextOverview = await fetchAdminOverview(token)
      setOverview(nextOverview)
    } catch (requestError) {
      setError(
        errorMessage(
          requestError,
          'Account access could not be updated.',
        ),
      )
    } finally {
      setSavingUserId(null)
    }
  }

  const createStaff = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setFormError('')
    setFeedback('')

    const trimmedName = name.trim()
    const trimmedEmail = email.trim()
    const trimmedEmployeeNumber = employeeNumber.trim()

    if (!trimmedName || !trimmedEmail || !password) {
      setFormError('Name, email, and temporary password are required.')
      return
    }

    if (!isTrimmedLengthBetween(trimmedName, 2, 255)) {
      setFormError('Staff name must be between 2 and 255 characters.')
      return
    }

    if (!isValidEmail(trimmedEmail)) {
      setFormError('Enter a valid staff email address.')
      return
    }

    if (password.length < 8 || password.length > 128) {
      setFormError('Temporary password must be between 8 and 128 characters.')
      return
    }

    if (
      role === 'advisor' &&
      (!departmentId || !isTrimmedLengthBetween(trimmedEmployeeNumber, 2, 64))
    ) {
      setFormError(
        'Select a department and enter a 2–64 character employee number for the advisor.',
      )
      return
    }

    if (!token) {
      return
    }

    setCreating(true)

    try {
      await createStaffAccount(token, {
        name: trimmedName,
        email: trimmedEmail,
        password,
        role,
        account_status: accountStatus,
        ...(role === 'advisor'
          ? {
              department_id: departmentId,
              employee_number: trimmedEmployeeNumber,
            }
          : {}),
      })

      setName('')
      setEmail('')
      setPassword('')
      setEmployeeNumber('')
      setDepartmentId('')
      setRole('advisor')
      setAccountStatus('active')
      setFeedback('Staff account created successfully.')
      await loadDashboard(appliedSearch, 1)
    } catch (requestError) {
      setFormError(
        errorMessage(
          requestError,
          'The staff account could not be created.',
        ),
      )
    } finally {
      setCreating(false)
    }
  }

const linkStudentProfile = async (
  event: FormEvent<HTMLFormElement>,
) => {
  event.preventDefault()
  setStudentFormError('')
  setFeedback('')

  if (!selectedStudent || !token) {
    setStudentFormError('Select an unlinked student account first.')
    return
  }

  const trimester = parseIntegerInRange(studentTrimester, 1, 30)

  if (
    !isTrimmedLengthBetween(studentNumber, 2, 64) ||
    !studentProgramId ||
    !studentAdvisorId ||
    trimester === null
  ) {
    setStudentFormError(
      'Enter a 2–64 character student number, program, advisor, and trimester from 1 to 30.',
    )
    return
  }

  const program = programs.find(
    (item) => item.id === studentProgramId,
  )
  const advisor = advisorOptions.find(
    (item) => item.id === studentAdvisorId,
  )

  if (
    !program ||
    !advisor ||
    program.department_id !== advisor.department_id
  ) {
    setStudentFormError(
      'Choose an advisor from the same department as the program.',
    )
    return
  }

  setLinkingStudent(true)

  try {
    await createStudentProfile(token, selectedStudent.id, {
      program_id: studentProgramId,
      advisor_id: studentAdvisorId,
      student_number: studentNumber.trim(),
      current_trimester: trimester,
    })
    setSelectedStudent(null)
    setStudentNumber('')
    setStudentTrimester('1')
    setStudentProgramId('')
    setStudentAdvisorId('')
    setFeedback('Student academic profile linked successfully.')
    await loadDashboard(appliedSearch, pagination.page)
  } catch (requestError) {
    setStudentFormError(
      errorMessage(
        requestError,
        'The student academic profile could not be linked.',
      ),
    )
  } finally {
    setLinkingStudent(false)
  }
}

const saveDepartment = async (
  event: FormEvent<HTMLFormElement>,
) => {
  event.preventDefault()
  setAcademicSetupError('')
  setFeedback('')

  if (
    !token ||
    !isTrimmedLengthBetween(departmentCode, 2, 32) ||
    !isTrimmedLengthBetween(departmentName, 2, 255)
  ) {
    setAcademicSetupError(
      'Department code must be 2–32 characters and name 2–255 characters.',
    )
    return
  }

  setSavingAcademicSetup(true)

  try {
    const department = await createDepartment(token, {
      code: departmentCode.trim(),
      name: departmentName.trim(),
    })
    setDepartments((current) => [...current, department])
    setDepartmentCode('')
    setDepartmentName('')
    setFeedback('Department created successfully.')
  } catch (requestError) {
    setAcademicSetupError(
      errorMessage(requestError, 'The department could not be created.'),
    )
  } finally {
    setSavingAcademicSetup(false)
  }
}

const saveProgram = async (
  event: FormEvent<HTMLFormElement>,
) => {
  event.preventDefault()
  setAcademicSetupError('')
  setFeedback('')

  const minimumCredit = parseIntegerInRange(programMinimumCredit, 0, 60)
  const maximumCredit = parseIntegerInRange(programMaximumCredit, 0, 60)

  if (
    !token ||
    !programDepartmentId ||
    !isTrimmedLengthBetween(programCode, 2, 32) ||
    !isTrimmedLengthBetween(programName, 2, 255) ||
    minimumCredit === null ||
    maximumCredit === null ||
    maximumCredit < minimumCredit
  ) {
    setAcademicSetupError(
      'Choose a department, use valid program details, and keep credits between 0 and 60 with maximum not below minimum.',
    )
    return
  }

  setSavingAcademicSetup(true)

  try {
    const program = await createProgram(token, {
      department_id: programDepartmentId,
      code: programCode.trim(),
      name: programName.trim(),
      minimum_credit: minimumCredit,
      maximum_credit: maximumCredit,
    })
    setPrograms((current) => [...current, program])
    setProgramCode('')
    setProgramName('')
    setProgramMinimumCredit('9')
    setProgramMaximumCredit('18')
    setFeedback('Academic program created successfully.')
  } catch (requestError) {
    setAcademicSetupError(
      errorMessage(requestError, 'The program could not be created.'),
    )
  } finally {
    setSavingAcademicSetup(false)
  }
}

  const firstName = user?.name.trim().split(/\s+/)[0] || 'Administrator'
  const pageLabel = useMemo(() => {
    if (!pagination.total_items) {
      return '0 accounts'
    }

    const start = (pagination.page - 1) * pagination.page_size + 1
    const end = Math.min(
      pagination.page * pagination.page_size,
      pagination.total_items,
    )
    return `${start}–${end} of ${pagination.total_items}`
  }, [pagination])

  return (
    <main className="app-main admin-main">
      <section className="dashboard-hero admin-hero">
        <div>
          <span className="page-eyebrow">Administration workspace</span>
          <h1>Welcome, {firstName}</h1>
          <p>
            Control staff access, protect privileged accounts, and monitor
            CoursePilot users from one administration workspace.
          </p>
        </div>

        <button
          className="refresh-button"
          type="button"
          disabled={loading}
          onClick={() => void loadDashboard(appliedSearch, pagination.page)}
        >
          <span aria-hidden="true">↻</span>
          Refresh
        </button>
      </section>

      <section className="admin-summary-grid" aria-label="Administration summary">
        <SummaryCard
          label="Visible users"
          value={overview.total_users}
          note="accounts in your scope"
        />
        <SummaryCard
          label="Active students"
          value={overview.active_students}
          note="student access enabled"
        />
        <SummaryCard
          label="Active advisors"
          value={overview.active_advisors}
          note="advisor access enabled"
        />
        <SummaryCard
          label="Pending staff"
          value={overview.pending_staff}
          note="awaiting activation"
        />
        <SummaryCard
          label="Suspended"
          value={overview.suspended_accounts}
          note="access blocked"
        />
        <SummaryCard
          label="Profiles to link"
          value={overview.unlinked_students}
          note="student setup required"
        />
      </section>

      {feedback && (
        <div className="inline-alert success" role="status">
          <strong>Administration updated</strong>
          <span>{feedback}</span>
        </div>
      )}

      {error && (
        <div className="inline-alert error" role="alert">
          <strong>Administration unavailable</strong>
          <span>{error}</span>
        </div>
      )}

      <section className="admin-workspace" id="admin-users">
        <div className="admin-access-panel">
          <div className="section-heading">
            <div>
              <span className="section-eyebrow">Users & access</span>
              <h2>Account administration</h2>
              <p>
                Students register themselves. Staff accounts are provisioned
                here and can be activated or suspended by authorized admins.
              </p>
            </div>
            <span className="summary-note">{pageLabel}</span>
          </div>

          <form className="admin-search-form" onSubmit={submitSearch}>
            <label>
              <span className="sr-only">Search users</span>
              <input
                type="search"
                value={search}
                placeholder="Search by name or email"
                onChange={(event) => setSearch(event.target.value)}
              />
            </label>
            <button type="submit">Search</button>
          </form>

          {loading ? (
            <div className="dashboard-state">
              <div className="state-spinner" aria-hidden="true" />
              <strong>Loading accounts…</strong>
            </div>
          ) : users.length === 0 ? (
            <div className="dashboard-state">
              <strong>No accounts found</strong>
              <span>Try another search or create a staff account.</span>
            </div>
          ) : (
            <div className="admin-user-list">
              {users.map((target) => {
                const manageable = canManage(target)
                const saving = savingUserId === target.id

                return (
                  <article className="admin-user-row" key={target.id}>
                    <div className="admin-user-identity">
                      <span
                        className={`registration-badge admin-role-${target.role}`}
                      >
                        {ROLE_LABELS[target.role] || target.role}
                      </span>
                      <h3>{target.name}</h3>
                      <p>{target.email}</p>
                    </div>

                    <div className="admin-user-meta">
                      <span>
                        Status
                        <strong
                          className={`admin-status admin-status-${target.account_status}`}
                        >
                          {STATUS_LABELS[target.account_status] ||
                            target.account_status}
                        </strong>
                      </span>
                      <span>
                        Profile
                        <strong>
                          {target.profile_status === 'missing'
                            ? 'Needs linking'
                            : target.profile_status === 'linked'
                              ? 'Linked'
                              : 'Not required'}
                        </strong>
                      </span>
                      <span>
                        Created
                        <strong>{formatDate(target.created_at)}</strong>
                      </span>
                    </div>

                    <div className="admin-user-actions">
                      {target.role === 'student' &&
                        target.profile_status === 'missing' && (
                          <button
                            type="button"
                            onClick={() => {
                              setSelectedStudent(target)
                              setStudentFormError('')
                            }}
                          >
                            Link profile
                          </button>
                        )}
                      {manageable ? (
                        <>
                          {target.account_status !== 'active' && (
                            <button
                              type="button"
                              disabled={saving}
                              onClick={() =>
                                void changeAccess(target, 'active')
                              }
                            >
                              Activate
                            </button>
                          )}
                          {target.account_status !== 'suspended' && (
                            <button
                              className="danger"
                              type="button"
                              disabled={saving}
                              onClick={() =>
                                void changeAccess(target, 'suspended')
                              }
                            >
                              Suspend
                            </button>
                          )}
                        </>
                      ) : (
                        <span className="admin-protected-note">
                          Protected account
                        </span>
                      )}
                    </div>
                  </article>
                )
              })}
            </div>
          )}

          {pagination.total_pages > 1 && (
            <div className="admin-pagination">
              <button
                type="button"
                disabled={pagination.page <= 1 || loading}
                onClick={() =>
                  void loadDashboard(appliedSearch, pagination.page - 1)
                }
              >
                Previous
              </button>
              <span>
                Page {pagination.page} of {pagination.total_pages}
              </span>
              <button
                type="button"
                disabled={
                  pagination.page >= pagination.total_pages || loading
                }
                onClick={() =>
                  void loadDashboard(appliedSearch, pagination.page + 1)
                }
              >
                Next
              </button>
            </div>
          )}
        </div>

        <aside className="admin-create-panel" id="admin-create-staff">
          <span className="section-eyebrow">Provision staff</span>
          <h2>Create staff account</h2>
          <p>
            Staff use the shared CoursePilot login after their account is
            created and activated here.
          </p>

          <form className="admin-create-form" onSubmit={createStaff} noValidate>
            <label>
              <span>Full name</span>
              <input
                value={name}
                placeholder="Dr. Nadia Rahman"
                maxLength={255}
                onChange={(event) => setName(event.target.value)}
              />
            </label>

            <label>
              <span>Email</span>
              <input
                type="email"
                value={email}
                placeholder="staff@university.edu"
                maxLength={254}
                onChange={(event) => setEmail(event.target.value)}
              />
            </label>

            <label>
              <span>Temporary password</span>
              <input
                type="password"
                value={password}
                placeholder="At least 8 characters"
                maxLength={128}
                autoComplete="new-password"
                onChange={(event) => setPassword(event.target.value)}
              />
            </label>

            <label>
              <span>Role</span>
              <select
                value={role}
                onChange={(event) =>
                  setRole(
                    event.target.value as CreateStaffPayload['role'],
                  )
                }
              >
                <option value="advisor">Advisor / faculty</option>
                {isSystemAdmin && (
                  <option value="department-admin">
                    Department administrator
                  </option>
                )}
              </select>
            </label>

            {role === 'advisor' && (
              <>
                <label>
                  <span>Department</span>
                  <select
                    value={departmentId}
                    onChange={(event) => setDepartmentId(event.target.value)}
                  >
                    <option value="">Select department</option>
                    {departments.map((department) => (
                      <option key={department.id} value={department.id}>
                        {department.code} · {department.name}
                      </option>
                    ))}
                  </select>
                </label>

                <label>
                  <span>Employee number</span>
                  <input
                    value={employeeNumber}
                    placeholder="FAC-001"
                    maxLength={64}
                    onChange={(event) =>
                      setEmployeeNumber(event.target.value)
                    }
                  />
                </label>
              </>
            )}

            <label>
              <span>Initial access</span>
              <select
                value={accountStatus}
                onChange={(event) =>
                  setAccountStatus(
                    event.target
                      .value as CreateStaffPayload['account_status'],
                  )
                }
              >
                <option value="active">Active</option>
                <option value="pending">Pending verification</option>
              </select>
            </label>

            {formError && (
              <p className="admin-form-error" role="alert">
                {formError}
              </p>
            )}

            <button
              className="admin-create-button"
              type="submit"
              disabled={creating}
            >
              {creating ? 'Creating…' : 'Create staff account'}
            </button>
          </form>

<div className="admin-policy-note">
    <strong>Access policy</strong>
    <span>
      Public sign-up remains student-only. Faculty and administrative
      roles cannot be self-assigned.
    </span>
  </div>

  <div className="admin-divider" />

  <span className="section-eyebrow">Student setup</span>
  <h2>Link academic profile</h2>
  <p>
    Link a self-registered student to a program and advisor before
    course registration actions are enabled.
  </p>

  {selectedStudent ? (
    <form
      className="admin-create-form"
      onSubmit={linkStudentProfile}
      noValidate
    >
      <div className="admin-selected-student">
        <strong>{selectedStudent.name}</strong>
        <span>{selectedStudent.email}</span>
      </div>

      <label>
        <span>Student number</span>
        <input
          value={studentNumber}
          placeholder="STU-2026-001"
          maxLength={64}
          onChange={(event) => setStudentNumber(event.target.value)}
        />
      </label>

      <label>
        <span>Current trimester</span>
        <input
          type="number"
          min="1"
          max="30"
          value={studentTrimester}
          onChange={(event) =>
            setStudentTrimester(event.target.value)
          }
        />
      </label>

      <label>
        <span>Program</span>
        <select
          value={studentProgramId}
          onChange={(event) => {
            setStudentProgramId(event.target.value)
            setStudentAdvisorId('')
          }}
        >
          <option value="">Select program</option>
          {programs.map((program) => (
            <option key={program.id} value={program.id}>
              {program.code} · {program.name}
            </option>
          ))}
        </select>
      </label>

      <label>
        <span>Advisor</span>
        <select
          value={studentAdvisorId}
          onChange={(event) =>
            setStudentAdvisorId(event.target.value)
          }
        >
          <option value="">Select advisor</option>
          {advisorOptions
            .filter((advisor) => {
              const program = programs.find(
                (item) => item.id === studentProgramId,
              )
              return (
                !program ||
                advisor.department_id === program.department_id
              )
            })
            .map((advisor) => (
              <option key={advisor.id} value={advisor.id}>
                {advisor.name} · {advisor.employee_number}
              </option>
            ))}
        </select>
      </label>

      {studentFormError && (
        <p className="admin-form-error" role="alert">
          {studentFormError}
        </p>
      )}

      <div className="admin-inline-actions">
        <button
          className="admin-create-button"
          type="submit"
          disabled={linkingStudent}
        >
          {linkingStudent ? 'Linking…' : 'Link student profile'}
        </button>
        <button
          className="admin-secondary-button"
          type="button"
          onClick={() => {
            setSelectedStudent(null)
            setStudentFormError('')
          }}
        >
          Cancel
        </button>
      </div>
    </form>
  ) : (
    <div className="admin-empty-note">
      Choose <strong>Link profile</strong> beside an unlinked student
      account.
    </div>
  )}

  {isSystemAdmin && (
    <>
      <div className="admin-divider" />

      <span className="section-eyebrow">Academic setup</span>
      <h2>Departments & programs</h2>
      <p>
        System administrators can create the academic structure used
        when staff and student profiles are provisioned.
      </p>

      <form
        className="admin-create-form admin-compact-form"
        onSubmit={saveDepartment}
      >
        <strong>Create department</strong>
        <label>
          <span>Department code</span>
          <input
            value={departmentCode}
            placeholder="CSE"
            maxLength={32}
            onChange={(event) =>
              setDepartmentCode(event.target.value)
            }
          />
        </label>
        <label>
          <span>Department name</span>
          <input
            value={departmentName}
            placeholder="Computer Science and Engineering"
            maxLength={255}
            onChange={(event) =>
              setDepartmentName(event.target.value)
            }
          />
        </label>
        <button
          className="admin-create-button"
          type="submit"
          disabled={savingAcademicSetup}
        >
          Create department
        </button>
      </form>

      <form
        className="admin-create-form admin-compact-form"
        onSubmit={saveProgram}
      >
        <strong>Create program</strong>
        <label>
          <span>Department</span>
          <select
            value={programDepartmentId}
            onChange={(event) =>
              setProgramDepartmentId(event.target.value)
            }
          >
            <option value="">Select department</option>
            {departments.map((department) => (
              <option key={department.id} value={department.id}>
                {department.code} · {department.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span>Program code</span>
          <input
            value={programCode}
            placeholder="BSC-CSE"
            maxLength={32}
            onChange={(event) => setProgramCode(event.target.value)}
          />
        </label>
        <label>
          <span>Program name</span>
          <input
            value={programName}
            placeholder="BSc in Computer Science and Engineering"
            maxLength={255}
            onChange={(event) => setProgramName(event.target.value)}
          />
        </label>
        <div className="admin-credit-grid">
          <label>
            <span>Minimum credits</span>
            <input
              type="number"
              min="0"
              max="60"
              value={programMinimumCredit}
              onChange={(event) =>
                setProgramMinimumCredit(event.target.value)
              }
            />
          </label>
          <label>
            <span>Maximum credits</span>
            <input
              type="number"
              min="0"
              max="60"
              value={programMaximumCredit}
              onChange={(event) =>
                setProgramMaximumCredit(event.target.value)
              }
            />
          </label>
        </div>
        <button
          className="admin-create-button"
          type="submit"
          disabled={savingAcademicSetup}
        >
          Create program
        </button>
      </form>

      {academicSetupError && (
        <p className="admin-form-error" role="alert">
          {academicSetupError}
        </p>
      )}
    </>
  )}
</aside>
      </section>

      {isSystemAdmin && <AuditLogPanel />}
    </main>
  )
}
