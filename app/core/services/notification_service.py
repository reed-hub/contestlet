"""
Clean notification service with centralized SMS and email logic.
Handles all notification operations with proper error handling and business rules.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.user import User
from app.models.contest import Contest
from app.models.entry import Entry
from app.shared.exceptions.base import (
    BusinessException, 
    ValidationException,
    ErrorCode
)
from app.shared.constants.auth import AuthConstants
from app.shared.types.pagination import PaginationParams, PaginatedResult, create_paginated_result
from app.core.datetime_utils import utc_now
from app.core.sms_notification_service import sms_notification_service


class NotificationService:
    """
    Clean notification service with centralized business logic.
    """
    
    def __init__(self, notification_repo, user_repo, contest_repo, entry_repo, db: Session):
        self.notification_repo = notification_repo
        self.user_repo = user_repo
        self.contest_repo = contest_repo
        self.entry_repo = entry_repo
        self.db = db
    
    async def send_sms_notification(
        self,
        recipient: str,
        message: str,
        contest_id: Optional[int] = None,
        entry_id: Optional[int] = None,
        template_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send SMS notification with proper error handling and logging.
        
        Args:
            recipient: Phone number to send to
            message: SMS message content
            contest_id: Optional contest ID for context
            entry_id: Optional entry ID for context
            template_type: Optional template type for categorization
            
        Returns:
            Dictionary with send result and metadata
        """
        try:
            # Create notification record
            notification = Notification(
                type="sms",
                recipient=recipient,
                message=message,
                status="pending",
                contest_id=contest_id,
                entry_id=entry_id,
                created_at=utc_now()
            )
            
            self.db.add(notification)
            self.db.flush()  # Get the ID
            
            # Send via SMS service
            result = await sms_notification_service.send_sms(recipient, message)
            
            # Update notification status
            if result.get("success"):
                notification.status = "sent"
                notification.sent_at = utc_now()
                notification.twilio_sid = result.get("sid")
                notification.twilio_status = result.get("status")
            else:
                notification.status = "failed"
                notification.error_message = result.get("error", "Unknown error")
            
            self.db.commit()
            
            return {
                "success": result.get("success", False),
                "notification_id": notification.id,
                "message_id": result.get("sid"),
                "status": notification.status,
                "cost": result.get("cost", 0),
                "error": result.get("error")
            }
            
        except Exception as e:
            self.db.rollback()
            raise BusinessException(
                message=f"Failed to send SMS notification: {str(e)}",
                error_code=ErrorCode.EXTERNAL_SERVICE_ERROR,
                details={"recipient": recipient, "error": str(e)}
            )
    
    async def get_notifications_paginated(
        self,
        pagination: PaginationParams,
        filters: Optional[Dict[str, Any]] = None
    ):
        """
        Get notifications with pagination and filtering.
        
        Args:
            pagination: Pagination parameters
            filters: Optional filters (type, status, date_range, etc.)
            
        Returns:
            Paginated result of notifications
        """
        try:
            query = self.db.query(Notification)
            
            # Apply filters
            if filters:
                if filters.get("type"):
                    query = query.filter(Notification.type == filters["type"])
                
                if filters.get("status"):
                    query = query.filter(Notification.status == filters["status"])
                
                if filters.get("contest_id"):
                    query = query.filter(Notification.contest_id == filters["contest_id"])
                
                if filters.get("date_from"):
                    query = query.filter(Notification.created_at >= filters["date_from"])
                
                if filters.get("date_to"):
                    query = query.filter(Notification.created_at <= filters["date_to"])
            
            # Get total count
            total = query.count()
            
            # Apply pagination and ordering
            notifications = query.order_by(Notification.created_at.desc()).offset(
                pagination.offset
            ).limit(pagination.size).all()
            
            return create_paginated_result(
                items=notifications,
                total=total,
                page=pagination.page,
                size=pagination.size
            )
            
        except Exception as e:
            raise BusinessException(
                message=f"Failed to retrieve notifications: {str(e)}",
                error_code=ErrorCode.DATABASE_ERROR,
                details={"error": str(e)}
            )
    
    async def send_contest_entry_confirmation(
        self,
        entry: Entry,
        contest: Contest,
        user: User,
        custom_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send entry confirmation SMS to user.
        
        Args:
            entry: Contest entry
            contest: Contest details
            user: User who entered
            custom_message: Optional custom message template
            
        Returns:
            Send result with metadata
        """
        if custom_message:
            message = custom_message
        else:
            message = f"Thanks for entering '{contest.name}'! Your entry has been confirmed. Good luck!"
        
        return await self.send_sms_notification(
            recipient=user.phone,
            message=message,
            contest_id=contest.id,
            entry_id=entry.id,
            template_type="entry_confirmation"
        )
    
    async def send_winner_notification(
        self,
        entry: Entry,
        contest: Contest,
        user: User,
        custom_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send winner notification SMS to user.
        
        Args:
            entry: Winning entry
            contest: Contest details
            user: Winner user
            custom_message: Optional custom message template
            
        Returns:
            Send result with metadata
        """
        if custom_message:
            message = custom_message
        else:
            message = f"Congratulations! You won '{contest.name}'! We'll contact you soon with details."
        
        return await self.send_sms_notification(
            recipient=user.phone,
            message=message,
            contest_id=contest.id,
            entry_id=entry.id,
            template_type="winner_notification"
        )
    
    async def send_bulk_notifications(
        self,
        recipients: List[str],
        message: str,
        contest_id: Optional[int] = None,
        template_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send bulk SMS notifications.
        
        Args:
            recipients: List of phone numbers
            message: SMS message content
            contest_id: Optional contest ID for context
            template_type: Optional template type
            
        Returns:
            Bulk send results with statistics
        """
        results = {
            "total": len(recipients),
            "sent": 0,
            "failed": 0,
            "errors": []
        }
        
        for recipient in recipients:
            try:
                result = await self.send_sms_notification(
                    recipient=recipient,
                    message=message,
                    contest_id=contest_id,
                    template_type=template_type
                )
                
                if result.get("success"):
                    results["sent"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append({
                        "recipient": recipient,
                        "error": result.get("error", "Unknown error")
                    })
                    
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "recipient": recipient,
                    "error": str(e)
                })
        
        return results
    
    async def get_notification_statistics(self) -> Dict[str, Any]:
        """
        Get notification statistics for admin dashboard.
        
        Returns:
            Dictionary with notification statistics
        """
        try:
            total_notifications = self.db.query(Notification).count()
            sent_notifications = self.db.query(Notification).filter(
                Notification.status == "sent"
            ).count()
            failed_notifications = self.db.query(Notification).filter(
                Notification.status == "failed"
            ).count()
            
            # Get recent activity (last 7 days)
            seven_days_ago = utc_now() - datetime.timedelta(days=7)
            recent_notifications = self.db.query(Notification).filter(
                Notification.created_at >= seven_days_ago
            ).count()
            
            return {
                "total_notifications": total_notifications,
                "sent_notifications": sent_notifications,
                "failed_notifications": failed_notifications,
                "success_rate": (sent_notifications / total_notifications * 100) if total_notifications > 0 else 0,
                "recent_activity_7_days": recent_notifications
            }
            
        except Exception as e:
            raise BusinessException(
                message=f"Failed to retrieve notification statistics: {str(e)}",
                error_code=ErrorCode.DATABASE_ERROR,
                details={"error": str(e)}
            )
