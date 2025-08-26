from sqlalchemy import Column, Integer, DateTime, Boolean, ForeignKey, String
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
    
    # Relationships
    user = relationship("User", back_populates="entries")
    contest = relationship("Contest", back_populates="entries")
    notifications = relationship("Notification", back_populates="entry")
