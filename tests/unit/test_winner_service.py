"""
Unit Tests for WinnerService

Tests the core business logic of the WinnerService class including
winner selection algorithms, validation, and edge cases.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.core.services.winner_service import WinnerService, WinnerSelectionResult
from app.models.contest import Contest
from app.models.entry import Entry
from app.models.user import User
from app.models.contest_winner import ContestWinner
from app.shared.exceptions.base import BusinessException, ContestException, ResourceNotFoundException
from app.core.datetime_utils import utc_now


@pytest.mark.unit
class TestWinnerService:
    """Unit tests for WinnerService"""
    
    def setup_method(self):
        """Setup test data for each test method"""
        self.mock_db = Mock(spec=Session)
        self.winner_service = WinnerService(self.mock_db)
    
    def create_mock_contest(self, contest_id: int = 1, winner_count: int = 1, status: str = "ended") -> Contest:
        """Create a mock contest for testing"""
        contest = Mock(spec=Contest)
        contest.id = contest_id
        contest.winner_count = winner_count
        contest.status = status
        
        # Create proper datetime objects for comparison
        now = utc_now()
        contest.start_time = now - timedelta(days=1)
        contest.end_time = now - timedelta(hours=1)
        contest.winner_selected_at = None
        
        return contest
    
    def create_mock_entries(self, count: int, contest_id: int = 1) -> list:
        """Create mock entries for testing"""
        entries = []
        for i in range(count):
            entry = Mock(spec=Entry)
            entry.id = i + 1
            entry.contest_id = contest_id
            entry.user_id = i + 1
            entry.status = "active"
            entry.selected = False
            
            # Mock user
            user = Mock(spec=User)
            user.id = i + 1
            user.phone = f"+155500{i:04d}"
            entry.user = user
            
            entries.append(entry)
        return entries
    
    def test_select_single_winner_success(self):
        """Test successful single winner selection"""
        # Setup mocks
        contest = self.create_mock_contest(winner_count=1)
        entries = self.create_mock_entries(5)
        
        # Mock database queries with proper side effects
        def mock_query_side_effect(*args):
            if args[0] == Contest:
                # For getting contest
                mock_contest_query = Mock()
                mock_contest_query.filter.return_value.first.return_value = contest
                return mock_contest_query
            elif args[0] == ContestWinner:
                # For checking existing winners
                mock_winner_query = Mock()
                mock_winner_query.filter.return_value.count.return_value = 0
                return mock_winner_query
            else:
                # For getting eligible entries
                mock_entry_query = Mock()
                mock_entry_query.join.return_value.filter.return_value.all.return_value = entries
                return mock_entry_query
        
        self.mock_db.query.side_effect = mock_query_side_effect
        
        # Mock winner creation
        created_winner = Mock(spec=ContestWinner)
        created_winner.id = 1
        created_winner.contest_id = 1
        created_winner.entry_id = 1
        created_winner.winner_position = 1
        created_winner.phone = "+15550000"
        
        self.mock_db.add.return_value = None
        
        # Test winner selection
        with patch('app.core.services.winner_service.calculate_contest_status') as mock_status:
            mock_status.return_value = "ended"
            
            with patch('random.sample') as mock_random:
                mock_random.return_value = [entries[0]]
                
                result = self.winner_service.select_winners(contest_id=1, winner_count=1)
        
        # Verify result
        assert isinstance(result, WinnerSelectionResult)
        assert result.success is True
        assert result.total_winners == 1
        assert result.total_entries == 5
        assert len(result.winners) == 1
        
        # Verify database operations
        self.mock_db.add.assert_called()
        self.mock_db.commit.assert_called()
    
    def test_select_multiple_winners_success(self):
        """Test successful multiple winner selection"""
        # Setup mocks
        contest = self.create_mock_contest(winner_count=3)
        entries = self.create_mock_entries(10)
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = contest
        self.mock_db.query.return_value.filter.return_value.count.return_value = 0  # No existing winners
        
        # Mock eligible entries query
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = entries
        self.mock_db.query.return_value = mock_query
        
        # Test winner selection
        with patch('app.core.services.winner_service.calculate_contest_status') as mock_status:
            mock_status.return_value = "ended"
            
            with patch('random.sample') as mock_random:
                mock_random.return_value = entries[:3]  # First 3 entries
                
                result = self.winner_service.select_winners(contest_id=1, winner_count=3)
        
        # Verify result
        assert result.success is True
        assert result.total_winners == 3
        assert result.total_entries == 10
        assert len(result.winners) == 3
        
        # Verify winner positions are sequential
        positions = [w.winner_position for w in result.winners]
        assert positions == [1, 2, 3]
    
    def test_select_winners_with_prize_tiers(self):
        """Test winner selection with prize tier configuration"""
        # Setup mocks
        contest = self.create_mock_contest(winner_count=2)
        entries = self.create_mock_entries(5)
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = contest
        self.mock_db.query.return_value.filter.return_value.count.return_value = 0
        
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = entries
        self.mock_db.query.return_value = mock_query
        
        prize_tiers = [
            {"position": 1, "prize": "$100 Gift Card"},
            {"position": 2, "prize": "$50 Gift Card"}
        ]
        
        # Test winner selection with prize tiers
        with patch('app.core.services.winner_service.calculate_contest_status') as mock_status:
            mock_status.return_value = "ended"
            
            with patch('random.sample') as mock_random:
                mock_random.return_value = entries[:2]
                
                result = self.winner_service.select_winners(
                    contest_id=1, 
                    winner_count=2,
                    prize_tiers=prize_tiers
                )
        
        # Verify prize descriptions are assigned
        assert result.success is True
        assert len(result.winners) == 2
        
        # Check that prize descriptions match the tiers
        for winner in result.winners:
            expected_prize = prize_tiers[winner.winner_position - 1]["prize"]
            assert winner.prize_description == expected_prize
    
    def test_contest_not_found_error(self):
        """Test error when contest is not found"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ResourceNotFoundException) as exc_info:
            self.winner_service.select_winners(contest_id=999)
        
        assert "Contest" in str(exc_info.value)
        assert "999" in str(exc_info.value)
    
    def test_contest_not_ended_error(self):
        """Test error when contest has not ended"""
        # Create active contest with future end time
        now = utc_now()
        contest = self.create_mock_contest(status="active")
        contest.end_time = now + timedelta(hours=1)  # Future end time
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = contest
        
        with patch('app.core.services.winner_service.calculate_contest_status') as mock_status:
            mock_status.return_value = "active"
            
            with pytest.raises(ContestException) as exc_info:
                self.winner_service.select_winners(contest_id=1)
        
        assert "Cannot select winners" in str(exc_info.value)
    
    def test_insufficient_entries_error(self):
        """Test error when not enough entries for winner count"""
        contest = self.create_mock_contest(winner_count=5)
        entries = self.create_mock_entries(2)  # Only 2 entries for 5 winners
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = contest
        self.mock_db.query.return_value.filter.return_value.count.return_value = 0
        
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = entries
        self.mock_db.query.return_value = mock_query
        
        with patch('app.core.services.winner_service.calculate_contest_status') as mock_status:
            mock_status.return_value = "ended"
            
            with pytest.raises(BusinessException) as exc_info:
                self.winner_service.select_winners(contest_id=1, winner_count=5)
        
        assert "Not enough eligible entries" in str(exc_info.value)
    
    def test_duplicate_winner_selection_error(self):
        """Test error when trying to select winners for contest that already has winners"""
        contest = self.create_mock_contest()
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = contest
        self.mock_db.query.return_value.filter.return_value.count.return_value = 1  # Existing winner
        
        with pytest.raises(BusinessException) as exc_info:
            self.winner_service.select_winners(contest_id=1)
        
        assert "already has" in str(exc_info.value)
        assert "winners selected" in str(exc_info.value)
    
    def test_get_contest_winners(self):
        """Test getting all winners for a contest"""
        # Mock winners
        winners = [
            Mock(spec=ContestWinner, winner_position=1, contest_id=1),
            Mock(spec=ContestWinner, winner_position=2, contest_id=1),
            Mock(spec=ContestWinner, winner_position=3, contest_id=1)
        ]
        
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = winners
        self.mock_db.query.return_value = mock_query
        
        result = self.winner_service.get_contest_winners(contest_id=1)
        
        assert len(result) == 3
        assert all(isinstance(w, Mock) for w in result)
    
    def test_get_winner_by_position(self):
        """Test getting a specific winner by position"""
        winner = Mock(spec=ContestWinner, winner_position=1, contest_id=1)
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = winner
        self.mock_db.query.return_value = mock_query
        
        result = self.winner_service.get_winner_by_position(contest_id=1, position=1)
        
        assert result == winner
    
    def test_reselect_winner_success(self):
        """Test successful winner reselection"""
        contest = self.create_mock_contest()
        existing_winner = Mock(spec=ContestWinner)
        existing_winner.winner_position = 1
        existing_winner.entry_id = 1
        existing_winner.entry = Mock(spec=Entry)
        
        new_entries = self.create_mock_entries(3)
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = contest
        
        # Mock get_winner_by_position call
        with patch.object(self.winner_service, 'get_winner_by_position') as mock_get_winner:
            mock_get_winner.return_value = existing_winner
            
            # Mock get_contest_winners call
            with patch.object(self.winner_service, 'get_contest_winners') as mock_get_winners:
                mock_get_winners.return_value = [existing_winner]
                
                # Mock eligible entries
                mock_query = Mock()
                mock_query.filter.return_value.all.return_value = new_entries
                self.mock_db.query.return_value = mock_query
                
                with patch('random.choice') as mock_choice:
                    mock_choice.return_value = new_entries[0]
                    
                    result = self.winner_service.reselect_winner(contest_id=1, position=1)
        
        assert result == existing_winner
        self.mock_db.commit.assert_called()
    
    def test_reselect_winner_not_found_error(self):
        """Test error when trying to reselect non-existent winner"""
        contest = self.create_mock_contest()
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = contest
        
        with patch.object(self.winner_service, 'get_winner_by_position') as mock_get_winner:
            mock_get_winner.return_value = None
            
            with pytest.raises(ResourceNotFoundException) as exc_info:
                self.winner_service.reselect_winner(contest_id=1, position=1)
        
        assert "Winner" in str(exc_info.value)
        assert "position 1" in str(exc_info.value)
    
    def test_remove_winner_success(self):
        """Test successful winner removal"""
        winner = Mock(spec=ContestWinner)
        winner.winner_position = 1
        winner.entry = Mock(spec=Entry)
        
        with patch.object(self.winner_service, 'get_winner_by_position') as mock_get_winner:
            mock_get_winner.return_value = winner
            
            result = self.winner_service.remove_winner(contest_id=1, position=1)
        
        assert result is True
        self.mock_db.delete.assert_called_with(winner)
        self.mock_db.commit.assert_called()
    
    def test_remove_winner_not_found_error(self):
        """Test error when trying to remove non-existent winner"""
        with patch.object(self.winner_service, 'get_winner_by_position') as mock_get_winner:
            mock_get_winner.return_value = None
            
            with pytest.raises(ResourceNotFoundException) as exc_info:
                self.winner_service.remove_winner(contest_id=1, position=1)
        
        assert "Winner" in str(exc_info.value)
        assert "position 1" in str(exc_info.value)
    
    def test_mark_winner_notified(self):
        """Test marking winner as notified"""
        winner = Mock(spec=ContestWinner)
        winner.mark_notified = Mock()
        
        with patch.object(self.winner_service, 'get_winner_by_position') as mock_get_winner:
            mock_get_winner.return_value = winner
            
            result = self.winner_service.mark_winner_notified(contest_id=1, position=1)
        
        assert result == winner
        winner.mark_notified.assert_called_once()
        self.mock_db.commit.assert_called()
    
    def test_mark_winner_claimed(self):
        """Test marking winner as claimed"""
        winner = Mock(spec=ContestWinner)
        winner.mark_claimed = Mock()
        
        with patch.object(self.winner_service, 'get_winner_by_position') as mock_get_winner:
            mock_get_winner.return_value = winner
            
            result = self.winner_service.mark_winner_claimed(contest_id=1, position=1)
        
        assert result == winner
        winner.mark_claimed.assert_called_once()
        self.mock_db.commit.assert_called()
    
    def test_validate_contest_for_winner_selection_success(self):
        """Test successful contest validation"""
        contest = self.create_mock_contest(status="ended")
        
        with patch('app.core.services.winner_service.calculate_contest_status') as mock_status:
            mock_status.return_value = "ended"
            
            # Should not raise any exception
            self.winner_service._validate_contest_for_winner_selection(contest)
    
    def test_validate_contest_for_winner_selection_active_contest_error(self):
        """Test validation error for active contest"""
        contest = self.create_mock_contest(status="active")
        
        with patch('app.core.services.winner_service.calculate_contest_status') as mock_status:
            mock_status.return_value = "active"
            
            with pytest.raises(ContestException) as exc_info:
                self.winner_service._validate_contest_for_winner_selection(contest)
        
        assert "Cannot select winners" in str(exc_info.value)
    
    def test_get_eligible_entries(self):
        """Test getting eligible entries"""
        entries = self.create_mock_entries(5)
        
        mock_query = Mock()
        mock_query.join.return_value.filter.return_value.all.return_value = entries
        self.mock_db.query.return_value = mock_query
        
        result = self.winner_service._get_eligible_entries(contest_id=1)
        
        assert len(result) == 5
        assert all(isinstance(e, Mock) for e in result)
    
    def test_get_eligible_entries_with_exclusions(self):
        """Test getting eligible entries with exclusions"""
        entries = self.create_mock_entries(3)
        
        mock_query = Mock()
        mock_query.join.return_value.filter.return_value.filter.return_value.all.return_value = entries
        self.mock_db.query.return_value = mock_query
        
        result = self.winner_service._get_eligible_entries(
            contest_id=1, 
            exclude_entry_ids=[1, 2]
        )
        
        assert len(result) == 3
    
    def test_select_random_winners_success(self):
        """Test random winner selection algorithm"""
        entries = self.create_mock_entries(10)
        
        with patch('random.sample') as mock_sample:
            mock_sample.return_value = entries[:3]
            
            result = self.winner_service._select_random_winners(entries, 3)
        
        assert len(result) == 3
        mock_sample.assert_called_once_with(entries, 3)
    
    def test_select_random_winners_insufficient_entries_error(self):
        """Test error when not enough entries for random selection"""
        entries = self.create_mock_entries(2)
        
        with pytest.raises(BusinessException) as exc_info:
            self.winner_service._select_random_winners(entries, 5)
        
        assert "Not enough entries" in str(exc_info.value)


@pytest.mark.unit
class TestWinnerSelectionResult:
    """Unit tests for WinnerSelectionResult class"""
    
    def test_winner_selection_result_creation(self):
        """Test creating WinnerSelectionResult"""
        winners = [Mock(spec=ContestWinner), Mock(spec=ContestWinner)]
        
        result = WinnerSelectionResult(
            success=True,
            message="Test message",
            winners=winners,
            total_entries=10,
            selection_method="random"
        )
        
        assert result.success is True
        assert result.message == "Test message"
        assert len(result.winners) == 2
        assert result.total_entries == 10
        assert result.selection_method == "random"
        assert result.total_winners == 2
    
    def test_winner_selection_result_empty_winners(self):
        """Test WinnerSelectionResult with empty winners list"""
        result = WinnerSelectionResult(
            success=False,
            message="No winners",
            total_entries=0
        )
        
        assert result.success is False
        assert result.total_winners == 0
        assert len(result.winners) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
