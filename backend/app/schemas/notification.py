from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import PaginationMeta, SuccessResponse


class NotificationData(BaseModel):
    id: UUID
    notification_type: str
    title: str
    message: str
    is_read: bool
    created_at: datetime


class NotificationListData(BaseModel):
    notifications: list[NotificationData]
    unread_count: int = Field(..., ge=0)
    pagination: PaginationMeta


class NotificationListResponse(SuccessResponse[NotificationListData]):
    pass


class NotificationResponse(SuccessResponse[NotificationData]):
    pass


class NotificationReadAllData(BaseModel):
    updated_count: int = Field(..., ge=0)
    unread_count: int = Field(..., ge=0)


class NotificationReadAllResponse(SuccessResponse[NotificationReadAllData]):
    pass
