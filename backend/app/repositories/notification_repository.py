from uuid import UUID

from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.schemas.common import PaginationMeta


class NotificationNotFoundError(Exception):
    pass


def list_notifications(
    db: Session,
    *,
    user_id: UUID,
    unread_only: bool,
    page: int,
    page_size: int,
):
    query = db.query(Notification).filter(Notification.user_id == user_id)

    if unread_only:
        query = query.filter(Notification.is_read.is_(False))

    total_items = query.count()
    notifications = (
        query.order_by(Notification.created_at.desc(), Notification.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    unread_count = (
        db.query(Notification)
        .filter(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )
        .count()
    )

    return (
        notifications,
        unread_count,
        PaginationMeta.from_total(
            page=page,
            page_size=page_size,
            total_items=total_items,
        ),
    )


def mark_notification_read(
    db: Session,
    *,
    notification_id: UUID,
    user_id: UUID,
) -> Notification:
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
        .first()
    )

    if notification is None:
        raise NotificationNotFoundError()

    if not notification.is_read:
        notification.is_read = True
        db.commit()
        db.refresh(notification)

    return notification


def mark_all_notifications_read(db: Session, *, user_id: UUID) -> int:
    updated_count = (
        db.query(Notification)
        .filter(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )
        .update({Notification.is_read: True}, synchronize_session=False)
    )
    db.commit()
    return int(updated_count)
