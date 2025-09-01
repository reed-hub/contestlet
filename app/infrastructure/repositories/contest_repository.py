"""
Contest repository implementation.
Provides clean data access layer for contest operations.
"""

from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_

from app.models.contest import Contest


class SQLAlchemyContestRepository:
    """
    SQLAlchemy implementation of contest repository.
    Provides clean data access with proper error handling.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_by_id(self, contest_id: int, include_related: bool = True) -> Optional[Contest]:
        """
        Get contest by ID with optional related data loading.
        
        Args:
            contest_id: Contest ID
            include_related: Whether to load related entities
            
        Returns:
            Contest if found, None otherwise
        """
        query = self.db.query(Contest)
        
        if include_related:
            query = query.options(
                joinedload(Contest.entries),
                joinedload(Contest.official_rules),
                joinedload(Contest.sms_templates),
                joinedload(Contest.creator),
                joinedload(Contest.approver),
                joinedload(Contest.sponsor_profile)
            )
        
        return query.filter(Contest.id == contest_id).first()
    
    async def save(self, contest: Contest) -> Contest:
        """
        Save contest with proper transaction handling.
        
        Args:
            contest: Contest to save
            
        Returns:
            Saved contest with updated fields
        """
        self.db.add(contest)
        self.db.commit()
        self.db.refresh(contest)
        return contest
    
    async def delete(self, contest_id: int) -> bool:
        """
        Delete contest by ID.
        
        Args:
            contest_id: Contest ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        contest = self.db.query(Contest).filter(Contest.id == contest_id).first()
        if contest:
            self.db.delete(contest)
            self.db.commit()
            return True
        return False
    
    async def get_active_contests(self, limit: int = 100, offset: int = 0) -> List[Contest]:
        """
        Get active contests with pagination.
        
        Args:
            limit: Maximum number of contests to return
            offset: Number of contests to skip
            
        Returns:
            List of active contests
        """
        return (
            self.db.query(Contest)
            .filter(Contest.status == "active")
            .order_by(Contest.start_time.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
    
    async def get_all_contests(self, limit: int = 100, offset: int = 0) -> List[Contest]:
        """
        Get all contests with pagination (admin access).
        
        Args:
            limit: Maximum number of contests to return
            offset: Number of contests to skip
            
        Returns:
            List of all contests
        """
        return (
            self.db.query(Contest)
            .options(
                joinedload(Contest.creator),
                joinedload(Contest.approver),
                joinedload(Contest.entries)
            )
            .order_by(Contest.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
    
    async def get_contests_by_creator(self, creator_id: int, limit: int = 100) -> List[Contest]:
        """
        Get contests created by specific user.
        
        Args:
            creator_id: Creator user ID
            limit: Maximum number of contests to return
            
        Returns:
            List of contests created by user
        """
        return (
            self.db.query(Contest)
            .filter(Contest.created_by_user_id == creator_id)
            .order_by(Contest.created_at.desc())
            .limit(limit)
            .all()
        )
    
    async def get_contests_by_sponsor(self, sponsor_id: int, limit: int = 100) -> List[Contest]:
        """
        Get contests by sponsor profile.
        
        Args:
            sponsor_id: Sponsor profile ID
            limit: Maximum number of contests to return
            
        Returns:
            List of contests by sponsor
        """
        return (
            self.db.query(Contest)
            .filter(Contest.sponsor_profile_id == sponsor_id)
            .order_by(Contest.created_at.desc())
            .limit(limit)
            .all()
        )
    
    async def search_contests(
        self, 
        search_term: Optional[str] = None,
        status_filter: Optional[str] = None,
        location_filter: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Contest]:
        """
        Search contests with multiple filters.
        
        Args:
            search_term: Search in name and description
            status_filter: Filter by status
            location_filter: Filter by location
            limit: Maximum results
            offset: Results to skip
            
        Returns:
            List of matching contests
        """
        query = self.db.query(Contest)
        
        # Apply filters
        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.filter(
                or_(
                    Contest.name.ilike(search_pattern),
                    Contest.description.ilike(search_pattern)
                )
            )
        
        if status_filter:
            query = query.filter(Contest.status == status_filter)
        
        if location_filter:
            query = query.filter(Contest.location.ilike(f"%{location_filter}%"))
        
        return (
            query.order_by(Contest.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
    
    async def count_contests(self, status_filter: Optional[str] = None) -> int:
        """
        Count contests with optional status filter.
        
        Args:
            status_filter: Optional status to filter by
            
        Returns:
            Number of contests
        """
        query = self.db.query(Contest)
        
        if status_filter:
            query = query.filter(Contest.status == status_filter)
        
        return query.count()
