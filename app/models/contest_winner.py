"""
Contest Winner Model for Multiple Winners Feature

This model stores individual winners for contests that support multiple winners.
Each winner has a position (1st, 2nd, 3rd place, etc.) and optional prize information.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.datetime_utils import utc_now
from . import Base


class ContestWinner(Base):
    """
    Model for individual contest winners.
    
    Supports multiple winners per contest with positions and prize tracking.
    Each contest can have 1-50 winners with unique positions.
    """
    __tablename__ = "contest_winners"

    id = Column(Integer, primary_key=True, index=True)
    contest_id = Column(Integer, ForeignKey("contests.id", ondelete="CASCADE"), nullable=False, index=True)
    entry_id = Column(Integer, ForeignKey("entries.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Winner position and prize information
    winner_position = Column(Integer, nullable=False, index=True)  # 1st, 2nd, 3rd place, etc.
    prize_description = Column(Text, nullable=True)  # Specific prize for this winner
    
    # Timestamps
    selected_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    notified_at = Column(DateTime(timezone=True), nullable=True)  # When winner notification was sent
    claimed_at = Column(DateTime(timezone=True), nullable=True)   # When winner claimed their prize
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    
    # Relationships
    contest = relationship("Contest", back_populates="winners")
    entry = relationship("Entry", back_populates="winner_record")
    
    def __repr__(self):
        return f"<ContestWinner(contest_id={self.contest_id}, position={self.winner_position}, entry_id={self.entry_id})>"
    
    @property
    def user(self):
        """Get the user associated with this winner through the entry"""
        return self.entry.user if self.entry else None
    
    @property
    def phone(self):
        """Get the winner's phone number through the entry"""
        return self.entry.user.phone if self.entry and self.entry.user else None
    
    @property
    def is_notified(self) -> bool:
        """Check if winner has been notified"""
        return self.notified_at is not None
    
    @property
    def is_claimed(self) -> bool:
        """Check if winner has claimed their prize"""
        return self.claimed_at is not None
    
    def mark_notified(self):
        """Mark winner as notified"""
        self.notified_at = utc_now()
        self.updated_at = utc_now()
    
    def mark_claimed(self):
        """Mark winner as having claimed their prize"""
        self.claimed_at = utc_now()
        self.updated_at = utc_now()
    
    def to_dict(self):
        """Convert winner to dictionary for API responses"""
        return {
            "id": self.id,
            "contest_id": self.contest_id,
            "entry_id": self.entry_id,
            "winner_position": self.winner_position,
            "prize_description": self.prize_description,
            "selected_at": self.selected_at,
            "notified_at": self.notified_at,
            "claimed_at": self.claimed_at,
            "phone": self.phone,
            "is_notified": self.is_notified,
            "is_claimed": self.is_claimed
        }
