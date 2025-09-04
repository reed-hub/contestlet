"""
Unit Tests for Manual Entry Validation and Business Logic
"""

import pytest
from pydantic import ValidationError
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch

from app.schemas.manual_entry import ManualEntryRequest, ManualEntryResponse
from app.core.services.contest_service import ContestService
from app.shared.exceptions.base import BusinessException, ContestException, ResourceNotFoundException


class TestManualEntryValidation:
    """Test manual entry request validation"""
    
    def test_valid_manual_entry_request(self):
        """Test valid manual entry request creation"""
        request = ManualEntryRequest(
            phone_number="+1234567890",
            admin_override=True,
            source="phone_call",
            notes="Customer called support"
        )
        
        assert request.phone_number == "+1234567890"
        assert request.admin_override is True
        assert request.source == "phone_call"
        assert request.notes == "Customer called support"
    
    def test_phone_number_validation_valid_formats(self):
        """Test valid phone number formats"""
        valid_numbers = [
            "+1234567890",      # US
            "+447700900123",    # UK
            "+33123456789",     # France
            "+81312345678",     # Japan
            "+61412345678",     # Australia
            "+49301234567",     # Germany
            "+86138000138000",  # China (longer)
        ]
        
        for phone in valid_numbers:
            request = ManualEntryRequest(
                phone_number=phone,
                admin_override=True
            )
            assert request.phone_number == phone
    
    def test_phone_number_validation_invalid_formats(self):
        """Test invalid phone number formats"""
        invalid_numbers = [
            "123-456-7890",     # US format with dashes
            "(123) 456-7890",   # US format with parentheses
            "1234567890",       # No country code
            "+",                # Just plus sign
            "invalid",          # Not a number
            "+1234",            # Too short
            "",                 # Empty string
            "+123456789012345678",  # Too long
        ]
        
        for phone in invalid_numbers:
            with pytest.raises(ValidationError) as exc_info:
                ManualEntryRequest(
                    phone_number=phone,
                    admin_override=True
                )
            assert "phone number" in str(exc_info.value).lower()
    
    def test_phone_number_cleaning(self):
        """Test phone number cleaning (spaces, dashes, parentheses)"""
        # Note: The current implementation validates E.164 format strictly
        # If we want to support cleaning, we'd need to update the validator
        
        # Test that clean E.164 numbers work
        clean_number = "+1234567890"
        request = ManualEntryRequest(
            phone_number=clean_number,
            admin_override=True
        )
        assert request.phone_number == clean_number
    
    def test_admin_override_validation(self):
        """Test admin_override field validation"""
        # Must be True
        request = ManualEntryRequest(
            phone_number="+1234567890",
            admin_override=True
        )
        assert request.admin_override is True
        
        # Cannot be False
        with pytest.raises(ValidationError) as exc_info:
            ManualEntryRequest(
                phone_number="+1234567890",
                admin_override=False
            )
        assert "admin_override must be true" in str(exc_info.value).lower()
    
    def test_source_validation(self):
        """Test source field validation"""
        valid_sources = [
            "manual_admin",
            "phone_call", 
            "event",
            "paper_form",
            "customer_service",
            "migration",
            "promotional"
        ]
        
        for source in valid_sources:
            request = ManualEntryRequest(
                phone_number="+1234567890",
                admin_override=True,
                source=source
            )
            assert request.source == source
        
        # Invalid source
        with pytest.raises(ValidationError) as exc_info:
            ManualEntryRequest(
                phone_number="+1234567890",
                admin_override=True,
                source="invalid_source"
            )
        assert "source must be one of" in str(exc_info.value).lower()
    
    def test_source_default_value(self):
        """Test source field default value"""
        request = ManualEntryRequest(
            phone_number="+1234567890",
            admin_override=True
        )
        assert request.source == "manual_admin"
    
    def test_notes_validation(self):
        """Test notes field validation"""
        # Valid notes
        request = ManualEntryRequest(
            phone_number="+1234567890",
            admin_override=True,
            notes="Customer called in to enter contest"
        )
        assert request.notes == "Customer called in to enter contest"
        
        # Empty notes (should be allowed)
        request = ManualEntryRequest(
            phone_number="+1234567890",
            admin_override=True,
            notes=""
        )
        assert request.notes == ""
        
        # No notes (should be allowed)
        request = ManualEntryRequest(
            phone_number="+1234567890",
            admin_override=True
        )
        assert request.notes is None
        
        # Very long notes (test max length)
        long_notes = "x" * 600  # Longer than 500 char limit
        with pytest.raises(ValidationError) as exc_info:
            ManualEntryRequest(
                phone_number="+1234567890",
                admin_override=True,
                notes=long_notes
            )
        assert "ensure this value has at most 500 characters" in str(exc_info.value).lower()


class TestManualEntryBusinessLogic:
    """Test manual entry business logic in ContestService"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_db = Mock()
        self.mock_contest_repo = Mock()
        self.mock_entry_repo = Mock()
        self.mock_user_repo = Mock()
        
        self.contest_service = ContestService(
            self.mock_contest_repo,
            self.mock_entry_repo,
            self.mock_user_repo,
            self.mock_db
        )
    
    @patch('app.core.services.contest_service.utc_now')
    @patch('app.core.services.contest_service.calculate_contest_status')
    def test_manual_entry_success(self, mock_calc_status, mock_utc_now):
        """Test successful manual entry creation"""
        # Setup mocks
        mock_utc_now.return_value = datetime.now(timezone.utc)
        mock_calc_status.return_value = "active"
        
        # Mock contest
        mock_contest = Mock()
        mock_contest.id = 1
        mock_contest.status = "published"
        mock_contest.start_time = datetime.now(timezone.utc) - timedelta(hours=1)
        mock_contest.end_time = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_contest.winner_selected_at = None
        mock_contest.max_entries_per_person = None
        mock_contest.total_entry_limit = None
        self.mock_db.query().filter().first.return_value = mock_contest
        
        # Mock user (existing user)
        mock_user = Mock()
        mock_user.id = 123
        mock_user.phone = "+1234567890"
        self.mock_db.query().filter().first.side_effect = [mock_contest, mock_user]
        
        # Mock no existing entry
        self.mock_db.query().filter().first.side_effect = [mock_contest, mock_user, None]
        
        # Mock entry creation
        mock_entry = Mock()
        mock_entry.id = 456
        mock_entry.user_id = 123
        mock_entry.contest_id = 1
        mock_entry.source = "phone_call"
        mock_entry.created_by_admin_id = 789
        mock_entry.admin_notes = "Test entry"
        
        # Test manual entry creation
        result = self.contest_service.create_manual_entry(
            contest_id=1,
            phone_number="+1234567890",
            admin_user_id=789,
            source="phone_call",
            notes="Test entry"
        )
        
        # Verify database operations
        self.mock_db.add.assert_called()
        self.mock_db.commit.assert_called()
        self.mock_db.refresh.assert_called()
    
    def test_manual_entry_contest_not_found(self):
        """Test manual entry with non-existent contest"""
        # Mock no contest found
        self.mock_db.query().filter().first.return_value = None
        
        with pytest.raises(ResourceNotFoundException) as exc_info:
            self.contest_service.create_manual_entry(
                contest_id=999,
                phone_number="+1234567890",
                admin_user_id=1
            )
        
        assert "Contest" in str(exc_info.value)
        assert "999" in str(exc_info.value)
    
    @patch('app.core.services.contest_service.utc_now')
    @patch('app.core.services.contest_service.calculate_contest_status')
    def test_manual_entry_contest_wrong_status(self, mock_calc_status, mock_utc_now):
        """Test manual entry with contest in wrong status"""
        # Setup mocks
        mock_utc_now.return_value = datetime.now(timezone.utc)
        mock_calc_status.return_value = "complete"  # Not allowed for manual entries
        
        # Mock contest
        mock_contest = Mock()
        mock_contest.id = 1
        mock_contest.status = "complete"
        self.mock_db.query().filter().first.return_value = mock_contest
        
        with pytest.raises(ContestException) as exc_info:
            self.contest_service.create_manual_entry(
                contest_id=1,
                phone_number="+1234567890",
                admin_user_id=1
            )
        
        assert "complete" in str(exc_info.value).lower()
    
    @patch('app.core.services.contest_service.utc_now')
    @patch('app.core.services.contest_service.calculate_contest_status')
    def test_manual_entry_duplicate_prevention(self, mock_calc_status, mock_utc_now):
        """Test duplicate manual entry prevention"""
        # Setup mocks
        mock_utc_now.return_value = datetime.now(timezone.utc)
        mock_calc_status.return_value = "active"
        
        # Mock contest
        mock_contest = Mock()
        mock_contest.id = 1
        self.mock_db.query().filter().first.return_value = mock_contest
        
        # Mock existing user
        mock_user = Mock()
        mock_user.id = 123
        
        # Mock existing entry (duplicate)
        mock_existing_entry = Mock()
        mock_existing_entry.id = 456
        mock_existing_entry.source = "web_app"
        
        # Setup query chain: contest -> user -> existing entry
        self.mock_db.query().filter().first.side_effect = [
            mock_contest,  # Contest query
            mock_user,     # User query
            mock_existing_entry  # Existing entry query
        ]
        
        with pytest.raises(BusinessException) as exc_info:
            self.contest_service.create_manual_entry(
                contest_id=1,
                phone_number="+1234567890",
                admin_user_id=1
            )
        
        assert "already entered" in str(exc_info.value).lower()
    
    @patch('app.core.services.contest_service.utc_now')
    @patch('app.core.services.contest_service.calculate_contest_status')
    def test_manual_entry_user_creation(self, mock_calc_status, mock_utc_now):
        """Test automatic user creation for new phone numbers"""
        # Setup mocks
        mock_utc_now.return_value = datetime.now(timezone.utc)
        mock_calc_status.return_value = "active"
        
        # Mock contest
        mock_contest = Mock()
        mock_contest.id = 1
        mock_contest.max_entries_per_person = None
        mock_contest.total_entry_limit = None
        
        # Mock no existing user (will be created)
        self.mock_db.query().filter().first.side_effect = [
            mock_contest,  # Contest query
            None,          # User query (not found)
            None           # Entry query (not found)
        ]
        
        result = self.contest_service.create_manual_entry(
            contest_id=1,
            phone_number="+1555999888",
            admin_user_id=1,
            source="phone_call",
            notes="New user entry"
        )
        
        # Verify user creation
        self.mock_db.add.assert_called()  # Should add both user and entry
        self.mock_db.flush.assert_called()  # Should flush to get user ID


class TestManualEntryResponse:
    """Test manual entry response schema"""
    
    def test_manual_entry_response_creation(self):
        """Test manual entry response creation"""
        response = ManualEntryResponse(
            entry_id=123,
            contest_id=1,
            phone_number="+1234567890",
            created_at=datetime.now(timezone.utc),
            created_by_admin_id=456,
            source="phone_call",
            status="active",
            notes="Test entry"
        )
        
        assert response.entry_id == 123
        assert response.contest_id == 1
        assert response.phone_number == "+1234567890"
        assert response.created_by_admin_id == 456
        assert response.source == "phone_call"
        assert response.status == "active"
        assert response.notes == "Test entry"
    
    def test_manual_entry_response_optional_fields(self):
        """Test manual entry response with optional fields"""
        response = ManualEntryResponse(
            entry_id=123,
            contest_id=1,
            phone_number="+1234567890",
            created_at=datetime.now(timezone.utc),
            created_by_admin_id=456,
            source="manual_admin"
            # notes is optional
        )
        
        assert response.notes is None
        assert response.status == "active"  # Default value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
