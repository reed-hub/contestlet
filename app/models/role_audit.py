"""
Role Audit Model

Tracks all role changes for security and compliance.
Provides audit trail for role assignments and modifications.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from . import Base
from app.core.datetime_utils import utc_now


class RoleAudit(Base):
    __tablename__ = "role_audit"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    old_role = Column(String(20), nullable=True)  # NULL for initial assignments
    new_role = Column(String(20), nullable=False)
    changed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="role_changes")
    changed_by = relationship("User", foreign_keys=[changed_by_user_id])
    
    def __repr__(self):
        return f"<RoleAudit(user_id={self.user_id}, {self.old_role} -> {self.new_role})>"


class ContestApprovalAudit(Base):
    __tablename__ = "contest_approval_audit"
    
    id = Column(Integer, primary_key=True, index=True)
    contest_id = Column(Integer, ForeignKey("contests.id"), nullable=False, index=True)
    action = Column(String(20), nullable=False, index=True)  # 'approved', 'rejected', 'pending'
    approved_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    
    # Relationships
    contest = relationship("Contest", back_populates="approval_history")
    approved_by = relationship("User")
    
    def __repr__(self):
        return f"<ContestApprovalAudit(contest_id={self.contest_id}, action='{self.action}')>"
