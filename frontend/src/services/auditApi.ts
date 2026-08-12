import { requestJson } from './apiClient'
import type { AuditLogItem, AuditLogPagination } from '../types/audit'

type AuditLogResponse = {
  success: true
  data: AuditLogItem[]
  pagination: AuditLogPagination
}

export async function fetchAuditLogs(
  token: string,
  page = 1,
): Promise<{ logs: AuditLogItem[]; pagination: AuditLogPagination }> {
  const response = await requestJson<AuditLogResponse>(
    `/api/admin/audit-logs?page=${page}&page_size=25`,
    {
      token,
      fallbackMessage: 'Audit activity could not be loaded.',
      fallbackCode: 'AUDIT_LOG_LOAD_FAILED',
    },
  )

  return {
    logs: response.data,
    pagination: response.pagination,
  }
}
