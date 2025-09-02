from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from . import Base
from app.core.datetime_utils import utc_now


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    
    # Personal Profile Fields
    full_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True, index=True)
    bio = Column(String(1000), nullable=True)  # Personal bio/description
    
    # Role System Fields
    role = Column(String(20), nullable=False, default='user', index=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    role_assigned_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    role_assigned_by = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # Timezone Preferences (available to all user roles)
    timezone = Column(String(50), nullable=True, default=None, index=True)  # IANA timezone identifier
    timezone_auto_detect = Column(Boolean, default=True, nullable=False)  # Auto-detect from browser
    
    # Relationships
    entries = relationship("Entry", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    sponsor_profile = relationship("SponsorProfile", back_populates="user", uselist=False)
    created_contests = relationship("Contest", foreign_keys="Contest.created_by_user_id", back_populates="creator")
    approved_contests = relationship("Contest", foreign_keys="Contest.approved_by_user_id", back_populates="approver")
    role_changes = relationship("RoleAudit", foreign_keys="RoleAudit.user_id", back_populates="user")
    
    # Self-referential relationships for user management
    created_by = relationship("User", remote_side=[id], foreign_keys=[created_by_user_id])
    role_assigned_by_user = relationship("User", remote_side=[id], foreign_keys=[role_assigned_by])
    
    def __repr__(self):
        return f"<User(id={self.id}, phone='{self.phone}', role='{self.role}')>"
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    @property
    def is_sponsor(self):
        return self.role == 'sponsor'
    
    @property
    def is_user(self):
        return self.role == 'user'
