from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import PaginatedResponse


class AuditLogData(BaseModel):
    id: UUID
    actor_user_id: UUID
    actor_name: str
    actor_email: str
    action_type: str
    entity_type: str
    entity_id: UUID
    action_details: str | None = None
    created_at: datetime


class AuditLogListResponse(PaginatedResponse[AuditLogData]):
    pass
