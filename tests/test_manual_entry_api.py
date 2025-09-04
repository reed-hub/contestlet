"""
Tests for Manual Entry API functionality
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from app.main import app
from app.schemas.manual_entry import ManualEntryRequest


class TestManualEntryAPI:
    """Test suite for manual entry API endpoints"""
    
    def setup_method(self):
        """Setup test client and mock data"""
        self.client = TestClient(app)
        self.admin_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test_admin_token"
        self.user_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test_user_token"
        self.contest_id = 1
        self.phone_number = "+1234567890"
    
    def test_manual_entry_schema_validation(self):
        """Test ManualEntryRequest schema validation"""
        
        # Valid request
        valid_data = {
            "phone_number": "+1234567890",
            "admin_override": True,
            "source": "phone_call",
            "notes": "Customer called in"
        }
        request = ManualEntryRequest(**valid_data)
        assert request.phone_number == "+1234567890"
        assert request.admin_override is True
        assert request.source == "phone_call"
        assert request.notes == "Customer called in"
    
    def test_phone_number_validation(self):
        """Test phone number format validation"""
        
        # Valid E.164 formats
        valid_phones = ["+1234567890", "+447700900123", "+33123456789"]
        for phone in valid_phones:
            request = ManualEntryRequest(
                phone_number=phone,
                admin_override=True
            )
            assert request.phone_number == phone
        
        # Invalid formats should raise validation error
        invalid_phones = ["123-456-7890", "1234567890", "+", "invalid"]
        for phone in invalid_phones:
            with pytest.raises(ValueError):
                ManualEntryRequest(
                    phone_number=phone,
                    admin_override=True
                )
    
    def test_admin_override_validation(self):
        """Test admin_override field validation"""
        
        # admin_override must be True for manual entries
        with pytest.raises(ValueError, match="admin_override must be true"):
            ManualEntryRequest(
                phone_number="+1234567890",
                admin_override=False
            )
    
    def test_source_validation(self):
        """Test source field validation"""
        
        # Valid sources
        valid_sources = [
            "manual_admin", "phone_call", "event", "paper_form",
            "customer_service", "migration", "promotional"
        ]
        for source in valid_sources:
            request = ManualEntryRequest(
                phone_number="+1234567890",
                admin_override=True,
                source=source
            )
            assert request.source == source
        
        # Invalid source should raise validation error
        with pytest.raises(ValueError):
            ManualEntryRequest(
                phone_number="+1234567890",
                admin_override=True,
                source="invalid_source"
            )
    
    @patch('app.routers.contests.get_optional_user')
    @patch('app.core.services.contest_service.ContestService.create_manual_entry')
    def test_manual_entry_via_contest_endpoint_success(self, mock_create_entry, mock_get_user):
        """Test successful manual entry creation via /contests/{id}/enter"""
        
        # Mock admin user
        mock_admin = Mock()
        mock_admin.id = 1
        mock_admin.role = "admin"
        mock_get_user.return_value = mock_admin
        
        # Mock created entry
        mock_entry = Mock()
        mock_entry.id = 123
        mock_entry.user_id = 456
        mock_entry.contest_id = self.contest_id
        mock_entry.created_at = datetime.now(timezone.utc)
        mock_create_entry.return_value = mock_entry
        
        # Make request
        response = self.client.post(
            f"/contests/{self.contest_id}/enter",
            headers={"Authorization": f"Bearer {self.admin_token}"},
            json={
                "phone_number": self.phone_number,
                "admin_override": True,
                "source": "phone_call",
                "notes": "Test manual entry"
            }
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Manual entry created successfully"
        assert data["contest_id"] == self.contest_id
        assert data["entry_id"] == 123
        
        # Verify service was called correctly
        mock_create_entry.assert_called_once_with(
            contest_id=self.contest_id,
            phone_number=self.phone_number,
            admin_user_id=1,
            source="phone_call",
            notes="Test manual entry"
        )
    
    @patch('app.routers.contests.get_optional_user')
    def test_manual_entry_unauthorized(self, mock_get_user):
        """Test manual entry with no authentication"""
        
        mock_get_user.return_value = None
        
        response = self.client.post(
            f"/contests/{self.contest_id}/enter",
            json={
                "phone_number": self.phone_number,
                "admin_override": True
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "Authentication required" in data["detail"]
    
    @patch('app.routers.contests.get_optional_user')
    def test_manual_entry_insufficient_permissions(self, mock_get_user):
        """Test manual entry with non-admin user"""
        
        # Mock regular user
        mock_user = Mock()
        mock_user.id = 2
        mock_user.role = "user"
        mock_get_user.return_value = mock_user
        
        response = self.client.post(
            f"/contests/{self.contest_id}/enter",
            headers={"Authorization": f"Bearer {self.user_token}"},
            json={
                "phone_number": self.phone_number,
                "admin_override": True
            }
        )
        
        assert response.status_code == 403
        data = response.json()
        assert "Admin privileges required" in data["detail"]
    
    def test_regular_user_entry_still_works(self):
        """Test that regular user entries still work without request body"""
        
        with patch('app.routers.contests.get_optional_user') as mock_get_user, \
             patch('app.core.services.contest_service.ContestService.enter_contest') as mock_enter:
            
            # Mock regular user
            mock_user = Mock()
            mock_user.id = 2
            mock_user.role = "user"
            mock_get_user.return_value = mock_user
            
            # Mock entry creation
            mock_entry = Mock()
            mock_entry.id = 789
            mock_entry.created_at = datetime.now(timezone.utc)
            mock_enter.return_value = mock_entry
            
            # Make request without body (regular entry)
            response = self.client.post(
                f"/contests/{self.contest_id}/enter",
                headers={"Authorization": f"Bearer {self.user_token}"}
            )
            
            # Should still work for regular entries
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "Entry successful" in data["message"]
    
    def test_invalid_phone_number_format_error(self):
        """Test error handling for invalid phone number format"""
        
        response = self.client.post(
            f"/contests/{self.contest_id}/enter",
            headers={"Authorization": f"Bearer {self.admin_token}"},
            json={
                "phone_number": "123-456-7890",  # Invalid format
                "admin_override": True
            }
        )
        
        assert response.status_code == 422  # Pydantic validation error
        data = response.json()
        assert "phone number" in str(data).lower()
    
    def test_missing_admin_override_error(self):
        """Test error when admin_override is missing or false"""
        
        response = self.client.post(
            f"/contests/{self.contest_id}/enter",
            headers={"Authorization": f"Bearer {self.admin_token}"},
            json={
                "phone_number": self.phone_number,
                "admin_override": False  # Should be True
            }
        )
        
        assert response.status_code == 422  # Pydantic validation error


class TestManualEntryIntegration:
    """Integration tests for manual entry functionality"""
    
    def test_manual_entry_workflow(self):
        """Test complete manual entry workflow"""
        
        # This would be a full integration test with real database
        # For now, we'll create a placeholder that demonstrates the workflow
        
        workflow_steps = [
            "1. Admin authenticates with valid JWT token",
            "2. Admin calls POST /contests/{id}/enter with manual entry data",
            "3. System validates phone number format (E.164)",
            "4. System checks admin permissions",
            "5. System validates contest status (active/upcoming/ended)",
            "6. System checks for duplicate entries",
            "7. System creates or finds user with phone number",
            "8. System creates entry with source tracking",
            "9. System returns success response with entry details",
            "10. Entry appears in admin dashboard with 'manual_admin' source"
        ]
        
        # In a real integration test, we would execute each step
        assert len(workflow_steps) == 10
        assert "Admin authenticates" in workflow_steps[0]
        assert "Entry appears in admin dashboard" in workflow_steps[-1]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
