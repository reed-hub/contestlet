"""
Clean entry service with centralized entry operations.
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.entry import Entry
from app.models.user import User
from app.shared.exceptions.base import (
    ResourceNotFoundException, 
    AuthorizationException, 
    BusinessException,
    ErrorCode
)
from app.shared.types.pagination import PaginationParams, PaginatedResult, create_paginated_result
from app.shared.constants.auth import AuthConstants


class EntryService:
    """
    Clean entry service with centralized entry operations.
    """
    
    def __init__(self, entry_repo, contest_repo, user_repo, db: Session):
        self.entry_repo = entry_repo
        self.contest_repo = contest_repo
        self.user_repo = user_repo
        self.db = db
    
    async def get_user_entries(
        self, 
        user_id: int, 
        pagination: PaginationParams
    ):
        """
        Get all entries for a specific user with pagination.
        
        Args:
            user_id: User ID
            pagination: Pagination parameters
            
        Returns:
            Paginated result of user entries
        """
        # Get total count
        total = self.db.query(Entry).filter(Entry.user_id == user_id).count()
        
        # Get paginated entries
        entries = await self.entry_repo.get_entries_by_user(user_id, pagination.limit)
        
        # Apply pagination offset manually since repo method doesn't support it yet
        start_idx = pagination.offset
        end_idx = start_idx + pagination.limit
        paginated_entries = entries[start_idx:end_idx] if start_idx < len(entries) else []
        
        return create_paginated_result(paginated_entries, total, pagination)
    
    async def get_contest_entries(
        self,
        contest_id: int,
        pagination: PaginationParams
    ):
        """
        Get all entries for a specific contest with pagination.
        
        Args:
            contest_id: Contest ID
            pagination: Pagination parameters
            
        Returns:
            Paginated result of contest entries
            
        Raises:
            ResourceNotFoundException: If contest not found
        """
        # Verify contest exists
        contest = await self.contest_repo.get_by_id(contest_id)
        if not contest:
            raise ResourceNotFoundException("Contest", contest_id)
        
        # Get total count
        total = await self.entry_repo.count_entries_for_contest(contest_id)
        
        # Get paginated entries
        all_entries = await self.entry_repo.get_entries_by_contest(contest_id)
        
        # Apply pagination
        start_idx = pagination.offset
        end_idx = start_idx + pagination.limit
        paginated_entries = all_entries[start_idx:end_idx] if start_idx < len(all_entries) else []
        
        return create_paginated_result(paginated_entries, total, pagination)
    
    async def get_entry_details(
        self,
        entry_id: int,
        requesting_user_id: int,
        user_role: str
    ) -> Entry:
        """
        Get entry details with proper authorization.
        
        Args:
            entry_id: Entry ID
            requesting_user_id: ID of user requesting the entry
            user_role: Role of requesting user
            
        Returns:
            Entry details
            
        Raises:
            ResourceNotFoundException: If entry not found
            AuthorizationException: If user cannot access entry
        """
        entry = await self.entry_repo.get_by_id(entry_id, include_related=True)
        if not entry:
            raise ResourceNotFoundException("Entry", entry_id)
        
        # Check authorization
        if user_role != AuthConstants.ADMIN_ROLE and entry.user_id != requesting_user_id:
            raise AuthorizationException(
                message="You can only view your own entries",
                details={
                    "entry_id": entry_id,
                    "entry_owner": entry.user_id,
                    "requesting_user": requesting_user_id
                }
            )
        
        return entry
    
    async def delete_entry(
        self,
        entry_id: int,
        requesting_user_id: int,
        user_role: str
    ) -> bool:
        """
        Delete an entry with proper authorization and business rules.
        
        Args:
            entry_id: Entry ID to delete
            requesting_user_id: ID of user requesting deletion
            user_role: Role of requesting user
            
        Returns:
            True if deleted successfully
            
        Raises:
            ResourceNotFoundException: If entry not found
            AuthorizationException: If user cannot delete entry
            BusinessException: If deletion violates business rules
        """
        entry = await self.entry_repo.get_by_id(entry_id, include_related=True)
        if not entry:
            raise ResourceNotFoundException("Entry", entry_id)
        
        # Check authorization
        if user_role != AuthConstants.ADMIN_ROLE and entry.user_id != requesting_user_id:
            raise AuthorizationException(
                message="You can only delete your own entries",
                details={
                    "entry_id": entry_id,
                    "entry_owner": entry.user_id,
                    "requesting_user": requesting_user_id
                }
            )
        
        # Check business rules - can't delete entry if contest is complete or if user won
        if entry.contest:
            if entry.contest.status == "complete":
                raise BusinessException(
                    error_code=ErrorCode.OPERATION_NOT_ALLOWED,
                    message="Cannot delete entry from completed contest",
                    details={"contest_status": entry.contest.status}
                )
            
            if entry.contest.winner_entry_id == entry.id:
                raise BusinessException(
                    error_code=ErrorCode.OPERATION_NOT_ALLOWED,
                    message="Cannot delete winning entry",
                    details={"is_winner": True}
                )
        
        # Perform deletion
        self.db.delete(entry)
        self.db.commit()
        
        return True
    
    async def get_entry_statistics(self, user_id: Optional[int] = None) -> dict:
        """
        Get entry statistics for a user or globally.
        
        Args:
            user_id: Optional user ID for user-specific stats
            
        Returns:
            Entry statistics
        """
        if user_id:
            # User-specific statistics
            total_entries = self.db.query(Entry).filter(Entry.user_id == user_id).count()
            
            # Count entries by contest status
            from sqlalchemy import func
            from app.models.contest import Contest
            
            stats_query = (
                self.db.query(Contest.status, func.count(Entry.id))
                .join(Entry, Contest.id == Entry.contest_id)
                .filter(Entry.user_id == user_id)
                .group_by(Contest.status)
                .all()
            )
            
            status_breakdown = {status: count for status, count in stats_query}
            
            return {
                "total_entries": total_entries,
                "entries_by_contest_status": status_breakdown,
                "user_id": user_id
            }
        else:
            # Global statistics
            total_entries = self.db.query(Entry).count()
            unique_users = self.db.query(Entry.user_id).distinct().count()
            
            return {
                "total_entries": total_entries,
                "unique_participants": unique_users
            }
