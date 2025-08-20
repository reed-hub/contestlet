from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base


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
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Winner tracking
    winner_entry_id = Column(Integer, nullable=True)  # ID of winning entry
    winner_phone = Column(String, nullable=True)  # Winner's phone number
    winner_selected_at = Column(DateTime(timezone=True), nullable=True)  # When winner was selected
    
    # Timezone metadata (for audit trail and admin context)
    created_timezone = Column(String(50), nullable=True)  # Admin's timezone when contest was created
    admin_user_id = Column(String(50), nullable=True)  # Admin who created the contest
    
    # Relationships
    entries = relationship("Entry", back_populates="contest")
    official_rules = relationship("OfficialRules", back_populates="contest", uselist=False)
    notifications = relationship("Notification", back_populates="contest")
