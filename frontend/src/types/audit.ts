export type AuditLogItem = {
  id: string
  actor_user_id: string
  actor_name: string
  actor_email: string
  action_type: string
  entity_type: string
  entity_id: string
  action_details: string | null
  created_at: string
}

export type AuditLogPagination = {
  page: number
  page_size: number
  total_items: number
  total_pages: number
}
