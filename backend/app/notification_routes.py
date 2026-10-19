from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.engine import Connection

from .auth import get_current_user
from .db import get_connection
from .schemas import NotificationResponse, UserResponse

router = APIRouter(prefix="/api/v1/notifications")


@router.get("", response_model=list[NotificationResponse])
def list_notifications(
    current_user: UserResponse = Depends(get_current_user),
    connection: Connection = Depends(get_connection),
) -> list[NotificationResponse]:
    rows = connection.execute(
        text(
            """
            SELECT id, title, message, notification_type, related_case_id,
                   is_read, created_at, read_at
            FROM notifications
            WHERE user_id = :user_id
            ORDER BY created_at DESC
            LIMIT 50
            """
        ),
        {"user_id": current_user.id},
    ).mappings()
    return [NotificationResponse(**row) for row in rows]


@router.post("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: int,
    current_user: UserResponse = Depends(get_current_user),
    connection: Connection = Depends(get_connection),
) -> NotificationResponse:
    row = connection.execute(
        text(
            """
            UPDATE notifications
            SET is_read = TRUE, read_at = COALESCE(read_at, now())
            WHERE id = :notification_id AND user_id = :user_id
            RETURNING id, title, message, notification_type, related_case_id,
                      is_read, created_at, read_at
            """
        ),
        {"notification_id": notification_id, "user_id": current_user.id},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    connection.commit()
    return NotificationResponse(**row)
