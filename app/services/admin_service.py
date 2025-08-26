from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_
from app.models.user import User
from app.models.contest import Contest
from app.models.entry import Entry
from app.core.exceptions import (
    raise_resource_not_found,
    raise_authorization_error
)
from app.core.config import get_settings


class AdminService:
    """Service layer for admin operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
    
    def get_all_contests(self, limit: int = 100) -> List[Contest]:
        """Get all contests with admin access"""
        return (
            self.db.query(Contest)
            .options(
                joinedload(Contest.creator),
                joinedload(Contest.approver),
                joinedload(Contest.entries)
            )
            .order_by(Contest.created_at.desc())
            .limit(limit)
            .all()
        )
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID with admin access"""
        return (
            self.db.query(User)
            .options(
                joinedload(User.entries),
                joinedload(User.notifications),
                joinedload(User.sponsor_profile)
            )
            .filter(User.id == user_id)
            .first()
        )
    
    def get_all_users(self, limit: int = 100, role: Optional[str] = None) -> List[User]:
        """Get all users with optional role filtering"""
        query = self.db.query(User)
        
        if role:
            query = query.filter(User.role == role)
        
        return (
            query.options(
                joinedload(User.entries),
                joinedload(User.sponsor_profile)
            )
            .order_by(User.created_at.desc())
            .limit(limit)
            .all()
        )
    
    def update_user_role(self, user_id: int, new_role: str, admin_user_id: int) -> User:
        """Update user role with audit trail"""
        user = self.get_user_by_id(user_id)
        if not user:
            raise_resource_not_found("User", user_id)
        
        # Validate role
        valid_roles = {'admin', 'sponsor', 'user'}
        if new_role not in valid_roles:
            raise ValueError(f"Invalid role. Must be one of: {valid_roles}")
        
        # Update role
        old_role = user.role
        user.role = new_role
        user.role_assigned_at = func.now()
        user.role_assigned_by = admin_user_id
        
        # Create audit record
        from app.models.role_audit import RoleAudit
        audit = RoleAudit(
            user_id=user_id,
            old_role=old_role,
            new_role=new_role,
            assigned_by_user_id=admin_user_id,
            assigned_at=func.now()
        )
        
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        # User statistics
        total_users = self.db.query(func.count(User.id)).scalar()
        verified_users = self.db.query(func.count(User.id)).filter(User.is_verified == True).scalar()
        admin_users = self.db.query(func.count(User.id)).filter(User.role == 'admin').scalar()
        sponsor_users = self.db.query(func.count(User.id)).filter(User.role == 'sponsor').scalar()
        
        # Contest statistics
        total_contests = self.db.query(func.count(Contest.id)).scalar()
        active_contests = self.db.query(func.count(Contest.id)).filter(Contest.active == True).scalar()
        completed_contests = self.db.query(func.count(Contest.id)).filter(Contest.end_time < func.now()).scalar()
        
        # Entry statistics
        total_entries = self.db.query(func.count(Entry.id)).scalar()
        valid_entries = self.db.query(func.count(Entry.id)).filter(Entry.is_valid == True).scalar()
        winner_entries = self.db.query(func.count(Entry.id)).filter(Entry.is_winner == True).scalar()
        
        return {
            "users": {
                "total": total_users,
                "verified": verified_users,
                "admins": admin_users,
                "sponsors": sponsor_users
            },
            "contests": {
                "total": total_contests,
                "active": active_contests,
                "completed": completed_contests
            },
            "entries": {
                "total": total_entries,
                "valid": valid_entries,
                "winners": winner_entries
            }
        }
    
    def get_admin_dashboard_data(self) -> Dict[str, Any]:
        """Get data for admin dashboard"""
        # Recent contests
        recent_contests = (
            self.db.query(Contest)
            .order_by(Contest.created_at.desc())
            .limit(5)
            .all()
        )
        
        # Recent users
        recent_users = (
            self.db.query(User)
            .order_by(User.created_at.desc())
            .limit(5)
            .all()
        )
        
        # Recent entries
        recent_entries = (
            self.db.query(Entry)
            .options(joinedload(Entry.user), joinedload(Entry.contest))
            .order_by(Entry.created_at.desc())
            .limit(10)
            .all()
        )
        
        return {
            "recent_contests": recent_contests,
            "recent_users": recent_users,
            "recent_entries": recent_entries,
            "statistics": self.get_system_statistics()
        }
