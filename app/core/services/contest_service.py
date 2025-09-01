"""
Clean contest service with extracted business logic.
Centralizes all contest operations with proper error handling and business rules.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.contest import Contest
from app.models.entry import Entry
from app.models.user import User
from app.shared.exceptions.base import (
    BusinessException, 
    ContestException, 
    ValidationException,
    ResourceNotFoundException,
    ErrorCode
)
from app.shared.constants.contest import ContestConstants, ContestMessages
from app.shared.types.pagination import PaginationParams, ContestFilterParams, PaginatedResult, create_paginated_result
from app.core.datetime_utils import utc_now
from app.core.contest_status import calculate_contest_status, can_enter_contest, can_delete_contest
from app.core.geolocation import haversine_distance, validate_coordinates


class ContestDeletionResult:
    """Result object for contest deletion operations"""
    
    def __init__(self, contest_name: str, deleted_at: datetime, cleanup_summary: Dict[str, Any]):
        self.contest_name = contest_name
        self.deleted_at = deleted_at
        self.cleanup_summary = cleanup_summary
    
    def dict(self):
        return {
            "contest_name": self.contest_name,
            "deleted_at": self.deleted_at,
            "cleanup_summary": self.cleanup_summary
        }


class ContestService:
    """
    Clean contest service with centralized business logic.
    """
    
    def __init__(self, contest_repo, entry_repo, user_repo, db: Session):
        self.contest_repo = contest_repo
        self.entry_repo = entry_repo
        self.user_repo = user_repo
        self.db = db
    
    async def get_active_contests(
        self, 
        pagination: PaginationParams, 
        filters: ContestFilterParams
    ):
        """
        Get active contests with pagination and filtering.
        
        Args:
            pagination: Pagination parameters
            filters: Filter parameters
            
        Returns:
            Paginated result of active contests
        """
        current_time = utc_now()
        
        from sqlalchemy.orm import joinedload
        
        # Build base query for active contests with sponsor profile
        query = self.db.query(Contest).options(
            joinedload(Contest.sponsor_profile),
            joinedload(Contest.entries)
        ).filter(
            Contest.status.in_(ContestConstants.PUBLISHED_STATUSES),
            Contest.start_time <= current_time,
            Contest.end_time > current_time
        )
        
        # Apply filters
        if filters.location:
            query = query.filter(Contest.location.ilike(f"%{filters.location}%"))
        
        if filters.status:
            query = query.filter(Contest.status == filters.status)
        
        if filters.creator_id:
            query = query.filter(Contest.created_by_user_id == filters.creator_id)
        
        if filters.sponsor_id:
            query = query.filter(Contest.sponsor_profile_id == filters.sponsor_id)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        contests = query.offset(pagination.offset).limit(pagination.limit).all()
        
        # Enhance contests with calculated status and sponsor names
        enhanced_contests = []
        for contest in contests:
            status = calculate_contest_status(
                contest.status,
                contest.start_time,
                contest.end_time,
                contest.winner_selected_at,
                current_time
            )
            # Add calculated status to contest object
            contest.calculated_status = status
            
            # Populate sponsor name from sponsor profile
            contest.sponsor_name = None
            if contest.sponsor_profile and contest.sponsor_profile.company_name:
                contest.sponsor_name = contest.sponsor_profile.company_name
                
            enhanced_contests.append(contest)
        
        return create_paginated_result(enhanced_contests, total, pagination)
    
    async def get_nearby_contests(
        self,
        latitude: float,
        longitude: float,
        radius_miles: float,
        pagination: PaginationParams
    ):
        """
        Get contests near a specific location.
        
        Args:
            latitude: User latitude
            longitude: User longitude
            radius_miles: Search radius in miles
            pagination: Pagination parameters
            
        Returns:
            Paginated result of nearby contests
            
        Raises:
            ValidationException: If coordinates are invalid
        """
        # Validate coordinates
        if not validate_coordinates(latitude, longitude):
            raise ValidationException(
                message=ContestMessages.INVALID_COORDINATES,
                field_errors={"latitude": "Invalid latitude", "longitude": "Invalid longitude"}
            )
        
        current_time = utc_now()
        
        from sqlalchemy.orm import joinedload
        
        # Get all active contests with location data and sponsor profiles
        base_query = self.db.query(Contest).options(
            joinedload(Contest.sponsor_profile),
            joinedload(Contest.entries)
        ).filter(
            and_(
                Contest.status == "active",
                Contest.latitude.isnot(None),
                Contest.longitude.isnot(None)
            )
        )
        
        all_contests = base_query.all()
        
        # Filter by distance and calculate distances, populate sponsor names
        nearby_contests = []
        for contest in all_contests:
            distance = haversine_distance(latitude, longitude, contest.latitude, contest.longitude)
            if distance <= radius_miles:
                contest.distance_miles = round(distance, 2)
                
                # Populate sponsor name from sponsor profile
                contest.sponsor_name = None
                if contest.sponsor_profile and contest.sponsor_profile.company_name:
                    contest.sponsor_name = contest.sponsor_profile.company_name
                    
                nearby_contests.append(contest)
        
        # Sort by distance
        nearby_contests.sort(key=lambda x: x.distance_miles)
        
        # Apply pagination
        total = len(nearby_contests)
        start_idx = pagination.offset
        end_idx = start_idx + pagination.limit
        paginated_contests = nearby_contests[start_idx:end_idx]
        
        return create_paginated_result(paginated_contests, total, pagination)
    
    async def get_contest_details(self, contest_id: int, current_user: Optional[User] = None) -> Contest:
        """
        Get contest details with proper authorization and status calculation.
        
        Args:
            contest_id: Contest ID
            current_user: Optional current user for context
            
        Returns:
            Contest with calculated status and sponsor information
            
        Raises:
            ResourceNotFoundException: If contest not found
        """
        from sqlalchemy.orm import joinedload
        
        # Load contest with sponsor profile to get sponsor name
        contest = self.db.query(Contest).options(
            joinedload(Contest.sponsor_profile),
            joinedload(Contest.entries)
        ).filter(Contest.id == contest_id).first()
        
        if not contest:
            raise ResourceNotFoundException("Contest", contest_id)
        
        # Calculate current status
        current_time = utc_now()
        status = calculate_contest_status(
            contest.status,
            contest.start_time,
            contest.end_time,
            contest.winner_selected_at,
            current_time
        )
        
        # Add calculated fields
        contest.calculated_status = status
        contest.is_active = status == 'active'
        contest.entry_count = len(contest.entries) if contest.entries else 0
        contest.is_winner_selected = contest.winner_entry_id is not None
        
        # Populate sponsor name from sponsor profile
        contest.sponsor_name = None
        if contest.sponsor_profile and contest.sponsor_profile.company_name:
            contest.sponsor_name = contest.sponsor_profile.company_name
        
        return contest
    
    async def enter_contest(self, contest_id: int, user_id: int) -> Entry:
        """
        Enter a user into a contest with business rule validation.
        
        Args:
            contest_id: Contest ID
            user_id: User ID
            
        Returns:
            Created entry
            
        Raises:
            ResourceNotFoundException: If contest not found
            ContestException: If contest entry rules violated
            BusinessException: If entry limits exceeded
        """
        # Get contest
        contest = self.db.query(Contest).filter(Contest.id == contest_id).first()
        if not contest:
            raise ResourceNotFoundException("Contest", contest_id)
        
        # Check contest status
        current_time = utc_now()
        current_status = calculate_contest_status(
            contest.status,
            contest.start_time,
            contest.end_time,
            contest.winner_selected_at,
            current_time
        )
        
        # Validate entry is allowed
        if not can_enter_contest(current_status):
            status_messages = {
                "draft": ContestMessages.CONTEST_DRAFT,
                "awaiting_approval": ContestMessages.CONTEST_AWAITING_APPROVAL,
                "rejected": ContestMessages.CONTEST_REJECTED,
                "upcoming": ContestMessages.CONTEST_NOT_STARTED,
                "ended": ContestMessages.CONTEST_ENDED,
                "complete": ContestMessages.CONTEST_COMPLETE,
                "cancelled": ContestMessages.CONTEST_CANCELLED
            }
            
            message = status_messages.get(current_status, f"Contest is not accepting entries (status: {current_status})")
            raise ContestException(
                error_code=ErrorCode.CONTEST_NOT_ACTIVE,
                message=message,
                contest_id=contest_id,
                contest_status=current_status
            )
        
        # Check for duplicate entry
        existing_entry = self.db.query(Entry).filter(
            and_(
                Entry.user_id == user_id,
                Entry.contest_id == contest_id
            )
        ).first()
        
        if existing_entry:
            raise BusinessException(
                error_code=ErrorCode.ENTRY_DUPLICATE,
                message=ContestMessages.ENTRY_DUPLICATE,
                details={"contest_id": contest_id, "user_id": user_id}
            )
        
        # Check entry limits
        if contest.max_entries_per_person:
            user_entry_count = self.db.query(Entry).filter(
                and_(
                    Entry.contest_id == contest_id,
                    Entry.user_id == user_id
                )
            ).count()
            
            if user_entry_count >= contest.max_entries_per_person:
                raise BusinessException(
                    error_code=ErrorCode.ENTRY_LIMIT_EXCEEDED,
                    message=f"Maximum {contest.max_entries_per_person} entries per person allowed",
                    details={"limit": contest.max_entries_per_person, "current": user_entry_count}
                )
        
        # Check total entry limit
        if contest.total_entry_limit:
            total_entries = self.db.query(Entry).filter(Entry.contest_id == contest_id).count()
            if total_entries >= contest.total_entry_limit:
                raise BusinessException(
                    error_code=ErrorCode.ENTRY_LIMIT_EXCEEDED,
                    message=ContestMessages.ENTRY_LIMIT_REACHED,
                    details={"limit": contest.total_entry_limit, "current": total_entries}
                )
        
        # Create entry
        entry = Entry(
            user_id=user_id,
            contest_id=contest_id
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        
        return entry
    
    async def delete_contest(self, contest_id: int, user_id: int, user_role: str) -> ContestDeletionResult:
        """
        Delete contest with comprehensive business rules and cleanup.
        
        Args:
            contest_id: Contest ID
            user_id: User performing deletion
            user_role: User role
            
        Returns:
            Deletion result with cleanup summary
            
        Raises:
            ResourceNotFoundException: If contest not found
            BusinessException: If deletion not allowed
        """
        # Get contest
        contest = self.db.query(Contest).filter(Contest.id == contest_id).first()
        if not contest:
            raise ResourceNotFoundException("Contest", contest_id)
        
        # Check permissions
        if user_role == "sponsor" and contest.created_by_user_id != user_id:
            raise BusinessException(
                error_code=ErrorCode.INSUFFICIENT_PERMISSIONS,
                message=ContestMessages.OWNER_ACCESS_REQUIRED,
                details={"contest_owner": contest.created_by_user_id, "requesting_user": user_id}
            )
        
        # Check business rules
        now = utc_now()
        contest_status = calculate_contest_status(
            contest.status,
            contest.start_time,
            contest.end_time,
            contest.winner_selected_at,
            now
        )
        
        entry_count = self.db.query(Entry).filter(Entry.contest_id == contest_id).count()
        
        can_delete = can_delete_contest(
            status=contest_status,
            user_role=user_role,
            is_creator=(contest.created_by_user_id == user_id),
            has_entries=(entry_count > 0)
        )
        
        if not can_delete:
            # Determine specific protection reason
            if contest_status == "active":
                message = ContestMessages.CANNOT_DELETE_ACTIVE
            elif entry_count > 0:
                message = ContestMessages.CANNOT_DELETE_HAS_ENTRIES
            elif contest_status == "complete":
                message = ContestMessages.CANNOT_DELETE_COMPLETE
            else:
                message = f"Contest with status '{contest_status}' cannot be deleted"
            
            raise BusinessException(
                error_code=ErrorCode.CONTEST_PROTECTED,
                message=message,
                details={
                    "contest_status": contest_status,
                    "entry_count": entry_count,
                    "is_complete": contest_status == "complete"
                }
            )
        
        # Perform deletion with cleanup
        cleanup_summary = await self._perform_contest_cleanup(contest_id)
        
        # Store contest info before deletion
        contest_name = contest.name
        deleted_at = utc_now()
        
        # Delete the contest
        self.db.delete(contest)
        self.db.commit()
        
        return ContestDeletionResult(contest_name, deleted_at, cleanup_summary)
    
    async def _perform_contest_cleanup(self, contest_id: int) -> Dict[str, Any]:
        """
        Perform comprehensive cleanup of contest-related data.
        
        Args:
            contest_id: Contest ID
            
        Returns:
            Cleanup summary
        """
        cleanup_summary = {
            "entries_deleted": 0,
            "notifications_deleted": 0,
            "official_rules_deleted": 0,
            "sms_templates_deleted": 0,
            "dependencies_cleared": 0
        }
        
        try:
            # Delete SMS templates
            from app.models.sms_template import SMSTemplate
            sms_count = self.db.query(SMSTemplate).filter(SMSTemplate.contest_id == contest_id).count()
            self.db.query(SMSTemplate).filter(SMSTemplate.contest_id == contest_id).delete()
            cleanup_summary["sms_templates_deleted"] = sms_count
            cleanup_summary["dependencies_cleared"] += sms_count
            
            # Delete official rules
            from app.models.official_rules import OfficialRules
            rules_count = self.db.query(OfficialRules).filter(OfficialRules.contest_id == contest_id).count()
            self.db.query(OfficialRules).filter(OfficialRules.contest_id == contest_id).delete()
            cleanup_summary["official_rules_deleted"] = rules_count
            cleanup_summary["dependencies_cleared"] += rules_count
            
            # Delete notifications
            from app.models.notification import Notification
            notification_count = self.db.query(Notification).filter(Notification.contest_id == contest_id).count()
            self.db.query(Notification).filter(Notification.contest_id == contest_id).delete()
            cleanup_summary["notifications_deleted"] = notification_count
            cleanup_summary["dependencies_cleared"] += notification_count
            
        except Exception as e:
            # Log cleanup errors but don't fail the deletion
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Cleanup error for contest {contest_id}: {e}")
        
        return cleanup_summary
