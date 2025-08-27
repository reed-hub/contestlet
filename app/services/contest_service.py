from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_
from datetime import datetime
from app.models.contest import Contest
from app.models.entry import Entry
from app.models.user import User
from app.models.official_rules import OfficialRules
from app.models.sms_template import SMSTemplate
from app.schemas.admin import AdminContestCreate, AdminContestUpdate
from app.core.exceptions import (
    raise_resource_not_found, 
    raise_validation_error,
    raise_business_logic_error,
    ErrorCode
)
from app.core.datetime_utils import utc_now
from app.core.config import get_settings


class ContestService:
    """Service layer for contest management operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
    
    def get_contest_by_id(self, contest_id: int, include_related: bool = True) -> Optional[Contest]:
        """Get contest by ID with optional related data"""
        query = self.db.query(Contest)
        
        if include_related:
            query = query.options(
                joinedload(Contest.entries),
                joinedload(Contest.official_rules),
                joinedload(Contest.sms_templates),
                joinedload(Contest.creator),
                joinedload(Contest.approver)
            )
        
        return query.filter(Contest.id == contest_id).first()
    
    def get_all_contests(self, limit: int = 100) -> List[Contest]:
        """Get all contests (for admin access)"""
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
    
    def get_active_contests(self, limit: int = 100) -> List[Contest]:
        """Get all active contests"""
        now = utc_now()
        return (
            self.db.query(Contest)
            .filter(
                and_(
                    Contest.active == True,
                    Contest.start_time <= now,
                    Contest.end_time > now
                )
            )
            .order_by(Contest.start_time.desc())
            .limit(limit)
            .all()
        )
    
    def get_contests_by_location(
        self, 
        latitude: float, 
        longitude: float, 
        radius_km: float = 50,
        limit: int = 100
    ) -> List[Contest]:
        """Get contests within specified radius of location"""
        # Haversine formula for distance calculation
        haversine_formula = func.acos(
            func.cos(func.radians(latitude)) * 
            func.cos(func.radians(Contest.latitude)) * 
            func.cos(func.radians(Contest.longitude) - func.radians(longitude)) + 
            func.sin(func.radians(latitude)) * 
            func.sin(func.radians(Contest.latitude))
        ) * 6371  # Earth radius in km
        
        return (
            self.db.query(Contest)
            .filter(
                and_(
                    Contest.active == True,
                    Contest.latitude.isnot(None),
                    Contest.longitude.isnot(None),
                    haversine_formula <= radius_km
                )
            )
            .order_by(haversine_formula)
            .limit(limit)
            .all()
        )
    
    def create_contest(self, contest_data: AdminContestCreate, creator_id: int) -> Contest:
        """Create a new contest with validation"""
        # Validate contest data
        self._validate_contest_data(contest_data)
        
        # Create contest instance
        contest = Contest(
            **contest_data.dict(),
            created_by_user_id=creator_id,
            created_at=utc_now()
        )
        
        self.db.add(contest)
        self.db.commit()
        self.db.refresh(contest)
        
        return contest
    
    def update_contest(self, contest_id: int, contest_data: AdminContestUpdate, admin_user_id: Optional[int] = None) -> Contest:
        """Update existing contest with admin override support"""
        contest = self.get_contest_by_id(contest_id)
        if not contest:
            raise_resource_not_found("Contest", contest_id)
        
        # Extract admin override fields
        admin_override = contest_data.admin_override or False
        override_reason = contest_data.override_reason
        
        # Validate update data (with override support)
        self._validate_contest_update(contest, contest_data, admin_override, override_reason)
        
        # Log admin override if used
        if admin_override and contest.entries and contest.active:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Admin override: User {admin_user_id} modifying active contest {contest_id} "
                f"with {len(contest.entries)} entries. Reason: {override_reason}"
            )
            
            # Create audit log entry
            self._create_admin_override_audit(
                admin_user_id=admin_user_id,
                contest_id=contest_id,
                override_reason=override_reason,
                entry_count=len(contest.entries),
                modified_fields=list(contest_data.dict(exclude_unset=True, exclude={'admin_override', 'override_reason'}).keys())
            )
        
        # Update contest fields (exclude admin override fields from model update)
        update_fields = contest_data.dict(exclude_unset=True, exclude={'admin_override', 'override_reason'})
        for field, value in update_fields.items():
            if hasattr(contest, field):
                try:
                    # Skip complex nested objects that need special handling
                    if field == 'official_rules':
                        # Handle official rules separately if needed
                        continue
                    setattr(contest, field, value)
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to set field '{field}' with value '{value}' (type: {type(value)}): {e}")
                    # Continue with other fields, don't fail the entire update
                    continue
        
        contest.updated_at = utc_now()
        self.db.commit()
        self.db.refresh(contest)
        
        return contest
    
    def delete_contest(self, contest_id: int) -> bool:
        """Delete contest and related data"""
        contest = self.get_contest_by_id(contest_id)
        if not contest:
            raise_resource_not_found("Contest", contest_id)
        
        # Check if contest can be deleted
        if contest.entries:
            raise_business_logic_error(
                ErrorCode.RESOURCE_IN_USE,
                "Cannot delete contest with existing entries"
            )
        
        # Delete related data
        self.db.query(SMSTemplate).filter(SMSTemplate.contest_id == contest_id).delete()
        self.db.query(OfficialRules).filter(OfficialRules.contest_id == contest_id).delete()
        
        # Delete contest
        self.db.delete(contest)
        self.db.commit()
        
        return True
    
    def get_contest_entries(self, contest_id: int, limit: int = 100) -> List[Entry]:
        """Get all entries for a contest"""
        contest = self.get_contest_by_id(contest_id)
        if not contest:
            raise_resource_not_found("Contest", contest_id)
        
        return (
            self.db.query(Entry)
            .filter(Entry.contest_id == contest_id)
            .order_by(Entry.created_at.desc())
            .limit(limit)
            .all()
        )
    
    def select_winner(self, contest_id: int, admin_id: int) -> Optional[Entry]:
        """Select a random winner for a contest"""
        contest = self.get_contest_by_id(contest_id)
        if not contest:
            raise_resource_not_found("Contest", contest_id)
        
        # Check if contest is active
        if not contest.active:
            raise_business_logic_error(
                ErrorCode.CONTEST_NOT_ACTIVE,
                "Cannot select winner for inactive contest"
            )
        
        # Check if contest has ended
        if contest.end_time > utc_now():
            raise_business_logic_error(
                ErrorCode.CONTEST_NOT_ACTIVE,
                "Cannot select winner before contest ends"
            )
        
        # Get eligible entries
        entries = (
            self.db.query(Entry)
            .filter(
                and_(
                    Entry.contest_id == contest_id,
                    Entry.is_valid == True
                )
            )
            .all()
        )
        
        if not entries:
            return None
        
        # Select random winner
        import random
        winner = random.choice(entries)
        
        # Update contest with winner
        contest.winner_entry_id = winner.id
        contest.winner_phone = winner.user.phone
        contest.winner_selected_at = utc_now()
        contest.updated_at = utc_now()
        
        # Update entry
        winner.is_winner = True
        winner.updated_at = utc_now()
        
        self.db.commit()
        self.db.refresh(winner)
        
        return winner
    
    def _validate_contest_data(self, contest_data: AdminContestCreate):
        """Validate contest creation data"""
        # Check required fields
        if not contest_data.name or len(contest_data.name.strip()) < 3:
            raise_validation_error("Contest name must be at least 3 characters", "name")
        
        if not contest_data.description or len(contest_data.description.strip()) < 10:
            raise_validation_error("Contest description must be at least 10 characters", "description")
        
        # Validate dates
        if contest_data.start_time >= contest_data.end_time:
            raise_validation_error("Start time must be before end time", "start_time")
        
        if contest_data.start_time <= utc_now():
            raise_validation_error("Start time must be in the future", "start_time")
        
        # Validate entry limits
        if contest_data.max_entries_per_person and contest_data.max_entries_per_person <= 0:
            raise_validation_error("Max entries per person must be positive", "max_entries_per_person")
        
        if contest_data.total_entry_limit and contest_data.total_entry_limit <= 0:
            raise_validation_error("Total entry limit must be positive", "total_entry_limit")
    
    def _validate_contest_update(self, contest: Contest, update_data: AdminContestUpdate, admin_override: bool = False, override_reason: Optional[str] = None):
        """Validate contest update data with admin override support"""
        # Check if contest can be modified
        if contest.entries and contest.active:
            if not admin_override:
                raise_business_logic_error(
                    ErrorCode.RESOURCE_IN_USE,
                    "Cannot modify active contest with entries"
                )
            elif not override_reason:
                raise_validation_error("Override reason is required for admin override", "override_reason")
        
        # Validate date changes (still apply even with override for data integrity)
        if update_data.start_time and update_data.start_time <= utc_now():
            if not admin_override:
                raise_validation_error("Start time must be in the future", "start_time")
        
        if update_data.end_time and update_data.start_time and update_data.start_time >= update_data.end_time:
            raise_validation_error("Start time must be before end time", "start_time")
    
    def get_contest_statistics(self, contest_id: int) -> Dict[str, Any]:
        """Get comprehensive statistics for a contest"""
        contest = self.get_contest_by_id(contest_id)
        if not contest:
            raise_resource_not_found("Contest", contest_id)
        
        # Get entry statistics
        total_entries = self.db.query(func.count(Entry.id)).filter(Entry.contest_id == contest_id).scalar()
        valid_entries = self.db.query(func.count(Entry.id)).filter(
            and_(Entry.contest_id == contest_id, Entry.is_valid == True)
        ).scalar()
        winner_entries = self.db.query(func.count(Entry.id)).filter(
            and_(Entry.contest_id == contest_id, Entry.is_winner == True)
        ).scalar()
        
        return {
            "contest_id": contest_id,
            "contest_name": contest.name,
            "total_entries": total_entries,
            "valid_entries": valid_entries,
            "winner_entries": winner_entries,
            "is_active": contest.active,
            "has_winner": contest.winner_entry_id is not None,
            "created_at": contest.created_at,
            "start_time": contest.start_time,
            "end_time": contest.end_time
        }
    
    def _create_admin_override_audit(self, admin_user_id: int, contest_id: int, override_reason: str, entry_count: int, modified_fields: List[str]):
        """Create audit log entry for admin override actions"""
        try:
            from app.models.role_audit import RoleAudit
            
            # Use a special role value for admin override actions
            audit_entry = RoleAudit(
                user_id=admin_user_id,
                old_role="admin",  # Current role
                new_role="admin",  # Same role (this is not a role change)
                reason=(
                    f"ADMIN_OVERRIDE: Contest {contest_id} modified with {entry_count} entries. "
                    f"Reason: {override_reason}. "
                    f"Modified fields: {', '.join(modified_fields)}"
                ),
                created_at=utc_now()
            )
            
            self.db.add(audit_entry)
            # Note: Commit is handled by the calling method
            
        except Exception as e:
            # Log the error but don't fail the contest update
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create admin override audit log: {e}")
            # Continue with contest update even if audit logging fails
