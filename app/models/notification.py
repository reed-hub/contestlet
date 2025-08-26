"""
Notification model for tracking SMS messages sent to users
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from . import Base
from app.core.datetime_utils import utc_now


class Notification(Base):
    """
    Model for tracking SMS notifications sent to users
    
    Stores a log of all SMS messages sent, including winner notifications,
    reminders, and other communication. Provides audit trail and prevents
    duplicate notifications.
    """
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    contest_id = Column(Integer, ForeignKey("contests.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    entry_id = Column(Integer, ForeignKey("entries.id"), nullable=True, index=True)  # Nullable for non-entry notifications
    
    # Message details
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), nullable=False, default="general")  # winner, reminder, general, etc.
    
    # Delivery status
    status = Column(String(20), nullable=False, default="pending")  # pending, sent, failed, test
    twilio_sid = Column(String(100), nullable=True)  # Twilio message SID for tracking
    error_message = Column(Text, nullable=True)  # Error details if failed
    
    # Metadata
    test_mode = Column(Boolean, default=False, nullable=False)  # True if this was a test notification
    sent_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    admin_user_id = Column(String(50), nullable=True)  # ID of admin who triggered the notification
    
    # Relationships
    contest = relationship("Contest", back_populates="notifications")
    user = relationship("User", back_populates="notifications")
    entry = relationship("Entry", back_populates="notifications")
    
    def __repr__(self):
        return f"<Notification(id={self.id}, type={self.notification_type}, status={self.status}, user_id={self.user_id})>"
    
    @property
    def masked_message(self):
        """Return message with potentially sensitive info masked for logs"""
        if len(self.message) > 100:
            return self.message[:100] + "..."
        return self.message
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "contest_id": self.contest_id,
            "user_id": self.user_id,
            "entry_id": self.entry_id,
            "notification_type": self.notification_type,
            "status": self.status,
            "test_mode": self.test_mode,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "message_preview": self.masked_message
        }
