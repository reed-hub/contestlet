"""
Entry repository implementation.
Provides clean data access layer for entry operations.
"""

from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_

from app.models.entry import Entry


class SQLAlchemyEntryRepository:
    """
    SQLAlchemy implementation of entry repository.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_by_id(self, entry_id: int, include_related: bool = False) -> Optional[Entry]:
        """
        Get entry by ID with optional related data.
        
        Args:
            entry_id: Entry ID
            include_related: Whether to load related entities
            
        Returns:
            Entry if found, None otherwise
        """
        query = self.db.query(Entry)
        
        if include_related:
            query = query.options(
                joinedload(Entry.user),
                joinedload(Entry.contest)
            )
        
        return query.filter(Entry.id == entry_id).first()
    
    async def save(self, entry: Entry) -> Entry:
        """
        Save entry with proper transaction handling.
        
        Args:
            entry: Entry to save
            
        Returns:
            Saved entry with updated fields
        """
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry
    
    async def get_entries_by_user(self, user_id: int, limit: int = 100) -> List[Entry]:
        """
        Get all entries by a specific user.
        
        Args:
            user_id: User ID
            limit: Maximum entries to return
            
        Returns:
            List of user entries
        """
        return (
            self.db.query(Entry)
            .filter(Entry.user_id == user_id)
            .options(joinedload(Entry.contest))
            .order_by(Entry.created_at.desc())
            .limit(limit)
            .all()
        )
    
    async def get_entries_by_contest(self, contest_id: int, limit: int = 1000) -> List[Entry]:
        """
        Get all entries for a specific contest.
        
        Args:
            contest_id: Contest ID
            limit: Maximum entries to return
            
        Returns:
            List of contest entries
        """
        return (
            self.db.query(Entry)
            .filter(Entry.contest_id == contest_id)
            .options(joinedload(Entry.user))
            .order_by(Entry.created_at.desc())
            .limit(limit)
            .all()
        )
    
    async def get_user_entry_for_contest(self, user_id: int, contest_id: int) -> Optional[Entry]:
        """
        Get specific user's entry for a contest.
        
        Args:
            user_id: User ID
            contest_id: Contest ID
            
        Returns:
            Entry if found, None otherwise
        """
        return (
            self.db.query(Entry)
            .filter(
                and_(
                    Entry.user_id == user_id,
                    Entry.contest_id == contest_id
                )
            )
            .first()
        )
    
    async def count_entries_by_user_for_contest(self, user_id: int, contest_id: int) -> int:
        """
        Count entries by a user for a specific contest.
        
        Args:
            user_id: User ID
            contest_id: Contest ID
            
        Returns:
            Number of entries
        """
        return (
            self.db.query(Entry)
            .filter(
                and_(
                    Entry.user_id == user_id,
                    Entry.contest_id == contest_id
                )
            )
            .count()
        )
    
    async def count_entries_for_contest(self, contest_id: int) -> int:
        """
        Count total entries for a contest.
        
        Args:
            contest_id: Contest ID
            
        Returns:
            Number of entries
        """
        return self.db.query(Entry).filter(Entry.contest_id == contest_id).count()
    
    async def delete_entries_for_contest(self, contest_id: int) -> int:
        """
        Delete all entries for a contest.
        
        Args:
            contest_id: Contest ID
            
        Returns:
            Number of entries deleted
        """
        count = self.count_entries_for_contest(contest_id)
        self.db.query(Entry).filter(Entry.contest_id == contest_id).delete()
        return count
