from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database.database import get_db
from app.schemas.admin import (
    WinnerNotificationRequest, WinnerNotificationResponse,
    NotificationLogResponse
)
from app.core.admin_auth import get_admin_user
from app.core.exceptions import raise_authorization_error
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/admin/notifications", tags=["admin-notifications"])


@router.get("/", response_model=List[NotificationLogResponse])
async def get_notification_logs(
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db),
    limit: int = 100,
    offset: int = 0
):
    """Get SMS notification logs with pagination"""
    notification_service = NotificationService(db)
    logs = notification_service.get_notification_logs(limit=limit, offset=offset)
    return logs


@router.post("/{contest_id}/notify-winner", response_model=WinnerNotificationResponse)
async def notify_winner(
    contest_id: int,
    notification_data: WinnerNotificationRequest,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Send winner notification via SMS"""
    notification_service = NotificationService(db)
    result = notification_service.send_winner_notification(
        contest_id, 
        notification_data.message,
        admin_user["sub"]
    )
    
    return WinnerNotificationResponse(
        success=result["success"],
        message=result["message"],
        notification_id=result.get("notification_id")
    )


@router.post("/{contest_id}/send-reminder", response_model=WinnerNotificationResponse)
async def send_reminder(
    contest_id: int,
    notification_data: WinnerNotificationRequest,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Send reminder notification to contest participants"""
    notification_service = NotificationService(db)
    result = notification_service.send_reminder_notification(
        contest_id,
        notification_data.message,
        admin_user["sub"]
    )
    
    return WinnerNotificationResponse(
        success=result["success"],
        message=result["message"],
        notification_id=result.get("notification_id")
    )


@router.post("/{contest_id}/send-announcement", response_model=WinnerNotificationResponse)
async def send_announcement(
    contest_id: int,
    notification_data: WinnerNotificationRequest,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Send announcement to all contest participants"""
    notification_service = NotificationService(db)
    result = notification_service.send_announcement_notification(
        contest_id,
        notification_data.message,
        admin_user["sub"]
    )
    
    return WinnerNotificationResponse(
        success=result["success"],
        message=result["message"],
        notification_id=result.get("notification_id")
    )


@router.get("/users/{user_id}/interaction-history", response_model=List[NotificationLogResponse])
async def get_user_interaction_history(
    user_id: int,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db),
    limit: int = 100
):
    """Get interaction history for a specific user"""
    notification_service = NotificationService(db)
    history = notification_service.get_user_interaction_history(user_id, limit=limit)
    return history
