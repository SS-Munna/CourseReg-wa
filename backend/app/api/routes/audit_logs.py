from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.errors import (
    REQUEST_VALIDATION_ERROR_RESPONSE,
    STANDARD_ERROR_RESPONSE,
)
from app.authorization import UserRole, require_roles
from app.database import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit_log import AuditLogData, AuditLogListResponse
from app.schemas.common import PaginationMeta


router = APIRouter(prefix="/api/admin/audit-logs", tags=["Audit Logs"])
require_system_admin = require_roles(UserRole.SYSTEM_ADMIN)


@router.get(
    "",
    response_model=AuditLogListResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: STANDARD_ERROR_RESPONSE,
        status.HTTP_403_FORBIDDEN: STANDARD_ERROR_RESPONSE,
        status.HTTP_422_UNPROCESSABLE_CONTENT: REQUEST_VALIDATION_ERROR_RESPONSE,
    },
)
def list_audit_logs(
    action_type: str | None = Query(default=None, max_length=64),
    entity_type: str | None = Query(default=None, max_length=64),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    _current_user: User = Depends(require_system_admin),
    db: Session = Depends(get_db),
):
    query = db.query(AuditLog).join(User, AuditLog.user_id == User.id)

    if action_type and action_type.strip():
        query = query.filter(AuditLog.action_type == action_type.strip())

    if entity_type and entity_type.strip():
        query = query.filter(AuditLog.entity_type == entity_type.strip())

    total_items = query.count()
    rows = (
        query.order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return AuditLogListResponse(
        data=[
            AuditLogData(
                id=row.id,
                actor_user_id=row.user_id,
                actor_name=row.user.full_name,
                actor_email=row.user.email,
                action_type=row.action_type,
                entity_type=row.entity_type,
                entity_id=row.entity_id,
                action_details=row.action_details,
                created_at=row.created_at,
            )
            for row in rows
        ],
        pagination=PaginationMeta.from_total(
            page=page,
            page_size=page_size,
            total_items=total_items,
        ),
    )
