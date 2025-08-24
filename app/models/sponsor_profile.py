"""
Sponsor Profile Model

Represents sponsor company information and verification status.
Links to User model for authentication and role management.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.database import Base
from app.core.datetime_utils import utc_now


class SponsorProfile(Base):
    __tablename__ = "sponsor_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Company Information
    company_name = Column(String(255), nullable=False, index=True)
    website_url = Column(String(500), nullable=True)
    logo_url = Column(String(500), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    industry = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    
    # Verification Status
    is_verified = Column(Boolean, default=False, nullable=False, index=True)
    verification_document_url = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="sponsor_profile")
    contests = relationship("Contest", back_populates="sponsor_profile")
    
    def __repr__(self):
        return f"<SponsorProfile(id={self.id}, company_name='{self.company_name}', verified={self.is_verified})>"
