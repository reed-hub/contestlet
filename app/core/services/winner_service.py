"""
Winner Service for Multiple Winners Feature

Handles all winner selection and management operations for contests.
Supports both single and multiple winner scenarios with backward compatibility.
"""

import random
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.models.contest import Contest
from app.models.entry import Entry
from app.models.contest_winner import ContestWinner
from app.models.user import User
from app.shared.exceptions.base import (
    BusinessException, 
    ContestException, 
    ValidationException,
    ResourceNotFoundException,
    ErrorCode
)
from app.core.datetime_utils import utc_now
from app.core.contest_status import calculate_contest_status


class WinnerSelectionResult:
    """Result object for winner selection operations"""
    
    def __init__(
        self, 
        success: bool, 
        message: str, 
        winners: List[ContestWinner] = None,
        total_entries: int = 0,
        selection_method: str = "random"
    ):
        self.success = success
        self.message = message
        self.winners = winners or []
        self.total_entries = total_entries
        self.selection_method = selection_method
    
    @property
    def total_winners(self) -> int:
        return len(self.winners)


class WinnerService:
    """
    Service for managing contest winners with multiple winner support.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def select_winners(
        self, 
        contest_id: int, 
        winner_count: Optional[int] = None,
        selection_method: str = "random",
        prize_tiers: Optional[List[Dict[str, Any]]] = None,
        admin_user_id: Optional[str] = None
    ) -> WinnerSelectionResult:
        """
        Select multiple winners for a contest.
        
        Args:
            contest_id: Contest ID
            winner_count: Number of winners to select (defaults to contest.winner_count)
            selection_method: Method for selection (random, manual)
            prize_tiers: Optional prize tier information
            admin_user_id: Admin performing the selection
            
        Returns:
            WinnerSelectionResult with selected winners
            
        Raises:
            ResourceNotFoundException: If contest not found
            ContestException: If contest is not eligible for winner selection
            BusinessException: If selection fails
        """
        # Get contest
        contest = self.db.query(Contest).filter(Contest.id == contest_id).first()
        if not contest:
            raise ResourceNotFoundException("Contest", contest_id)
        
        # Use contest's winner_count if not specified
        if winner_count is None:
            winner_count = contest.winner_count or 1
        
        # Validate contest eligibility
        self._validate_contest_for_winner_selection(contest)
        
        # Check if winners already selected
        existing_winners = self.db.query(ContestWinner).filter(
            ContestWinner.contest_id == contest_id
        ).count()
        
        if existing_winners > 0:
            raise BusinessException(
                error_code=ErrorCode.BUSINESS_RULE_VIOLATION,
                message=f"Contest already has {existing_winners} winners selected. Use reselect operation to change winners."
            )
        
        # Get eligible entries
        eligible_entries = self._get_eligible_entries(contest_id)
        
        if len(eligible_entries) == 0:
            return WinnerSelectionResult(
                success=False,
                message="No eligible entries found for winner selection",
                total_entries=0
            )
        
        if len(eligible_entries) < winner_count:
            raise BusinessException(
                error_code=ErrorCode.BUSINESS_RULE_VIOLATION,
                message=f"Not enough eligible entries ({len(eligible_entries)}) for {winner_count} winners"
            )
        
        # Select winners based on method
        if selection_method == "random":
            selected_entries = self._select_random_winners(eligible_entries, winner_count)
        else:
            raise ValidationException(f"Unsupported selection method: {selection_method}")
        
        # Create winner records
        winners = []
        for position, entry in enumerate(selected_entries, 1):
            prize_description = None
            if prize_tiers and position <= len(prize_tiers):
                prize_description = prize_tiers[position - 1].get('prize')
            
            winner = ContestWinner(
                contest_id=contest_id,
                entry_id=entry.id,
                winner_position=position,
                prize_description=prize_description,
                selected_at=utc_now()
            )
            
            self.db.add(winner)
            winners.append(winner)
            
            # Update entry status
            entry.selected = True
            entry.status = "winner"
        
        # Update contest legacy fields for backward compatibility
        if winners:
            first_winner = winners[0]
            contest.winner_entry_id = first_winner.entry_id
            contest.winner_phone = first_winner.phone
            contest.winner_selected_at = first_winner.selected_at
        
        # Update contest prize tiers if provided
        if prize_tiers:
            contest.prize_tiers = {"tiers": prize_tiers}
        
        self.db.commit()
        
        return WinnerSelectionResult(
            success=True,
            message=f"Successfully selected {len(winners)} winners",
            winners=winners,
            total_entries=len(eligible_entries),
            selection_method=selection_method
        )
    
    def get_contest_winners(self, contest_id: int) -> List[ContestWinner]:
        """
        Get all winners for a contest ordered by position.
        
        Args:
            contest_id: Contest ID
            
        Returns:
            List of ContestWinner objects
        """
        return self.db.query(ContestWinner).filter(
            ContestWinner.contest_id == contest_id
        ).order_by(ContestWinner.winner_position).all()
    
    def get_winner_by_position(self, contest_id: int, position: int) -> Optional[ContestWinner]:
        """
        Get a specific winner by position.
        
        Args:
            contest_id: Contest ID
            position: Winner position (1st, 2nd, etc.)
            
        Returns:
            ContestWinner or None if not found
        """
        return self.db.query(ContestWinner).filter(
            and_(
                ContestWinner.contest_id == contest_id,
                ContestWinner.winner_position == position
            )
        ).first()
    
    def reselect_winner(
        self, 
        contest_id: int, 
        position: int,
        admin_user_id: Optional[str] = None
    ) -> ContestWinner:
        """
        Reselect a winner for a specific position.
        
        Args:
            contest_id: Contest ID
            position: Winner position to reselect
            admin_user_id: Admin performing the reselection
            
        Returns:
            New ContestWinner object
            
        Raises:
            ResourceNotFoundException: If contest or winner not found
            BusinessException: If reselection fails
        """
        # Get contest
        contest = self.db.query(Contest).filter(Contest.id == contest_id).first()
        if not contest:
            raise ResourceNotFoundException("Contest", contest_id)
        
        # Get existing winner
        existing_winner = self.get_winner_by_position(contest_id, position)
        if not existing_winner:
            raise ResourceNotFoundException("Winner", f"position {position}")
        
        # Get eligible entries (excluding current winners)
        current_winner_entry_ids = [
            w.entry_id for w in self.get_contest_winners(contest_id) 
            if w.winner_position != position
        ]
        
        eligible_entries = self._get_eligible_entries(contest_id, exclude_entry_ids=current_winner_entry_ids)
        
        if not eligible_entries:
            raise BusinessException(
                error_code=ErrorCode.BUSINESS_RULE_VIOLATION,
                message="No eligible entries available for reselection"
            )
        
        # Select new winner
        new_entry = random.choice(eligible_entries)
        
        # Update existing winner record
        old_entry = existing_winner.entry
        if old_entry:
            old_entry.selected = False
            old_entry.status = "active"
        
        existing_winner.entry_id = new_entry.id
        existing_winner.selected_at = utc_now()
        existing_winner.notified_at = None  # Reset notification status
        existing_winner.claimed_at = None   # Reset claim status
        existing_winner.updated_at = utc_now()
        
        # Update new entry
        new_entry.selected = True
        new_entry.status = "winner"
        
        # Update contest legacy fields if this is the first place winner
        if position == 1:
            contest.winner_entry_id = new_entry.id
            contest.winner_phone = new_entry.user.phone if new_entry.user else None
            contest.winner_selected_at = existing_winner.selected_at
        
        self.db.commit()
        
        return existing_winner
    
    def remove_winner(self, contest_id: int, position: int) -> bool:
        """
        Remove a winner from a specific position.
        
        Args:
            contest_id: Contest ID
            position: Winner position to remove
            
        Returns:
            True if winner was removed
            
        Raises:
            ResourceNotFoundException: If winner not found
        """
        winner = self.get_winner_by_position(contest_id, position)
        if not winner:
            raise ResourceNotFoundException("Winner", f"position {position}")
        
        # Update entry status
        if winner.entry:
            winner.entry.selected = False
            winner.entry.status = "active"
        
        # Remove winner record
        self.db.delete(winner)
        
        # Update contest legacy fields if this was the first place winner
        if position == 1:
            contest = self.db.query(Contest).filter(Contest.id == contest_id).first()
            if contest:
                # Find new first place winner or clear legacy fields
                new_first_winner = self.get_winner_by_position(contest_id, 1)
                if new_first_winner:
                    contest.winner_entry_id = new_first_winner.entry_id
                    contest.winner_phone = new_first_winner.phone
                    contest.winner_selected_at = new_first_winner.selected_at
                else:
                    contest.winner_entry_id = None
                    contest.winner_phone = None
                    contest.winner_selected_at = None
        
        self.db.commit()
        return True
    
    def mark_winner_notified(self, contest_id: int, position: int) -> ContestWinner:
        """
        Mark a winner as notified.
        
        Args:
            contest_id: Contest ID
            position: Winner position
            
        Returns:
            Updated ContestWinner object
        """
        winner = self.get_winner_by_position(contest_id, position)
        if not winner:
            raise ResourceNotFoundException("Winner", f"position {position}")
        
        winner.mark_notified()
        self.db.commit()
        
        return winner
    
    def mark_winner_claimed(self, contest_id: int, position: int) -> ContestWinner:
        """
        Mark a winner as having claimed their prize.
        
        Args:
            contest_id: Contest ID
            position: Winner position
            
        Returns:
            Updated ContestWinner object
        """
        winner = self.get_winner_by_position(contest_id, position)
        if not winner:
            raise ResourceNotFoundException("Winner", f"position {position}")
        
        winner.mark_claimed()
        self.db.commit()
        
        return winner
    
    def _validate_contest_for_winner_selection(self, contest: Contest):
        """
        Validate that a contest is eligible for winner selection.
        
        Args:
            contest: Contest object
            
        Raises:
            ContestException: If contest is not eligible
        """
        current_time = utc_now()
        status = calculate_contest_status(
            contest.status,
            contest.start_time,
            contest.end_time,
            contest.winner_selected_at,
            current_time
        )
        
        # Contest must be ended or complete to select winners
        if status not in ['ended', 'complete']:
            raise ContestException(
                error_code=ErrorCode.CONTEST_NOT_ACTIVE,
                message=f"Cannot select winners for contest with status: {status}. Contest must be ended.",
                contest_id=contest.id,
                contest_status=status
            )
        
        # Check if contest has ended
        if contest.end_time > current_time:
            raise ContestException(
                error_code=ErrorCode.CONTEST_NOT_ACTIVE,
                message="Cannot select winners before contest ends",
                contest_id=contest.id
            )
    
    def _get_eligible_entries(
        self, 
        contest_id: int, 
        exclude_entry_ids: Optional[List[int]] = None
    ) -> List[Entry]:
        """
        Get eligible entries for winner selection.
        
        Args:
            contest_id: Contest ID
            exclude_entry_ids: Entry IDs to exclude
            
        Returns:
            List of eligible Entry objects
        """
        query = self.db.query(Entry).join(User).filter(
            and_(
                Entry.contest_id == contest_id,
                Entry.status == "active"
            )
        )
        
        if exclude_entry_ids:
            query = query.filter(~Entry.id.in_(exclude_entry_ids))
        
        return query.all()
    
    def _select_random_winners(self, entries: List[Entry], count: int) -> List[Entry]:
        """
        Select random winners from eligible entries.
        
        Args:
            entries: List of eligible entries
            count: Number of winners to select
            
        Returns:
            List of selected Entry objects
        """
        if len(entries) < count:
            raise BusinessException(
                error_code=ErrorCode.BUSINESS_RULE_VIOLATION,
                message=f"Not enough entries ({len(entries)}) to select {count} winners"
            )
        
        return random.sample(entries, count)
