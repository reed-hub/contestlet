"""
Tests for Multiple Winners Feature

Tests the complete multiple winners functionality including:
- Winner selection (single and multiple)
- Winner management operations
- Backward compatibility
- Prize tier configuration
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.contest import Contest
from app.models.entry import Entry
from app.models.user import User
from app.models.contest_winner import ContestWinner
from app.core.services.winner_service import WinnerService
from app.core.datetime_utils import utc_now
from app.shared.exceptions.base import BusinessException, ResourceNotFoundException


class TestMultipleWinners:
    """Test suite for multiple winners functionality"""
    
    def test_single_winner_selection(self, db_session: Session):
        """Test selecting a single winner (backward compatibility)"""
        # Create test contest
        contest = Contest(
            name="Single Winner Test",
            description="Test contest",
            start_time=utc_now() - timedelta(days=1),
            end_time=utc_now() - timedelta(hours=1),
            prize_description="$100 Gift Card",
            status="ended",
            winner_count=1
        )
        db_session.add(contest)
        db_session.flush()
        
        # Create test users and entries
        users = []
        entries = []
        for i in range(5):
            user = User(
                phone=f"+155500000{i}",
                role="user",
                is_verified=True
            )
            db_session.add(user)
            db_session.flush()
            users.append(user)
            
            entry = Entry(
                user_id=user.id,
                contest_id=contest.id,
                status="active"
            )
            db_session.add(entry)
            entries.append(entry)
        
        db_session.commit()
        
        # Test winner selection
        winner_service = WinnerService(db_session)
        result = winner_service.select_winners(contest.id, winner_count=1)
        
        assert result.success is True
        assert result.total_winners == 1
        assert result.total_entries == 5
        assert len(result.winners) == 1
        
        winner = result.winners[0]
        assert winner.contest_id == contest.id
        assert winner.winner_position == 1
        assert winner.entry_id in [e.id for e in entries]
        
        # Verify database state
        db_winners = db_session.query(ContestWinner).filter(
            ContestWinner.contest_id == contest.id
        ).all()
        assert len(db_winners) == 1
        
        # Verify legacy fields are updated
        db_session.refresh(contest)
        assert contest.winner_entry_id == winner.entry_id
        assert contest.winner_phone == winner.phone
        assert contest.winner_selected_at is not None
    
    def test_multiple_winner_selection(self, db_session: Session):
        """Test selecting multiple winners"""
        # Create test contest
        contest = Contest(
            name="Multiple Winners Test",
            description="Test contest with 3 winners",
            start_time=utc_now() - timedelta(days=1),
            end_time=utc_now() - timedelta(hours=1),
            prize_description="Various prizes",
            status="ended",
            winner_count=3
        )
        db_session.add(contest)
        db_session.flush()
        
        # Create test users and entries
        users = []
        entries = []
        for i in range(10):
            user = User(
                phone=f"+155500001{i}",
                role="user",
                is_verified=True
            )
            db_session.add(user)
            db_session.flush()
            users.append(user)
            
            entry = Entry(
                user_id=user.id,
                contest_id=contest.id,
                status="active"
            )
            db_session.add(entry)
            entries.append(entry)
        
        db_session.commit()
        
        # Test multiple winner selection
        winner_service = WinnerService(db_session)
        result = winner_service.select_winners(contest.id, winner_count=3)
        
        assert result.success is True
        assert result.total_winners == 3
        assert result.total_entries == 10
        assert len(result.winners) == 3
        
        # Verify winner positions are unique and sequential
        positions = [w.winner_position for w in result.winners]
        assert sorted(positions) == [1, 2, 3]
        
        # Verify all winners are from different entries
        entry_ids = [w.entry_id for w in result.winners]
        assert len(set(entry_ids)) == 3
        
        # Verify database state
        db_winners = db_session.query(ContestWinner).filter(
            ContestWinner.contest_id == contest.id
        ).order_by(ContestWinner.winner_position).all()
        assert len(db_winners) == 3
        
        for i, winner in enumerate(db_winners, 1):
            assert winner.winner_position == i
            assert winner.contest_id == contest.id
    
    def test_winner_selection_with_prize_tiers(self, db_session: Session):
        """Test winner selection with prize tier configuration"""
        # Create test contest
        contest = Contest(
            name="Prize Tiers Test",
            description="Test contest with prize tiers",
            start_time=utc_now() - timedelta(days=1),
            end_time=utc_now() - timedelta(hours=1),
            prize_description="Tiered prizes",
            status="ended",
            winner_count=3
        )
        db_session.add(contest)
        db_session.flush()
        
        # Create test entries
        for i in range(5):
            user = User(
                phone=f"+155500002{i}",
                role="user",
                is_verified=True
            )
            db_session.add(user)
            db_session.flush()
            
            entry = Entry(
                user_id=user.id,
                contest_id=contest.id,
                status="active"
            )
            db_session.add(entry)
        
        db_session.commit()
        
        # Define prize tiers
        prize_tiers = [
            {"position": 1, "prize": "$100 Gift Card"},
            {"position": 2, "prize": "$50 Gift Card"},
            {"position": 3, "prize": "$25 Gift Card"}
        ]
        
        # Test winner selection with prize tiers
        winner_service = WinnerService(db_session)
        result = winner_service.select_winners(
            contest.id, 
            winner_count=3,
            prize_tiers=prize_tiers
        )
        
        assert result.success is True
        assert len(result.winners) == 3
        
        # Verify prize descriptions are assigned correctly
        for winner in result.winners:
            expected_prize = prize_tiers[winner.winner_position - 1]["prize"]
            assert winner.prize_description == expected_prize
    
    def test_winner_reselection(self, db_session: Session):
        """Test reselecting a winner at a specific position"""
        # Create test contest with existing winners
        contest = Contest(
            name="Reselection Test",
            description="Test winner reselection",
            start_time=utc_now() - timedelta(days=1),
            end_time=utc_now() - timedelta(hours=1),
            prize_description="Test prize",
            status="ended",
            winner_count=2
        )
        db_session.add(contest)
        db_session.flush()
        
        # Create test entries
        entries = []
        for i in range(5):
            user = User(
                phone=f"+155500003{i}",
                role="user",
                is_verified=True
            )
            db_session.add(user)
            db_session.flush()
            
            entry = Entry(
                user_id=user.id,
                contest_id=contest.id,
                status="active"
            )
            db_session.add(entry)
            entries.append(entry)
        
        db_session.commit()
        
        # Select initial winners
        winner_service = WinnerService(db_session)
        initial_result = winner_service.select_winners(contest.id, winner_count=2)
        
        assert len(initial_result.winners) == 2
        original_first_winner = initial_result.winners[0]
        
        # Reselect first place winner
        new_winner = winner_service.reselect_winner(contest.id, position=1)
        
        assert new_winner.winner_position == 1
        assert new_winner.entry_id != original_first_winner.entry_id
        assert new_winner.notified_at is None  # Should reset notification status
        
        # Verify only 2 winners still exist
        all_winners = winner_service.get_contest_winners(contest.id)
        assert len(all_winners) == 2
    
    def test_winner_management_operations(self, db_session: Session):
        """Test winner management operations (notify, claim, remove)"""
        # Create test contest with winner
        contest = Contest(
            name="Management Test",
            description="Test winner management",
            start_time=utc_now() - timedelta(days=1),
            end_time=utc_now() - timedelta(hours=1),
            prize_description="Test prize",
            status="ended",
            winner_count=1
        )
        db_session.add(contest)
        db_session.flush()
        
        # Create test entry
        user = User(
            phone="+15550000999",
            role="user",
            is_verified=True
        )
        db_session.add(user)
        db_session.flush()
        
        entry = Entry(
            user_id=user.id,
            contest_id=contest.id,
            status="active"
        )
        db_session.add(entry)
        db_session.commit()
        
        # Select winner
        winner_service = WinnerService(db_session)
        result = winner_service.select_winners(contest.id, winner_count=1)
        winner = result.winners[0]
        
        # Test mark as notified
        updated_winner = winner_service.mark_winner_notified(contest.id, 1)
        assert updated_winner.is_notified is True
        assert updated_winner.notified_at is not None
        
        # Test mark as claimed
        updated_winner = winner_service.mark_winner_claimed(contest.id, 1)
        assert updated_winner.is_claimed is True
        assert updated_winner.claimed_at is not None
        
        # Test remove winner
        success = winner_service.remove_winner(contest.id, 1)
        assert success is True
        
        # Verify winner is removed
        remaining_winners = winner_service.get_contest_winners(contest.id)
        assert len(remaining_winners) == 0
    
    def test_insufficient_entries_error(self, db_session: Session):
        """Test error when not enough entries for winner count"""
        # Create test contest
        contest = Contest(
            name="Insufficient Entries Test",
            description="Test insufficient entries",
            start_time=utc_now() - timedelta(days=1),
            end_time=utc_now() - timedelta(hours=1),
            prize_description="Test prize",
            status="ended",
            winner_count=5
        )
        db_session.add(contest)
        db_session.flush()
        
        # Create only 2 entries
        for i in range(2):
            user = User(
                phone=f"+155500004{i}",
                role="user",
                is_verified=True
            )
            db_session.add(user)
            db_session.flush()
            
            entry = Entry(
                user_id=user.id,
                contest_id=contest.id,
                status="active"
            )
            db_session.add(entry)
        
        db_session.commit()
        
        # Test winner selection should fail
        winner_service = WinnerService(db_session)
        
        with pytest.raises(BusinessException) as exc_info:
            winner_service.select_winners(contest.id, winner_count=5)
        
        assert "Not enough eligible entries" in str(exc_info.value)
    
    def test_duplicate_winner_selection_error(self, db_session: Session):
        """Test error when trying to select winners for contest that already has winners"""
        # Create test contest
        contest = Contest(
            name="Duplicate Selection Test",
            description="Test duplicate selection error",
            start_time=utc_now() - timedelta(days=1),
            end_time=utc_now() - timedelta(hours=1),
            prize_description="Test prize",
            status="ended",
            winner_count=1
        )
        db_session.add(contest)
        db_session.flush()
        
        # Create test entry
        user = User(
            phone="+15550000888",
            role="user",
            is_verified=True
        )
        db_session.add(user)
        db_session.flush()
        
        entry = Entry(
            user_id=user.id,
            contest_id=contest.id,
            status="active"
        )
        db_session.add(entry)
        db_session.commit()
        
        # Select winner first time
        winner_service = WinnerService(db_session)
        result = winner_service.select_winners(contest.id, winner_count=1)
        assert result.success is True
        
        # Try to select winner again should fail
        with pytest.raises(BusinessException) as exc_info:
            winner_service.select_winners(contest.id, winner_count=1)
        
        assert "already has" in str(exc_info.value) and "winners selected" in str(exc_info.value)


@pytest.fixture
def db_session():
    """Create a test database session"""
    from app.database.database import get_db
    from app.models import Base
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # Create in-memory SQLite database for testing
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        yield session
    finally:
        session.close()
