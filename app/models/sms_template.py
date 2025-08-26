from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from . import Base
from app.core.datetime_utils import utc_now


class SMSTemplate(Base):
    """
    SMS Template model for storing custom SMS messages for contests.
    
    Supports different template types:
    - entry_confirmation: Sent when user enters contest
    - winner_notification: Sent to contest winner
    - non_winner: Sent to non-winners (optional)
    - reminder: Sent as contest reminder
    - follow_up: Sent after contest ends
    """
    __tablename__ = "sms_templates"

    id = Column(Integer, primary_key=True, index=True)
    contest_id = Column(Integer, ForeignKey("contests.id"), nullable=False)
    template_type = Column(String(50), nullable=False)  # entry_confirmation, winner_notification, non_winner, etc.
    message_content = Column(Text, nullable=False)
    variables = Column(JSON, nullable=True)  # Available template variables like {contest_name}, {prize_description}
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    
    # Relationship back to contest
    contest = relationship("Contest", back_populates="sms_templates")
    
    def __repr__(self):
        return f"<SMSTemplate(contest_id={self.contest_id}, type={self.template_type})>"
