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
    
    # Relationships
    entries = relationship("Entry", back_populates="contest")
    official_rules = relationship("OfficialRules", back_populates="contest", uselist=False)
