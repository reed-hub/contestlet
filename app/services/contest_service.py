from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_
from datetime import datetime
from app.models.contest import Contest
from app.models.entry import Entry
from app.models.user import User
from app.models.sponsor_profile import SponsorProfile
from app.models.official_rules import OfficialRules
from app.models.sms_template import SMSTemplate
from app.schemas.admin import AdminContestCreate, AdminContestUpdate
from app.schemas.universal_contest import UniversalContestForm, UniversalContestResponse
from app.schemas.universal_contest_edit import UniversalContestFormEdit
from app.core.exceptions import (
    raise_resource_not_found, 
    raise_validation_error,
    raise_business_logic_error,
    ErrorCode
)
from app.core.datetime_utils import utc_now
from app.core.config import get_settings
from app.core.contest_status import (
    calculate_contest_status, 
    can_edit_contest, 
    can_delete_contest,
    ContestStatus as StatusEnum
)
from app.models.contest_status_audit import ContestStatusAudit


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
                joinedload(Contest.approver),
                joinedload(Contest.sponsor_profile)  # Added sponsor profile
            )
        
        return query.filter(Contest.id == contest_id).first()
    
    def get_all_contests(self, limit: int = 100) -> List[Contest]:
        """Get all contests (for admin access)"""
        return (
            self.db.query(Contest)
            .options(
                joinedload(Contest.creator),
                joinedload(Contest.approver),
                joinedload(Contest.entries),
                joinedload(Contest.sponsor_profile)  # Added sponsor profile
            )
            .order_by(Contest.created_at.desc())
            .limit(limit)
            .all()
        )
    
    def get_active_contests(self, limit: int = 100) -> List[Contest]:
        """Get all active contests using enhanced status system"""
        return (
            self.db.query(Contest)
            .filter(Contest.status == "active")
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
        
        # Extract official_rules and sms_templates data separately (these are relationships, not columns)
        contest_dict = contest_data.dict()
        official_rules_data = contest_dict.pop('official_rules', None)
        sms_templates_data = contest_dict.pop('sms_templates', None)
        
        # Handle JSON array fields - convert None to empty lists
        if contest_dict.get('selected_states') is None:
            contest_dict['selected_states'] = []
        if contest_dict.get('contest_tags') is None:
            contest_dict['contest_tags'] = []
        if contest_dict.get('promotion_channels') is None:
            contest_dict['promotion_channels'] = []
        
        # Create contest instance
        contest = Contest(
            **contest_dict,
            created_by_user_id=creator_id,
            created_at=utc_now()
        )
        
        self.db.add(contest)
        self.db.commit()
        self.db.refresh(contest)
        
        # Create official rules if provided
        if official_rules_data:
            from app.models.official_rules import OfficialRules
            official_rules = OfficialRules(
                contest_id=contest.id,
                **official_rules_data
            )
            self.db.add(official_rules)
            self.db.commit()
        
        return contest
    
    def create_draft_contest(self, contest_data: AdminContestCreate, creator_id: int) -> Contest:
        """Create a new contest in draft status"""
        # Validate contest data (relaxed validation for drafts)
        self._validate_draft_contest_data(contest_data)
        
        # Extract official_rules data separately
        contest_dict = contest_data.dict()
        official_rules_data = contest_dict.pop('official_rules', None)
        
        # Set draft status
        contest_dict['status'] = StatusEnum.DRAFT
        
        contest = Contest(
            **contest_dict,
            created_by_user_id=creator_id,
            created_at=utc_now()
        )
        
        self.db.add(contest)
        self.db.commit()
        self.db.refresh(contest)
        
        # Create official rules if provided
        if official_rules_data:
            from app.models.official_rules import OfficialRules
            official_rules = OfficialRules(
                contest_id=contest.id,
                **official_rules_data
            )
            self.db.add(official_rules)
            self.db.commit()
        
        # Create initial status audit entry
        self._create_status_audit(
            contest_id=contest.id,
            old_status=None,
            new_status=StatusEnum.DRAFT,
            changed_by_user_id=creator_id,
            reason="Contest created as draft"
        )
        
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
    
    # =====================================================
    # ENHANCED STATUS MANAGEMENT METHODS
    # =====================================================
    
    def transition_contest_status(
        self, 
        contest_id: int, 
        new_status: str, 
        user_id: int, 
        user_role: str,
        reason: Optional[str] = None
    ) -> Contest:
        """Transition contest to a new status with validation and audit"""
        contest = self.get_contest_by_id(contest_id)
        if not contest:
            raise_resource_not_found("Contest", contest_id)
        
        old_status = contest.status
        
        # Validate transition is allowed
        self._validate_status_transition(contest, new_status, user_role, user_id)
        
        # Update contest status
        contest.status = new_status
        
        # No longer need backward compatibility fields - using enhanced status system only
        
        # Set approval metadata for published statuses
        if new_status in [StatusEnum.UPCOMING, StatusEnum.ACTIVE] and old_status == StatusEnum.AWAITING_APPROVAL:
            contest.approved_by_user_id = user_id
            contest.approved_at = utc_now()
        
        contest.updated_at = utc_now()
        
        # Create status audit entry
        self._create_status_audit(
            contest_id=contest_id,
            old_status=old_status,
            new_status=new_status,
            changed_by_user_id=user_id,
            reason=reason
        )
        
        self.db.commit()
        self.db.refresh(contest)
        
        return contest
    
    def submit_contest_for_approval(self, contest_id: int, user_id: int, message: Optional[str] = None) -> Contest:
        """Submit a draft contest for admin approval"""
        contest = self.get_contest_by_id(contest_id)
        if not contest:
            raise_resource_not_found("Contest", contest_id)
        
        # Validate contest is in draft or rejected status
        if contest.status not in [StatusEnum.DRAFT, StatusEnum.REJECTED]:
            raise_business_logic_error(
                ErrorCode.VALIDATION_ERROR,
                f"Cannot submit contest with status '{contest.status}' for approval"
            )
        
        # Validate contest data is complete for submission
        self._validate_contest_for_submission(contest)
        
        # Transition to awaiting approval
        reason = f"Submitted for approval. {message}" if message else "Submitted for approval"
        return self.transition_contest_status(
            contest_id, StatusEnum.AWAITING_APPROVAL, user_id, "sponsor", reason
        )
    
    def approve_contest(self, contest_id: int, admin_user_id: int, reason: Optional[str] = None) -> Contest:
        """Approve a contest (admin only)"""
        contest = self.get_contest_by_id(contest_id)
        if not contest:
            raise_resource_not_found("Contest", contest_id)
        
        if contest.status != StatusEnum.AWAITING_APPROVAL:
            raise_business_logic_error(
                ErrorCode.VALIDATION_ERROR,
                f"Cannot approve contest with status '{contest.status}'"
            )
        
        # Calculate appropriate published status based on timing
        now = utc_now()
        
        # Ensure contest times are timezone-aware for comparison
        start_time = contest.start_time
        end_time = contest.end_time
        
        if start_time.tzinfo is None:
            from datetime import timezone
            start_time = start_time.replace(tzinfo=timezone.utc)
        if end_time.tzinfo is None:
            from datetime import timezone
            end_time = end_time.replace(tzinfo=timezone.utc)
        
        if start_time > now:
            new_status = StatusEnum.UPCOMING
        elif end_time > now:
            new_status = StatusEnum.ACTIVE
        else:
            new_status = StatusEnum.ENDED
        
        return self.transition_contest_status(
            contest_id, new_status, admin_user_id, "admin", 
            reason or "Contest approved by admin"
        )
    
    def reject_contest(self, contest_id: int, admin_user_id: int, reason: str) -> Contest:
        """Reject a contest (admin only)"""
        contest = self.get_contest_by_id(contest_id)
        if not contest:
            raise_resource_not_found("Contest", contest_id)
        
        if contest.status != StatusEnum.AWAITING_APPROVAL:
            raise_business_logic_error(
                ErrorCode.VALIDATION_ERROR,
                f"Cannot reject contest with status '{contest.status}'"
            )
        
        return self.transition_contest_status(
            contest_id, StatusEnum.REJECTED, admin_user_id, "admin", reason
        )
    
    def create_contest_universal(self, form_data: UniversalContestForm, creator_id: int) -> Contest:
        """Create a new contest using universal form"""
        # Validate form data
        self._validate_universal_form(form_data, mode="create")
        
        # Get creator user to determine role-based sponsor assignment
        creator = self.db.query(User).filter(User.id == creator_id).first()
        if not creator:
            raise ValueError("Creator user not found")
        
        # Extract official_rules and sms_templates data separately
        form_dict = form_data.dict()
        official_rules_data = form_dict.pop('official_rules', None)
        sms_templates_data = form_dict.pop('sms_templates', None)
        
        # Remove edit-specific fields for creation
        form_dict.pop('admin_override', None)
        form_dict.pop('override_reason', None)
        
        # Handle role-based sponsor assignment
        self._handle_sponsor_assignment(form_dict, creator)
        
        # Handle JSON array fields - convert None to empty lists
        if form_dict.get('selected_states') is None:
            form_dict['selected_states'] = []
        if form_dict.get('contest_tags') is None:
            form_dict['contest_tags'] = []
        if form_dict.get('promotion_channels') is None:
            form_dict['promotion_channels'] = []
        
        # Create contest instance with draft status
        contest = Contest(
            **form_dict,
            created_by_user_id=creator_id,
            created_at=utc_now(),
            status="draft"  # Always start as draft
        )
        
        self.db.add(contest)
        self.db.commit()
        self.db.refresh(contest)
        
        # Create official rules if provided
        if official_rules_data:
            official_rules = OfficialRules(
                contest_id=contest.id,
                **official_rules_data
            )
            self.db.add(official_rules)
            self.db.commit()
        
        # Create SMS templates if provided
        if sms_templates_data:
            self._create_sms_templates(contest.id, sms_templates_data)
        
        return contest
    
    def update_contest_universal(self, contest_id: int, form_data: UniversalContestFormEdit, admin_user_id: int) -> Contest:
        """Update an existing contest using universal form"""
        contest = self.get_contest_by_id(contest_id)
        if not contest:
            raise_resource_not_found("Contest", contest_id)
        
        # Validate form data for editing
        self._validate_universal_form(form_data, mode="edit", existing_contest=contest)
        
        # Check edit permissions based on contest status
        self._validate_edit_permissions(contest, form_data)
        
        # Extract relationship data
        form_dict = form_data.dict(exclude_unset=True)
        official_rules_data = form_dict.pop('official_rules', None)
        sms_templates_data = form_dict.pop('sms_templates', None)
        
        # Remove edit-specific fields from contest update
        form_dict.pop('admin_override', None)
        form_dict.pop('override_reason', None)
        
        # Handle JSON array fields
        for field in ['selected_states', 'contest_tags', 'promotion_channels']:
            if field in form_dict and form_dict[field] is None:
                form_dict[field] = []
        
        # Update contest fields
        for field, value in form_dict.items():
            if hasattr(contest, field):
                setattr(contest, field, value)
        
        # Update official rules if provided
        if official_rules_data:
            if contest.official_rules:
                # Update existing official rules
                for field, value in official_rules_data.items():
                    if hasattr(contest.official_rules, field):
                        setattr(contest.official_rules, field, value)
            else:
                # Create new official rules
                official_rules = OfficialRules(
                    contest_id=contest.id,
                    **official_rules_data
                )
                self.db.add(official_rules)
        
        # Update SMS templates if provided
        if sms_templates_data:
            self._update_sms_templates(contest.id, sms_templates_data)
        
        self.db.commit()
        self.db.refresh(contest)
        
        return contest
    
    def _validate_universal_form(self, form_data: UniversalContestForm, mode: str, existing_contest: Contest = None):
        """Validate universal form data based on mode"""
        
        # Basic validation (handled by Pydantic)
        # Additional business logic validation can be added here
        
        if mode == "edit" and existing_contest:
            # Check if contest can be edited
            if not can_edit_contest(existing_contest.status, "admin", True):
                if not form_data.admin_override:
                    raise_business_logic_error(
                        ErrorCode.VALIDATION_ERROR,
                        f"Cannot edit contest with status '{existing_contest.status}' without admin override"
                    )
    
    def _validate_edit_permissions(self, contest: Contest, form_data: UniversalContestFormEdit):
        """Validate what fields can be edited based on contest status"""
        
        # If admin override is used, allow all edits
        if form_data.admin_override and form_data.override_reason:
            return
        
        # Define restricted fields for different statuses
        status_restrictions = {
            'active': [
                'start_time', 'end_time', 'contest_type', 'entry_method', 
                'winner_selection_method', 'minimum_age', 'max_entries_per_person',
                'total_entry_limit', 'location_type', 'selected_states'
            ],
            'ended': [
                'start_time', 'end_time', 'contest_type', 'entry_method',
                'winner_selection_method', 'minimum_age', 'max_entries_per_person',
                'total_entry_limit', 'location_type', 'selected_states', 'name'
            ],
            'complete': ['*']  # No edits allowed for complete contests
        }
        
        restricted_fields = status_restrictions.get(contest.status, [])
        
        if '*' in restricted_fields:
            raise_business_logic_error(
                ErrorCode.VALIDATION_ERROR,
                f"Cannot edit contests with status '{contest.status}'"
            )
        
        # Check if any restricted fields are being changed
        form_dict = form_data.dict(exclude_unset=True)
        attempted_changes = set(form_dict.keys())
        restricted_changes = attempted_changes.intersection(set(restricted_fields))
        
        if restricted_changes:
            raise_business_logic_error(
                ErrorCode.VALIDATION_ERROR,
                f"Cannot edit fields {list(restricted_changes)} on contest with status '{contest.status}' without admin override"
            )
    
    def _create_sms_templates(self, contest_id: int, templates_data: dict):
        """Create SMS templates for a contest"""
        # Implementation for SMS template creation
        # This would create SMSTemplate records based on the templates_data
        pass
    
    def _update_sms_templates(self, contest_id: int, templates_data: dict):
        """Update SMS templates for a contest"""
        # Implementation for SMS template updates
        # This would update existing SMSTemplate records
        pass
    
    def _handle_sponsor_assignment(self, form_dict: dict, creator: User) -> None:
        """Handle role-based sponsor assignment logic"""
        if creator.role == "sponsor":
            # For sponsors: auto-assign their own sponsor profile, ignore form input
            if creator.sponsor_profile:
                form_dict['sponsor_profile_id'] = creator.sponsor_profile.id
            else:
                raise ValueError("Sponsor user does not have a sponsor profile")
        elif creator.role == "admin":
            # For admins: use provided sponsor_profile_id or require selection
            sponsor_id = form_dict.get('sponsor_profile_id')
            if not sponsor_id:
                raise ValueError("Admin must select a sponsor for the contest")
            
            # Validate sponsor exists and is verified
            sponsor_profile = self.db.query(SponsorProfile).filter(
                SponsorProfile.id == sponsor_id,
                SponsorProfile.is_verified == True
            ).first()
            if not sponsor_profile:
                raise ValueError("Selected sponsor profile not found or not verified")
        else:
            # Regular users cannot create contests
            raise ValueError("Only sponsors and admins can create contests")
    
    def _generate_location_summary(self, contest: Contest) -> str:
        """Generate location summary for frontend display"""
        if contest.location_type == "united_states":
            return "Contest open to all United States residents"
        elif contest.location_type == "specific_states":
            if not contest.selected_states or len(contest.selected_states) == 0:
                return "No states selected"
            elif len(contest.selected_states) == 1:
                # You could add a state code to name mapping here
                return f"Contest open to {contest.selected_states[0]} residents only"
            elif len(contest.selected_states) <= 3:
                return f"Contest open to residents of {', '.join(contest.selected_states)}"
            else:
                return f"Contest open to residents of {len(contest.selected_states)} selected states"
        elif contest.location_type == "radius":
            if not contest.radius_address or not contest.radius_miles:
                return "Radius targeting not configured"
            return f"Contest open to residents within {contest.radius_miles} miles of {contest.radius_address}"
        else:
            return "Location targeting not configured"

    def get_contests_by_status(self, status: str, limit: int = 100) -> List[Contest]:
        """Get contests filtered by status"""
        return (
            self.db.query(Contest)
            .filter(Contest.status == status)
            .order_by(Contest.created_at.desc())
            .limit(limit)
            .all()
        )
    
    def get_approval_queue(self, limit: int = 100) -> List[Contest]:
        """Get contests awaiting approval"""
        return self.get_contests_by_status(StatusEnum.AWAITING_APPROVAL, limit)
    
    def update_contest_statuses(self) -> int:
        """Update contest statuses based on current time (batch job)"""
        now = utc_now()
        updated_count = 0
        
        # Get all published contests that might need status updates
        contests = (
            self.db.query(Contest)
            .filter(Contest.status.in_([
                StatusEnum.UPCOMING, StatusEnum.ACTIVE, StatusEnum.ENDED
            ]))
            .all()
        )
        
        for contest in contests:
            calculated_status = calculate_contest_status(
                contest.status, contest.start_time, contest.end_time, 
                contest.winner_selected_at, now
            )
            
            if calculated_status != contest.status:
                old_status = contest.status
                contest.status = calculated_status
                contest.updated_at = now
                
                # Create audit entry for automatic transitions
                self._create_status_audit(
                    contest_id=contest.id,
                    old_status=old_status,
                    new_status=calculated_status,
                    changed_by_user_id=None,  # System update
                    reason="Automatic status update based on time"
                )
                
                updated_count += 1
        
        if updated_count > 0:
            self.db.commit()
        
        return updated_count
    
    def _validate_draft_contest_data(self, contest_data: AdminContestCreate):
        """Validate contest data for draft creation (relaxed validation)"""
        # Only require basic fields for drafts
        if not contest_data.name or len(contest_data.name.strip()) < 3:
            raise_validation_error("Contest name must be at least 3 characters", "name")
    
    def _validate_contest_for_submission(self, contest: Contest):
        """Validate contest is ready for submission to admin"""
        errors = []
        
        if not contest.name or len(contest.name.strip()) < 3:
            errors.append("Contest name must be at least 3 characters")
        
        if not contest.description or len(contest.description.strip()) < 10:
            errors.append("Contest description must be at least 10 characters")
        
        if not contest.start_time or not contest.end_time:
            errors.append("Contest must have start and end times")
        elif contest.start_time >= contest.end_time:
            errors.append("Start time must be before end time")
        
        if not contest.prize_description:
            errors.append("Prize description is required")
        
        # Check for official rules
        if not contest.official_rules:
            errors.append("Official rules are required")
        
        if errors:
            raise_validation_error("; ".join(errors), "contest_validation")
    
    def _validate_status_transition(self, contest: Contest, new_status: str, user_role: str, user_id: int):
        """Validate that a status transition is allowed"""
        from app.core.contest_status import get_next_possible_statuses
        
        # Check if user has permission for this transition
        allowed_statuses = get_next_possible_statuses(contest.status, user_role)
        
        if new_status not in allowed_statuses:
            raise_business_logic_error(
                ErrorCode.VALIDATION_ERROR,
                f"Cannot transition from '{contest.status}' to '{new_status}' with role '{user_role}'"
            )
        
        # Additional validation for specific transitions
        if new_status == StatusEnum.ACTIVE:
            now = utc_now()
            if contest.start_time > now:
                raise_business_logic_error(
                    ErrorCode.VALIDATION_ERROR,
                    "Cannot activate contest before start time"
                )
    
    def _create_status_audit(
        self, 
        contest_id: int, 
        old_status: Optional[str], 
        new_status: str,
        changed_by_user_id: Optional[int],
        reason: Optional[str] = None
    ):
        """Create status audit trail entry"""
        audit_entry = ContestStatusAudit(
            contest_id=contest_id,
            old_status=old_status,
            new_status=new_status,
            changed_by_user_id=changed_by_user_id,
            reason=reason,
            created_at=utc_now()
        )
        
        self.db.add(audit_entry)
        # Note: Commit is handled by calling method
