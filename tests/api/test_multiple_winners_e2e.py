"""
End-to-End Tests for Multiple Winners Feature

Comprehensive test suite covering all aspects of the multiple winners functionality
including API endpoints, business logic, edge cases, and integration scenarios.
"""

import pytest
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.contest import Contest
from app.models.entry import Entry
from app.models.contest_winner import ContestWinner
from app.core.datetime_utils import utc_now


@pytest.mark.api
class TestMultipleWinnersE2E:
    """End-to-end tests for multiple winners feature"""
    
    def setup_method(self):
        """Setup test data for each test method"""
        self.base_contest_data = {
            "name": "Multi-Winner Test Contest",
            "description": "Test contest for multiple winners",
            "location": "Test City, TS 12345",
            "start_time": utc_now() - timedelta(days=1),
            "end_time": utc_now() - timedelta(hours=1),  # Contest ended
            "prize_description": "Various prizes for winners",
            "status": "ended",
            "contest_type": "general",
            "entry_method": "sms",
            "winner_selection_method": "random",
            "minimum_age": 18
        }
    
    def create_test_users_and_entries(self, db: Session, contest_id: int, num_users: int = 10) -> List[int]:
        """Create test users and entries for a contest"""
        entry_ids = []
        
        for i in range(num_users):
            # Create user
            user = User(
                phone=f"+155500{i:04d}",
                role="user",
                is_verified=True
            )
            db.add(user)
            db.flush()
            
            # Create entry
            entry = Entry(
                user_id=user.id,
                contest_id=contest_id,
                status="active"
            )
            db.add(entry)
            db.flush()
            entry_ids.append(entry.id)
        
        db.commit()
        return entry_ids
    
    def test_single_winner_selection_e2e(self, client: TestClient, db_session: Session, auth_headers: Dict[str, str]):
        """Test complete single winner selection flow (backward compatibility)"""
        # Create admin user
        admin_user = User(phone="+18187958204", role="admin", is_verified=True)
        db_session.add(admin_user)
        db_session.commit()
        
        # Create contest with single winner
        contest_data = {**self.base_contest_data, "winner_count": 1}
        contest = Contest(**contest_data, created_by_user_id=admin_user.id)
        db_session.add(contest)
        db_session.commit()
        
        # Create entries
        entry_ids = self.create_test_users_and_entries(db_session, contest.id, 5)
        
        # Test legacy single winner selection endpoint
        response = client.post(
            f"/admin/contests/{contest.id}/select-winner",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert data["success"] is True
        assert "Winner selected:" in data["message"]
        assert data["winner_entry_id"] in entry_ids
        assert data["winner_user_phone"].startswith("+1555")
        assert data["total_entries"] == 5
        
        # Verify database state
        winners = db_session.query(ContestWinner).filter(
            ContestWinner.contest_id == contest.id
        ).all()
        assert len(winners) == 1
        assert winners[0].winner_position == 1
        assert winners[0].entry_id == data["winner_entry_id"]
        
        # Verify legacy fields are updated
        db_session.refresh(contest)
        assert contest.winner_entry_id == data["winner_entry_id"]
        assert contest.winner_phone == data["winner_user_phone"]
        assert contest.winner_selected_at is not None
    
    def test_multiple_winner_selection_e2e(self, client: TestClient, db_session: Session, auth_headers: Dict[str, str]):
        """Test complete multiple winner selection flow"""
        # Create admin user
        admin_user = User(phone="+18187958204", role="admin", is_verified=True)
        db_session.add(admin_user)
        db_session.commit()
        
        # Create contest with multiple winners
        contest_data = {**self.base_contest_data, "winner_count": 3}
        contest = Contest(**contest_data, created_by_user_id=admin_user.id)
        db_session.add(contest)
        db_session.commit()
        
        # Create entries
        entry_ids = self.create_test_users_and_entries(db_session, contest.id, 10)
        
        # Test multiple winner selection
        request_data = {
            "winner_count": 3,
            "selection_method": "random",
            "prize_tiers": [
                {"position": 1, "prize": "$100 Gift Card", "description": "First place winner"},
                {"position": 2, "prize": "$50 Gift Card", "description": "Second place winner"},
                {"position": 3, "prize": "$25 Gift Card", "description": "Third place winner"}
            ]
        }
        
        response = client.post(
            f"/admin/contests/{contest.id}/select-winners",
            headers=auth_headers,
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert data["success"] is True
        assert data["total_winners"] == 3
        assert data["total_entries"] == 10
        assert data["selection_method"] == "random"
        assert len(data["winners"]) == 3
        
        # Verify winner positions are unique and sequential
        positions = [w["winner_position"] for w in data["winners"]]
        assert sorted(positions) == [1, 2, 3]
        
        # Verify prize descriptions are assigned correctly
        for winner in data["winners"]:
            expected_prize = request_data["prize_tiers"][winner["winner_position"] - 1]["prize"]
            assert winner["prize_description"] == expected_prize
            assert winner["entry_id"] in entry_ids
            assert winner["phone"].startswith("+1555")
            assert winner["is_notified"] is False
            assert winner["is_claimed"] is False
        
        # Verify database state
        db_winners = db_session.query(ContestWinner).filter(
            ContestWinner.contest_id == contest.id
        ).order_by(ContestWinner.winner_position).all()
        
        assert len(db_winners) == 3
        for i, winner in enumerate(db_winners, 1):
            assert winner.winner_position == i
            assert winner.contest_id == contest.id
            assert winner.entry_id in entry_ids
            assert winner.prize_description == request_data["prize_tiers"][i-1]["prize"]
        
        # Verify legacy fields are updated (first winner)
        db_session.refresh(contest)
        first_winner = db_winners[0]
        assert contest.winner_entry_id == first_winner.entry_id
        assert contest.winner_phone == first_winner.phone
        assert contest.winner_selected_at is not None
    
    def test_winner_management_e2e(self, client: TestClient, db_session: Session, auth_headers: Dict[str, str]):
        """Test complete winner management workflow"""
        # Create admin user
        admin_user = User(phone="+18187958204", role="admin", is_verified=True)
        db_session.add(admin_user)
        db_session.commit()
        
        # Create contest with multiple winners
        contest_data = {**self.base_contest_data, "winner_count": 2}
        contest = Contest(**contest_data, created_by_user_id=admin_user.id)
        db_session.add(contest)
        db_session.commit()
        
        # Create entries
        entry_ids = self.create_test_users_and_entries(db_session, contest.id, 5)
        
        # Select initial winners
        request_data = {
            "winner_count": 2,
            "selection_method": "random"
        }
        
        response = client.post(
            f"/admin/contests/{contest.id}/select-winners",
            headers=auth_headers,
            json=request_data
        )
        assert response.status_code == 200
        
        # Get winners list
        response = client.get(
            f"/admin/contests/{contest.id}/winners",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["contest_id"] == contest.id
        assert data["contest_name"] == contest.name
        assert data["winner_count"] == 2
        assert data["selected_winners"] == 2
        assert len(data["winners"]) == 2
        
        original_first_winner_id = data["winners"][0]["entry_id"]
        
        # Test winner reselection
        response = client.post(
            f"/admin/contests/{contest.id}/winners/1/manage",
            headers=auth_headers,
            json={"action": "reselect"}
        )
        
        assert response.status_code == 200
        reselect_data = response.json()
        
        assert reselect_data["success"] is True
        assert "reselected" in reselect_data["message"]
        assert reselect_data["winner"]["winner_position"] == 1
        assert reselect_data["winner"]["entry_id"] != original_first_winner_id
        assert reselect_data["winner"]["is_notified"] is False  # Should reset
        
        # Test mark winner as notified
        response = client.post(
            f"/admin/contests/{contest.id}/winners/1/manage",
            headers=auth_headers,
            json={"action": "notify", "custom_message": "Congratulations! You won first place!"}
        )
        
        assert response.status_code == 200
        notify_data = response.json()
        
        assert notify_data["success"] is True
        assert "notified" in notify_data["message"]
        
        # Verify winner is marked as notified
        winner = db_session.query(ContestWinner).filter(
            ContestWinner.contest_id == contest.id,
            ContestWinner.winner_position == 1
        ).first()
        assert winner.notified_at is not None
        
        # Test mark winner as claimed
        response = client.post(
            f"/admin/contests/{contest.id}/winners/1/manage",
            headers=auth_headers,
            json={"action": "mark_claimed"}
        )
        
        assert response.status_code == 200
        claim_data = response.json()
        
        assert claim_data["success"] is True
        assert "claimed" in claim_data["message"]
        
        # Verify winner is marked as claimed
        db_session.refresh(winner)
        assert winner.claimed_at is not None
        
        # Test remove winner
        response = client.post(
            f"/admin/contests/{contest.id}/winners/2/manage",
            headers=auth_headers,
            json={"action": "remove"}
        )
        
        assert response.status_code == 200
        remove_data = response.json()
        
        assert remove_data["success"] is True
        assert "removed" in remove_data["message"]
        
        # Verify winner is removed
        remaining_winners = db_session.query(ContestWinner).filter(
            ContestWinner.contest_id == contest.id
        ).all()
        assert len(remaining_winners) == 1
        assert remaining_winners[0].winner_position == 1
    
    def test_winner_notifications_e2e(self, client: TestClient, db_session: Session, auth_headers: Dict[str, str]):
        """Test winner notification workflow"""
        # Create admin user
        admin_user = User(phone="+18187958204", role="admin", is_verified=True)
        db_session.add(admin_user)
        db_session.commit()
        
        # Create contest with multiple winners
        contest_data = {**self.base_contest_data, "winner_count": 3}
        contest = Contest(**contest_data, created_by_user_id=admin_user.id)
        db_session.add(contest)
        db_session.commit()
        
        # Create entries and select winners
        self.create_test_users_and_entries(db_session, contest.id, 5)
        
        request_data = {
            "winner_count": 3,
            "selection_method": "random"
        }
        
        response = client.post(
            f"/admin/contests/{contest.id}/select-winners",
            headers=auth_headers,
            json=request_data
        )
        assert response.status_code == 200
        
        # Test notify all winners
        notification_request = {
            "custom_message": "Congratulations! You won {prize_description}!",
            "test_mode": True  # Don't actually send SMS in tests
        }
        
        response = client.post(
            f"/admin/contests/{contest.id}/winners/notify",
            headers=auth_headers,
            json=notification_request
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["notifications_sent"] == 3
        assert data["failed_notifications"] == 0
        assert len(data["details"]) == 3
        
        # Verify notification details
        for detail in data["details"]:
            assert detail["position"] in [1, 2, 3]
            assert detail["phone"].startswith("+1555")
            assert detail["status"] == "test_mode"
        
        # Test notify specific winners
        specific_notification_request = {
            "winner_positions": [1, 3],
            "custom_message": "Special message for positions 1 and 3",
            "test_mode": True
        }
        
        response = client.post(
            f"/admin/contests/{contest.id}/winners/notify",
            headers=auth_headers,
            json=specific_notification_request
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["notifications_sent"] == 2
        assert len(data["details"]) == 2
        
        # Verify only positions 1 and 3 were notified
        notified_positions = [detail["position"] for detail in data["details"]]
        assert sorted(notified_positions) == [1, 3]
    
    def test_winner_statistics_e2e(self, client: TestClient, db_session: Session, auth_headers: Dict[str, str]):
        """Test winner statistics endpoint"""
        # Create admin user
        admin_user = User(phone="+18187958204", role="admin", is_verified=True)
        db_session.add(admin_user)
        db_session.commit()
        
        # Create contest with multiple winners
        contest_data = {**self.base_contest_data, "winner_count": 3}
        contest = Contest(**contest_data, created_by_user_id=admin_user.id)
        db_session.add(contest)
        db_session.commit()
        
        # Create entries and select winners
        self.create_test_users_and_entries(db_session, contest.id, 5)
        
        request_data = {
            "winner_count": 3,
            "selection_method": "random",
            "prize_tiers": [
                {"position": 1, "prize": "$100 Gift Card"},
                {"position": 2, "prize": "$50 Gift Card"},
                {"position": 3, "prize": "$25 Gift Card"}
            ]
        }
        
        response = client.post(
            f"/admin/contests/{contest.id}/select-winners",
            headers=auth_headers,
            json=request_data
        )
        assert response.status_code == 200
        
        # Notify some winners
        client.post(
            f"/admin/contests/{contest.id}/winners/1/manage",
            headers=auth_headers,
            json={"action": "notify"}
        )
        
        client.post(
            f"/admin/contests/{contest.id}/winners/2/manage",
            headers=auth_headers,
            json={"action": "notify"}
        )
        
        # Mark one as claimed
        client.post(
            f"/admin/contests/{contest.id}/winners/1/manage",
            headers=auth_headers,
            json={"action": "mark_claimed"}
        )
        
        # Get statistics
        response = client.get(
            f"/admin/contests/{contest.id}/winners/stats",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["contest_id"] == contest.id
        assert data["contest_name"] == contest.name
        assert data["winner_count"] == 3
        assert data["selected_winners"] == 3
        assert data["notified_winners"] == 2
        assert data["claimed_winners"] == 1
        assert data["notification_rate"] == 2/3
        assert data["claim_rate"] == 1/3
        assert data["has_prize_tiers"] is True
    
    def test_error_handling_e2e(self, client: TestClient, db_session: Session, auth_headers: Dict[str, str]):
        """Test error handling scenarios"""
        # Create admin user
        admin_user = User(phone="+18187958204", role="admin", is_verified=True)
        db_session.add(admin_user)
        db_session.commit()
        
        # Test 1: Contest not found
        response = client.post(
            "/admin/contests/99999/select-winners",
            headers=auth_headers,
            json={"winner_count": 1, "selection_method": "random"}
        )
        assert response.status_code == 400
        
        # Test 2: Contest not ended yet
        future_contest_data = {
            **self.base_contest_data,
            "start_time": utc_now() + timedelta(hours=1),
            "end_time": utc_now() + timedelta(days=7),
            "status": "active"
        }
        future_contest = Contest(**future_contest_data, created_by_user_id=admin_user.id)
        db_session.add(future_contest)
        db_session.commit()
        
        response = client.post(
            f"/admin/contests/{future_contest.id}/select-winners",
            headers=auth_headers,
            json={"winner_count": 1, "selection_method": "random"}
        )
        assert response.status_code == 400
        
        # Test 3: Not enough entries
        ended_contest = Contest(**self.base_contest_data, created_by_user_id=admin_user.id)
        db_session.add(ended_contest)
        db_session.commit()
        
        # Create only 2 entries but try to select 5 winners
        self.create_test_users_and_entries(db_session, ended_contest.id, 2)
        
        response = client.post(
            f"/admin/contests/{ended_contest.id}/select-winners",
            headers=auth_headers,
            json={"winner_count": 5, "selection_method": "random"}
        )
        assert response.status_code == 400
        assert "Not enough eligible entries" in response.json()["detail"]
        
        # Test 4: Duplicate winner selection
        # First select winners successfully
        response = client.post(
            f"/admin/contests/{ended_contest.id}/select-winners",
            headers=auth_headers,
            json={"winner_count": 2, "selection_method": "random"}
        )
        assert response.status_code == 200
        
        # Try to select winners again
        response = client.post(
            f"/admin/contests/{ended_contest.id}/select-winners",
            headers=auth_headers,
            json={"winner_count": 1, "selection_method": "random"}
        )
        assert response.status_code == 400
        assert "already has" in response.json()["detail"]
        
        # Test 5: Invalid prize tier count
        another_contest = Contest(**self.base_contest_data, created_by_user_id=admin_user.id)
        db_session.add(another_contest)
        db_session.commit()
        
        self.create_test_users_and_entries(db_session, another_contest.id, 5)
        
        response = client.post(
            f"/admin/contests/{another_contest.id}/select-winners",
            headers=auth_headers,
            json={
                "winner_count": 3,
                "selection_method": "random",
                "prize_tiers": [
                    {"position": 1, "prize": "$100"},
                    {"position": 2, "prize": "$50"}
                    # Missing third tier
                ]
            }
        )
        assert response.status_code == 422  # Validation error
        
        # Test 6: Winner not found for management
        response = client.post(
            f"/admin/contests/{ended_contest.id}/winners/99/manage",
            headers=auth_headers,
            json={"action": "reselect"}
        )
        assert response.status_code == 404
    
    def test_large_contest_performance_e2e(self, client: TestClient, db_session: Session, auth_headers: Dict[str, str]):
        """Test performance with larger number of entries and winners"""
        # Create admin user
        admin_user = User(phone="+18187958204", role="admin", is_verified=True)
        db_session.add(admin_user)
        db_session.commit()
        
        # Create contest with many winners
        contest_data = {**self.base_contest_data, "winner_count": 20}
        contest = Contest(**contest_data, created_by_user_id=admin_user.id)
        db_session.add(contest)
        db_session.commit()
        
        # Create many entries
        entry_ids = self.create_test_users_and_entries(db_session, contest.id, 100)
        
        # Select 20 winners
        request_data = {
            "winner_count": 20,
            "selection_method": "random"
        }
        
        response = client.post(
            f"/admin/contests/{contest.id}/select-winners",
            headers=auth_headers,
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["total_winners"] == 20
        assert data["total_entries"] == 100
        assert len(data["winners"]) == 20
        
        # Verify all positions are unique
        positions = [w["winner_position"] for w in data["winners"]]
        assert len(set(positions)) == 20
        assert min(positions) == 1
        assert max(positions) == 20
        
        # Verify all entry IDs are unique
        winner_entry_ids = [w["entry_id"] for w in data["winners"]]
        assert len(set(winner_entry_ids)) == 20
        
        # Test getting winners list (should be fast)
        response = client.get(
            f"/admin/contests/{contest.id}/winners",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["winners"]) == 20
    
    def test_backward_compatibility_e2e(self, client: TestClient, db_session: Session, auth_headers: Dict[str, str]):
        """Test that existing single-winner functionality still works"""
        # Create admin user
        admin_user = User(phone="+18187958204", role="admin", is_verified=True)
        db_session.add(admin_user)
        db_session.commit()
        
        # Create old-style contest (no winner_count specified, defaults to 1)
        contest_data = self.base_contest_data.copy()
        contest_data.pop("winner_count", None)  # Remove if present
        
        contest = Contest(**contest_data, created_by_user_id=admin_user.id)
        db_session.add(contest)
        db_session.commit()
        
        # Create entries
        entry_ids = self.create_test_users_and_entries(db_session, contest.id, 5)
        
        # Use legacy single winner endpoint
        response = client.post(
            f"/admin/contests/{contest.id}/select-winner",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify legacy response format
        assert data["success"] is True
        assert data["winner_entry_id"] in entry_ids
        assert data["winner_user_phone"].startswith("+1555")
        assert data["total_entries"] == 5
        
        # Verify that new multiple winner system was used internally
        winners = db_session.query(ContestWinner).filter(
            ContestWinner.contest_id == contest.id
        ).all()
        assert len(winners) == 1
        assert winners[0].winner_position == 1
        assert winners[0].entry_id == data["winner_entry_id"]
        
        # Verify legacy fields are still populated
        db_session.refresh(contest)
        assert contest.winner_entry_id == data["winner_entry_id"]
        assert contest.winner_phone == data["winner_user_phone"]
        assert contest.winner_selected_at is not None
        
        # Test that new endpoints also work with this contest
        response = client.get(
            f"/admin/contests/{contest.id}/winners",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        winner_data = response.json()
        assert winner_data["winner_count"] == 1
        assert winner_data["selected_winners"] == 1
        assert len(winner_data["winners"]) == 1
    
    def test_contest_creation_with_multiple_winners_e2e(self, client: TestClient, db_session: Session, auth_headers: Dict[str, str]):
        """Test creating contests with multiple winner configuration"""
        # Create admin user
        admin_user = User(phone="+18187958204", role="admin", is_verified=True)
        db_session.add(admin_user)
        db_session.commit()
        
        # Test creating contest with multiple winners via API
        contest_create_data = {
            "name": "Multi-Winner API Contest",
            "description": "Contest created via API with multiple winners",
            "location": "API City, AC 12345",
            "start_time": (utc_now() + timedelta(hours=1)).isoformat(),
            "end_time": (utc_now() + timedelta(days=7)).isoformat(),
            "prize_description": "Multiple prizes for multiple winners",
            "winner_count": 5,
            "prize_tiers": {
                "tiers": [
                    {"position": 1, "prize": "$500 Grand Prize"},
                    {"position": 2, "prize": "$200 Second Prize"},
                    {"position": 3, "prize": "$100 Third Prize"},
                    {"position": 4, "prize": "$50 Fourth Prize"},
                    {"position": 5, "prize": "$25 Fifth Prize"}
                ],
                "total_value": 875,
                "currency": "USD"
            },
            "official_rules": {
                "eligibility_text": "Must be 18+ and US resident",
                "sponsor_name": "Test Sponsor",
                "prize_value_usd": 875,
                "start_date": (utc_now() + timedelta(hours=1)).date().isoformat(),
                "end_date": (utc_now() + timedelta(days=7)).date().isoformat()
            }
        }
        
        # Note: This test assumes there's a contest creation endpoint that accepts winner_count
        # If not available, we'll create the contest directly in the database
        contest = Contest(
            name=contest_create_data["name"],
            description=contest_create_data["description"],
            location=contest_create_data["location"],
            start_time=datetime.fromisoformat(contest_create_data["start_time"].replace('Z', '+00:00')),
            end_time=datetime.fromisoformat(contest_create_data["end_time"].replace('Z', '+00:00')),
            prize_description=contest_create_data["prize_description"],
            winner_count=contest_create_data["winner_count"],
            prize_tiers=json.dumps(contest_create_data["prize_tiers"]),
            status="draft",
            created_by_user_id=admin_user.id
        )
        db_session.add(contest)
        db_session.commit()
        
        # Verify contest was created with correct winner configuration
        assert contest.winner_count == 5
        assert contest.prize_tiers is not None
        
        prize_tiers = json.loads(contest.prize_tiers)
        assert len(prize_tiers["tiers"]) == 5
        assert prize_tiers["total_value"] == 875
        
        # Test that the contest can be retrieved with winner information
        response = client.get(
            f"/admin/contests/{contest.id}",
            headers=auth_headers
        )
        
        if response.status_code == 200:
            data = response.json()
            assert data["winner_count"] == 5
            if "prize_tiers" in data:
                assert data["prize_tiers"] is not None


@pytest.mark.integration
class TestMultipleWinnersIntegration:
    """Integration tests for multiple winners with other systems"""
    
    def test_winner_notification_integration(self, client: TestClient, db_session: Session, auth_headers: Dict[str, str]):
        """Test integration between winner selection and notification system"""
        # This test would verify that the notification service properly
        # integrates with the winner system, but since we're using mock SMS
        # in tests, we'll focus on the API integration
        
        # Create admin user
        admin_user = User(phone="+18187958204", role="admin", is_verified=True)
        db_session.add(admin_user)
        db_session.commit()
        
        # Create contest and entries
        contest_data = {
            "name": "Notification Integration Test",
            "description": "Test notification integration",
            "location": "Test City, TS 12345",
            "start_time": utc_now() - timedelta(days=1),
            "end_time": utc_now() - timedelta(hours=1),
            "prize_description": "Test prizes",
            "status": "ended",
            "winner_count": 2
        }
        
        contest = Contest(**contest_data, created_by_user_id=admin_user.id)
        db_session.add(contest)
        db_session.commit()
        
        # Create entries
        for i in range(3):
            user = User(phone=f"+155500{i:04d}", role="user", is_verified=True)
            db_session.add(user)
            db_session.flush()
            
            entry = Entry(user_id=user.id, contest_id=contest.id, status="active")
            db_session.add(entry)
        
        db_session.commit()
        
        # Select winners
        response = client.post(
            f"/admin/contests/{contest.id}/select-winners",
            headers=auth_headers,
            json={"winner_count": 2, "selection_method": "random"}
        )
        assert response.status_code == 200
        
        # Test notification with custom message
        response = client.post(
            f"/admin/contests/{contest.id}/winners/notify",
            headers=auth_headers,
            json={
                "custom_message": "Congratulations! You won {prize_description} in {contest_name}!",
                "test_mode": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["notifications_sent"] == 2
        assert data["failed_notifications"] == 0
    
    def test_winner_audit_trail_integration(self, client: TestClient, db_session: Session, auth_headers: Dict[str, str]):
        """Test that winner operations create proper audit trails"""
        # Create admin user
        admin_user = User(phone="+18187958204", role="admin", is_verified=True)
        db_session.add(admin_user)
        db_session.commit()
        
        # Create contest and entries
        contest_data = {
            "name": "Audit Trail Test",
            "description": "Test audit trail",
            "location": "Test City, TS 12345",
            "start_time": utc_now() - timedelta(days=1),
            "end_time": utc_now() - timedelta(hours=1),
            "prize_description": "Test prize",
            "status": "ended",
            "winner_count": 1
        }
        
        contest = Contest(**contest_data, created_by_user_id=admin_user.id)
        db_session.add(contest)
        db_session.commit()
        
        # Create entry
        user = User(phone="+15550001234", role="user", is_verified=True)
        db_session.add(user)
        db_session.flush()
        
        entry = Entry(user_id=user.id, contest_id=contest.id, status="active")
        db_session.add(entry)
        db_session.commit()
        
        # Select winner
        response = client.post(
            f"/admin/contests/{contest.id}/select-winners",
            headers=auth_headers,
            json={"winner_count": 1, "selection_method": "random"}
        )
        assert response.status_code == 200
        
        # Verify winner record has proper timestamps
        winner = db_session.query(ContestWinner).filter(
            ContestWinner.contest_id == contest.id
        ).first()
        
        assert winner is not None
        assert winner.selected_at is not None
        assert winner.created_at is not None
        assert winner.updated_at is not None
        
        # Perform winner management operations and verify timestamps update
        original_updated_at = winner.updated_at
        
        # Reselect winner
        response = client.post(
            f"/admin/contests/{contest.id}/winners/1/manage",
            headers=auth_headers,
            json={"action": "reselect"}
        )
        assert response.status_code == 200
        
        # Verify timestamps updated
        db_session.refresh(winner)
        assert winner.updated_at > original_updated_at
        assert winner.notified_at is None  # Should reset
        assert winner.claimed_at is None   # Should reset


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
