from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from . import Base
from app.core.datetime_utils import utc_now


class ContestStatusAudit(Base):
    """Audit trail for contest status changes"""
    __tablename__ = "contest_status_audit"

    id = Column(Integer, primary_key=True, index=True)
    contest_id = Column(Integer, ForeignKey("contests.id"), nullable=False, index=True)
    old_status = Column(String(20), nullable=True)  # Null for initial status
    new_status = Column(String(20), nullable=False, index=True)
    changed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    reason = Column(Text, nullable=True)  # Reason for status change (especially for rejections)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    
    # Relationships
    contest = relationship("Contest", back_populates="status_audit")
    changed_by = relationship("User", foreign_keys=[changed_by_user_id])
