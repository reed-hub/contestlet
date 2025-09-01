"""
User repository implementation.
Provides clean data access layer for user operations.
"""

from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_

from app.models.user import User


class SQLAlchemyUserRepository:
    """
    SQLAlchemy implementation of user repository.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_by_id(self, user_id: int, include_related: bool = False) -> Optional[User]:
        """
        Get user by ID with optional related data.
        
        Args:
            user_id: User ID
            include_related: Whether to load related entities
            
        Returns:
            User if found, None otherwise
        """
        query = self.db.query(User)
        
        if include_related:
            query = query.options(
                joinedload(User.entries),
                joinedload(User.notifications),
                joinedload(User.sponsor_profile),
                joinedload(User.admin_profile)
            )
        
        return query.filter(User.id == user_id).first()
    
    async def get_by_phone(self, phone: str) -> Optional[User]:
        """
        Get user by phone number.
        
        Args:
            phone: Phone number
            
        Returns:
            User if found, None otherwise
        """
        return self.db.query(User).filter(User.phone == phone).first()
    
    async def save(self, user: User) -> User:
        """
        Save user with proper transaction handling.
        
        Args:
            user: User to save
            
        Returns:
            Saved user with updated fields
        """
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    async def get_all_users(
        self, 
        role_filter: Optional[str] = None,
        verified_only: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> List[User]:
        """
        Get all users with optional filtering.
        
        Args:
            role_filter: Filter by role
            verified_only: Only return verified users
            limit: Maximum users to return
            offset: Users to skip
            
        Returns:
            List of users
        """
        query = self.db.query(User)
        
        if role_filter:
            query = query.filter(User.role == role_filter)
        
        if verified_only:
            query = query.filter(User.is_verified == True)
        
        return (
            query.options(
                joinedload(User.entries),
                joinedload(User.sponsor_profile)
            )
            .order_by(User.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
    
    async def count_users(self, role_filter: Optional[str] = None) -> int:
        """
        Count users with optional role filter.
        
        Args:
            role_filter: Optional role to filter by
            
        Returns:
            Number of users
        """
        query = self.db.query(User)
        
        if role_filter:
            query = query.filter(User.role == role_filter)
        
        return query.count()
    
    async def search_users(
        self,
        search_term: Optional[str] = None,
        role_filter: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[User]:
        """
        Search users by phone or related data.
        
        Args:
            search_term: Search term
            role_filter: Filter by role
            limit: Maximum results
            offset: Results to skip
            
        Returns:
            List of matching users
        """
        query = self.db.query(User)
        
        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.filter(User.phone.ilike(search_pattern))
        
        if role_filter:
            query = query.filter(User.role == role_filter)
        
        return (
            query.order_by(User.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
