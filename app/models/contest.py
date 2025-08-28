from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from . import Base
from app.core.datetime_utils import utc_now


class Contest(Base):
    __tablename__ = "contests"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    # Legacy location fields (kept for backward compatibility)
    location = Column(String)  # Format: "City, State ZIP" or similar - now used as display_text
    latitude = Column(Float)  # Legacy latitude for geolocation
    longitude = Column(Float)  # Legacy longitude for geolocation
    
    # Smart Location System fields
    location_type = Column(String(20), default="united_states", nullable=False)  # Location targeting type
    selected_states = Column(JSON, nullable=True)  # Array of state codes for specific_states type
    radius_address = Column(String(500), nullable=True)  # Address for radius targeting
    radius_miles = Column(Integer, nullable=True)  # Radius in miles for radius targeting
    radius_latitude = Column(Float, nullable=True)  # Latitude for radius center
    radius_longitude = Column(Float, nullable=True)  # Longitude for radius center
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
    
    # Visual branding and sponsor information
    image_url = Column(String, nullable=True)                 # Full Cloudinary URL for hero media
    image_public_id = Column(String, nullable=True)           # Cloudinary public ID for transformations
    media_type = Column(String(10), default="image", nullable=False)  # "image" or "video"
    media_metadata = Column(JSON, nullable=True)              # Size, format, upload info, etc.
    sponsor_url = Column(String, nullable=True)               # Sponsor's website URL
    
    # Role System Fields
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    sponsor_profile_id = Column(Integer, ForeignKey("sponsor_profiles.id"), nullable=True, index=True)
    is_approved = Column(Boolean, default=True, nullable=False, index=True)  # Default true for backward compatibility
    approved_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    entries = relationship("Entry", back_populates="contest")
    official_rules = relationship("OfficialRules", back_populates="contest", uselist=False)
    notifications = relationship("Notification", back_populates="contest")
    sms_templates = relationship("SMSTemplate", back_populates="contest")
    
    # Role System Relationships
    creator = relationship("User", foreign_keys=[created_by_user_id], back_populates="created_contests")
    approver = relationship("User", foreign_keys=[approved_by_user_id], back_populates="approved_contests")
    sponsor_profile = relationship("SponsorProfile", back_populates="contests")
    approval_history = relationship("ContestApprovalAudit", back_populates="contest")
