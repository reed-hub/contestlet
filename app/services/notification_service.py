from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_
from app.models.notification import Notification
from app.models.contest import Contest
from app.models.entry import Entry
from app.models.user import User
from app.core.exceptions import (
    raise_resource_not_found,
    raise_business_logic_error,
    ErrorCode
)
from app.core.sms_notification_service import sms_notification_service
from app.core.config import get_settings
from app.core.datetime_utils import utc_now


class NotificationService:
    """Service layer for notification operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
    
    def get_notification_logs(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get SMS notification logs with pagination"""
        notifications = (
            self.db.query(Notification)
            .options(
                joinedload(Notification.user),
                joinedload(Notification.contest)
            )
            .order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        
        return [
            {
                "id": n.id,
                "user_phone": n.user.phone if n.user else "Unknown",
                "contest_name": n.contest.name if n.contest else "System",
                "message": n.message,
                "status": n.status,
                "created_at": n.created_at,
                "sent_at": n.sent_at
            }
            for n in notifications
        ]
    
    async def send_winner_notification(
        self, 
        contest_id: int, 
        message: str, 
        admin_user_id: int
    ) -> Dict[str, Any]:
        """Send winner notification via SMS"""
        contest = self.db.query(Contest).filter(Contest.id == contest_id).first()
        if not contest:
            raise_resource_not_found("Contest", contest_id)
        
        if not contest.winner_entry_id:
            raise_business_logic_error(
                ErrorCode.CONTEST_NOT_ACTIVE,
                "Cannot send winner notification - no winner selected"
            )
        
        winner_entry = self.db.query(Entry).filter(Entry.id == contest.winner_entry_id).first()
        if not winner_entry:
            raise_resource_not_found("Entry", contest.winner_entry_id)
        
        # Send SMS notification
        success, sms_message = await sms_notification_service.send_sms(
            winner_entry.user.phone,
            message
        )
        
        # Create notification record
        notification = Notification(
            user_id=winner_entry.user_id,
            contest_id=contest_id,
            message=message,
            status="sent" if success else "failed",
            notification_type="winner_notification",
            created_by_user_id=admin_user_id,
            created_at=utc_now()
        )
        
        if success:
            notification.sent_at = utc_now()
        
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        
        return {
            "success": success,
            "message": sms_message,
            "notification_id": notification.id
        }
    
    async def send_reminder_notification(
        self, 
        contest_id: int, 
        message: str, 
        admin_user_id: int
    ) -> Dict[str, Any]:
        """Send reminder notification to contest participants"""
        contest = self.db.query(Contest).filter(Contest.id == contest_id).first()
        if not contest:
            raise_resource_not_found("Contest", contest_id)
        
        # Get all participants
        participants = (
            self.db.query(Entry)
            .filter(Entry.contest_id == contest_id)
            .options(joinedload(Entry.user))
            .all()
        )
        
        if not participants:
            return {
                "success": False,
                "message": "No participants found for this contest"
            }
        
        # Send notifications to all participants
        sent_count = 0
        failed_count = 0
        
        for entry in participants:
            success, _ = await sms_notification_service.send_sms(
                entry.user.phone,
                message
            )
            
            # Create notification record
            notification = Notification(
                user_id=entry.user_id,
                contest_id=contest_id,
                message=message,
                status="sent" if success else "failed",
                notification_type="reminder",
                created_by_user_id=admin_user_id,
                created_at=utc_now()
            )
            
            if success:
                notification.sent_at = utc_now()
                sent_count += 1
            else:
                failed_count += 1
            
            self.db.add(notification)
        
        self.db.commit()
        
        return {
            "success": True,
            "message": f"Sent {sent_count} reminders, {failed_count} failed",
            "sent_count": sent_count,
            "failed_count": failed_count
        }
    
    async def send_announcement_notification(
        self, 
        contest_id: int, 
        message: str, 
        admin_user_id: int
    ) -> Dict[str, Any]:
        """Send announcement to all contest participants"""
        contest = self.db.query(Contest).filter(Contest.id == contest_id).first()
        if not contest:
            raise_resource_not_found("Contest", contest_id)
        
        # Get all participants
        participants = (
            self.db.query(Entry)
            .filter(Entry.contest_id == contest_id)
            .options(joinedload(Entry.user))
            .all()
        )
        
        if not participants:
            return {
                "success": False,
                "message": "No participants found for this contest"
            }
        
        # Send announcements to all participants
        sent_count = 0
        failed_count = 0
        
        for entry in participants:
            success, _ = await sms_notification_service.send_sms(
                entry.user.phone,
                message
            )
            
            # Create notification record
            notification = Notification(
                user_id=entry.user_id,
                contest_id=contest_id,
                message=message,
                status="sent" if success else "failed",
                notification_type="announcement",
                created_by_user_id=admin_user_id,
                created_at=utc_now()
            )
            
            if success:
                notification.sent_at = utc_now()
                sent_count += 1
            else:
                failed_count += 1
            
            self.db.add(notification)
        
        self.db.commit()
        
        return {
            "success": True,
            "message": f"Sent {sent_count} announcements, {failed_count} failed",
            "sent_count": sent_count,
            "failed_count": failed_count
        }
    
    def get_user_interaction_history(self, user_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """Get interaction history for a specific user"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise_resource_not_found("User", user_id)
        
        notifications = (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id)
            .options(joinedload(Notification.contest))
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .all()
        )
        
        return [
            {
                "id": n.id,
                "contest_name": n.contest.name if n.contest else "System",
                "message": n.message,
                "status": n.status,
                "type": n.notification_type,
                "created_at": n.created_at,
                "sent_at": n.sent_at
            }
            for n in notifications
        ]
    
    def get_notification_statistics(self) -> Dict[str, Any]:
        """Get notification statistics"""
        total_notifications = self.db.query(func.count(Notification.id)).scalar()
        sent_notifications = self.db.query(func.count(Notification.id)).filter(Notification.status == "sent").scalar()
        failed_notifications = self.db.query(func.count(Notification.id)).filter(Notification.status == "failed").scalar()
        
        # Get notifications by type
        type_counts = (
            self.db.query(
                Notification.notification_type,
                func.count(Notification.id)
            )
            .group_by(Notification.notification_type)
            .all()
        )
        
        return {
            "total": total_notifications,
            "sent": sent_notifications,
            "failed": failed_notifications,
            "success_rate": (sent_notifications / total_notifications * 100) if total_notifications > 0 else 0,
            "by_type": dict(type_counts)
        }
