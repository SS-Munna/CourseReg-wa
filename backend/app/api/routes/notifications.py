from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.api.errors import (
    REQUEST_VALIDATION_ERROR_RESPONSE,
    STANDARD_ERROR_RESPONSE,
)
from app.authorization import get_current_user
from app.database import get_db
from app.models.user import User
from app.repositories.notification_repository import (
    NotificationNotFoundError,
    list_notifications,
    mark_all_notifications_read,
    mark_notification_read,
)
from app.schemas.notification import (
    NotificationData,
    NotificationListData,
    NotificationListResponse,
    NotificationReadAllData,
    NotificationReadAllResponse,
    NotificationResponse,
)


router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


def _data(notification) -> NotificationData:
    return NotificationData(
        id=notification.id,
        notification_type=notification.notification_type,
        title=notification.title,
        message=notification.message,
        is_read=notification.is_read,
        created_at=notification.created_at,
    )


@router.get(
    "",
    response_model=NotificationListResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: STANDARD_ERROR_RESPONSE,
        status.HTTP_403_FORBIDDEN: STANDARD_ERROR_RESPONSE,
        status.HTTP_422_UNPROCESSABLE_CONTENT: REQUEST_VALIDATION_ERROR_RESPONSE,
    },
)
def get_notifications(
    unread_only: bool = Query(default=False),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notifications, unread_count, pagination = list_notifications(
        db,
        user_id=current_user.id,
        unread_only=unread_only,
        page=page,
        page_size=page_size,
    )

    return NotificationListResponse(
        data=NotificationListData(
            notifications=[_data(item) for item in notifications],
            unread_count=unread_count,
            pagination=pagination,
        )
    )


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: STANDARD_ERROR_RESPONSE,
        status.HTTP_403_FORBIDDEN: STANDARD_ERROR_RESPONSE,
        status.HTTP_404_NOT_FOUND: STANDARD_ERROR_RESPONSE,
        status.HTTP_422_UNPROCESSABLE_CONTENT: REQUEST_VALIDATION_ERROR_RESPONSE,
    },
)
def read_notification(
    notification_id: UUID = Path(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        notification = mark_notification_read(
            db,
            notification_id=notification_id,
            user_id=current_user.id,
        )
    except NotificationNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOTIFICATION_NOT_FOUND",
                "message": "The notification was not found for this account.",
            },
        ) from error

    return NotificationResponse(data=_data(notification))


@router.post(
    "/read-all",
    response_model=NotificationReadAllResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: STANDARD_ERROR_RESPONSE,
        status.HTTP_403_FORBIDDEN: STANDARD_ERROR_RESPONSE,
    },
)
def read_all_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    updated_count = mark_all_notifications_read(db, user_id=current_user.id)

    return NotificationReadAllResponse(
        data=NotificationReadAllData(
            updated_count=updated_count,
            unread_count=0,
        )
    )
