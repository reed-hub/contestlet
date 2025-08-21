from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base
from app.core.datetime_utils import utc_now


class Contest(Base):
    __tablename__ = "contests"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    location = Column(String)  # Format: "City, State ZIP" or similar
    latitude = Column(Float)  # Latitude for geolocation
    longitude = Column(Float)  # Longitude for geolocation
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    prize_description = Column(Text)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    
    # Winner tracking
    winner_entry_id = Column(Integer, nullable=True)  # ID of winning entry
    winner_phone = Column(String, nullable=True)  # Winner's phone number
    winner_selected_at = Column(DateTime(timezone=True), nullable=True)  # When winner was selected
    
    # Timezone metadata (for audit trail and admin context)
    created_timezone = Column(String(50), nullable=True)  # Admin's timezone when contest was created
    admin_user_id = Column(String(50), nullable=True)  # Admin who created the contest
    
    # Campaign import metadata
    campaign_metadata = Column(JSON, nullable=True)  # Original one-sheet JSON and import data
    
    # Contest configuration (Phase 1 form support)
    contest_type = Column(String(50), default="general", nullable=False)  # general, sweepstakes, instant_win
    entry_method = Column(String(50), default="sms", nullable=False)      # sms, email, web_form
    winner_selection_method = Column(String(50), default="random", nullable=False)  # random, scheduled, instant
    
    # Entry limitations and validation
    minimum_age = Column(Integer, default=18, nullable=False)
    max_entries_per_person = Column(Integer, nullable=True)    # NULL = unlimited
    total_entry_limit = Column(Integer, nullable=True)         # NULL = unlimited
    
    # Additional contest details
    consolation_offer = Column(Text, nullable=True)            # Consolation prize/offer for non-winners
    geographic_restrictions = Column(Text, nullable=True)      # Geographic limitations
    contest_tags = Column(JSON, nullable=True)                # Array of tags for organization
    promotion_channels = Column(JSON, nullable=True)          # Array of promotion channels
    
    # Relationships
    entries = relationship("Entry", back_populates="contest")
    official_rules = relationship("OfficialRules", back_populates="contest", uselist=False)
    notifications = relationship("Notification", back_populates="contest")
    sms_templates = relationship("SMSTemplate", back_populates="contest")
