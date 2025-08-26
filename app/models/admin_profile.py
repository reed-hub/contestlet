"""
Admin Profile model for storing admin preferences including timezone settings
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from . import Base


class AdminProfile(Base):
    """
    Model for storing admin user preferences and settings
    
    Stores timezone preferences, UI settings, and other admin-specific configuration.
    """
    __tablename__ = "admin_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    admin_user_id = Column(String(50), unique=True, nullable=False, index=True)  # Maps to JWT sub claim
    
    # Timezone preferences
    timezone = Column(String(50), nullable=False, default="UTC")  # IANA timezone identifier
    timezone_auto_detect = Column(Boolean, default=True, nullable=False)  # Use browser timezone
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<AdminProfile(admin_user_id={self.admin_user_id}, timezone={self.timezone})>"
