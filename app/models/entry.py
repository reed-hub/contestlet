from sqlalchemy import Column, Integer, DateTime, Boolean, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from . import Base
from app.core.datetime_utils import utc_now


class Entry(Base):
    __tablename__ = "entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    contest_id = Column(Integer, ForeignKey("contests.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    selected = Column(Boolean, default=False)  # For marking winners
    status = Column(String, default="active")  # Entry status: active, winner, disqualified
    
    # Manual Entry Fields
    source = Column(String(50), default="web_app", nullable=False)  # Entry source tracking
    created_by_admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Admin who created manual entry
    admin_notes = Column(Text, nullable=True)  # Admin notes for manual entries
    
    # Relationships
    user = relationship("User", back_populates="entries")
    contest = relationship("Contest", back_populates="entries")
    notifications = relationship("Notification", back_populates="entry")
    winner_record = relationship("ContestWinner", back_populates="entry", uselist=False)
    created_by_admin = relationship("User", foreign_keys=[created_by_admin_id])
