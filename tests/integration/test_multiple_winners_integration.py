"""
Integration Tests for Multiple Winners Feature

Tests the integration between multiple winner components including
database operations, service layer interactions, and API endpoints.
"""

import pytest
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models.user import User
from app.models.contest import Contest
from app.models.entry import Entry
from app.models.contest_winner import ContestWinner
from app.core.services.winner_service import WinnerService
from app.core.datetime_utils import utc_now


@pytest.mark.integration
class TestMultipleWinnersIntegration:
    """Integration tests for multiple winners feature"""
    
    def setup_method(self):
        """Setup test data for each test method"""
        self.base_contest_data = {
            "name": "Integration Test Contest",
            "description": "Contest for integration testing",
            "location": "Test City, TS 12345",
            "start_time": utc_now() - timedelta(days=1),
            "end_time": utc_now() - timedelta(hours=1),
            "prize_description": "Integration test prizes",
            "status": "ended",
            "contest_type": "general",
            "entry_method": "sms",
            "winner_selection_method": "random",
            "minimum_age": 18
        }
    
    def create_test_data(self, db: Session, num_users: int = 10, winner_count: int = 3):
        """Create test contest, users, and entries"""
        # Create admin user
        admin_user = User(
            phone="+18187958204",
            role="admin",
            is_verified=True
        )
        db.add(admin_user)
        db.flush()
        
        # Create contest
        contest_data = {**self.base_contest_data, "winner_count": winner_count}
        contest = Contest(**contest_data, created_by_user_id=admin_user.id)
        db.add(contest)
        db.flush()
        
        # Create users and entries
        users = []
        entries = []
        
        for i in range(num_users):
            user = User(
                phone=f"+155500{i:04d}",
                role="user",
                is_verified=True
            )
            db.add(user)
            db.flush()
            users.append(user)
            
            entry = Entry(
                user_id=user.id,
                contest_id=contest.id,
                status="active"
            )
            db.add(entry)
            entries.append(entry)
        
        db.commit()
        
        return {
            "admin_user": admin_user,
            "contest": contest,
            "users": users,
            "entries": entries
        }
    
    def test_database_schema_integration(self, db_session: Session):
        """Test that database schema supports multiple winners correctly"""
        test_data = self.create_test_data(db_session, num_users=5, winner_count=3)
        contest = test_data["contest"]
        entries = test_data["entries"]
        
        # Create winners directly in database
        winners = []
        for i in range(3):
            winner = ContestWinner(
                contest_id=contest.id,
                entry_id=entries[i].id,
                winner_position=i + 1,
                prize_description=f"Prize {i + 1}",
                selected_at=utc_now()
            )
            db_session.add(winner)
            winners.append(winner)
        
        db_session.commit()
        
        # Test database constraints and relationships
        # 1. Test unique constraints
        with pytest.raises(Exception):  # Should violate unique constraint
            duplicate_winner = ContestWinner(
                contest_id=contest.id,
                entry_id=entries[0].id,  # Same entry as first winner
                winner_position=4,
                selected_at=utc_now()
            )
            db_session.add(duplicate_winner)
            db_session.commit()
        
        db_session.rollback()
        
        # 2. Test position uniqueness
        with pytest.raises(Exception):  # Should violate position uniqueness
            duplicate_position = ContestWinner(
                contest_id=contest.id,
                entry_id=entries[3].id,
                winner_position=1,  # Same position as first winner
                selected_at=utc_now()
            )
            db_session.add(duplicate_position)
            db_session.commit()
        
        db_session.rollback()
        
        # 3. Test relationships work correctly
        db_winners = db_session.query(ContestWinner).filter(
            ContestWinner.contest_id == contest.id
        ).all()
        
        assert len(db_winners) == 3
        
        for winner in db_winners:
            assert winner.contest is not None
            assert winner.entry is not None
            assert winner.user is not None  # Through entry relationship
            assert winner.phone is not None  # Property through relationships
        
        # 4. Test cascade deletion
        contest_winners_before = db_session.query(ContestWinner).count()
        db_session.delete(contest)
        db_session.commit()
        
        contest_winners_after = db_session.query(ContestWinner).count()
        assert contest_winners_after < contest_winners_before
    
    def test_service_layer_integration(self, db_session: Session):
        """Test integration between WinnerService and database"""
        test_data = self.create_test_data(db_session, num_users=10, winner_count=5)
        contest = test_data["contest"]
        
        # Test winner selection through service
        winner_service = WinnerService(db_session)
        
        prize_tiers = [
            {"position": 1, "prize": "$500 Grand Prize"},
            {"position": 2, "prize": "$200 Second Prize"},
            {"position": 3, "prize": "$100 Third Prize"},
            {"position": 4, "prize": "$50 Fourth Prize"},
            {"position": 5, "prize": "$25 Fifth Prize"}
        ]
        
        result = winner_service.select_winners(
            contest_id=contest.id,
            winner_count=5,
            selection_method="random",
            prize_tiers=prize_tiers
        )
        
        # Verify service result
        assert result.success is True
        assert result.total_winners == 5
        assert result.total_entries == 10
        assert len(result.winners) == 5
        
        # Verify database state
        db_winners = db_session.query(ContestWinner).filter(
            ContestWinner.contest_id == contest.id
        ).order_by(ContestWinner.winner_position).all()
        
        assert len(db_winners) == 5
        
        for i, winner in enumerate(db_winners, 1):
            assert winner.winner_position == i
            assert winner.prize_description == prize_tiers[i-1]["prize"]
            assert winner.selected_at is not None
            assert winner.notified_at is None
            assert winner.claimed_at is None
        
        # Test winner management operations
        original_winner = db_winners[0]
        original_entry_id = original_winner.entry_id
        
        # Test reselection
        new_winner = winner_service.reselect_winner(contest.id, position=1)
        assert new_winner.entry_id != original_entry_id
        assert new_winner.notified_at is None
        
        # Test notification tracking
        notified_winner = winner_service.mark_winner_notified(contest.id, position=1)
        assert notified_winner.notified_at is not None
        
        # Test claim tracking
        claimed_winner = winner_service.mark_winner_claimed(contest.id, position=1)
        assert claimed_winner.claimed_at is not None
        
        # Test winner removal
        success = winner_service.remove_winner(contest.id, position=5)
        assert success is True
        
        remaining_winners = winner_service.get_contest_winners(contest.id)
        assert len(remaining_winners) == 4
    
    def test_api_database_integration(self, client: TestClient, db_session: Session, auth_headers):
        """Test integration between API endpoints and database"""
        test_data = self.create_test_data(db_session, num_users=8, winner_count=3)
        contest = test_data["contest"]
        
        # Test winner selection via API
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
        api_data = response.json()
        
        # Verify API response matches database state
        db_winners = db_session.query(ContestWinner).filter(
            ContestWinner.contest_id == contest.id
        ).order_by(ContestWinner.winner_position).all()
        
        assert len(db_winners) == len(api_data["winners"])
        
        for api_winner, db_winner in zip(api_data["winners"], db_winners):
            assert api_winner["id"] == db_winner.id
            assert api_winner["contest_id"] == db_winner.contest_id
            assert api_winner["entry_id"] == db_winner.entry_id
            assert api_winner["winner_position"] == db_winner.winner_position
            assert api_winner["prize_description"] == db_winner.prize_description
        
        # Test winner list API
        response = client.get(
            f"/admin/contests/{contest.id}/winners",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        list_data = response.json()
        
        assert list_data["contest_id"] == contest.id
        assert list_data["winner_count"] == 3
        assert list_data["selected_winners"] == 3
        assert len(list_data["winners"]) == 3
        
        # Test winner management API
        response = client.post(
            f"/admin/contests/{contest.id}/winners/1/manage",
            headers=auth_headers,
            json={"action": "notify"}
        )
        
        assert response.status_code == 200
        
        # Verify database was updated
        first_winner = db_session.query(ContestWinner).filter(
            ContestWinner.contest_id == contest.id,
            ContestWinner.winner_position == 1
        ).first()
        
        assert first_winner.notified_at is not None
    
    def test_backward_compatibility_integration(self, client: TestClient, db_session: Session, auth_headers):
        """Test that legacy single winner functionality integrates with new system"""
        test_data = self.create_test_data(db_session, num_users=5, winner_count=1)
        contest = test_data["contest"]
        
        # Use legacy single winner endpoint
        response = client.post(
            f"/admin/contests/{contest.id}/select-winner",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        legacy_data = response.json()
        
        # Verify legacy response format
        assert legacy_data["success"] is True
        assert "winner_entry_id" in legacy_data
        assert "winner_phone" in legacy_data
        
        # Verify new system was used internally
        db_winners = db_session.query(ContestWinner).filter(
            ContestWinner.contest_id == contest.id
        ).all()
        
        assert len(db_winners) == 1
        assert db_winners[0].winner_position == 1
        assert db_winners[0].entry_id == legacy_data["winner_entry_id"]
        
        # Verify legacy fields are populated
        db_session.refresh(contest)
        assert contest.winner_entry_id == legacy_data["winner_entry_id"]
        assert contest.winner_phone == legacy_data["winner_phone"]
        assert contest.winner_selected_at is not None
        
        # Verify new endpoints work with legacy-selected winner
        response = client.get(
            f"/admin/contests/{contest.id}/winners",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        new_data = response.json()
        
        assert new_data["winner_count"] == 1
        assert new_data["selected_winners"] == 1
        assert len(new_data["winners"]) == 1
        assert new_data["winners"][0]["entry_id"] == legacy_data["winner_entry_id"]
    
    def test_contest_lifecycle_integration(self, client: TestClient, db_session: Session, auth_headers):
        """Test multiple winners feature through complete contest lifecycle"""
        # Create contest with multiple winners configuration
        admin_user = User(phone="+18187958204", role="admin", is_verified=True)
        db_session.add(admin_user)
        db_session.commit()
        
        contest_data = {
            **self.base_contest_data,
            "winner_count": 4,
            "prize_tiers": json.dumps({
                "tiers": [
                    {"position": 1, "prize": "$1000 Grand Prize"},
                    {"position": 2, "prize": "$500 Second Prize"},
                    {"position": 3, "prize": "$250 Third Prize"},
                    {"position": 4, "prize": "$100 Fourth Prize"}
                ],
                "total_value": 1850,
                "currency": "USD"
            })
        }
        
        contest = Contest(**contest_data, created_by_user_id=admin_user.id)
        db_session.add(contest)
        db_session.commit()
        
        # Create entries
        for i in range(15):
            user = User(phone=f"+155500{i:04d}", role="user", is_verified=True)
            db_session.add(user)
            db_session.flush()
            
            entry = Entry(user_id=user.id, contest_id=contest.id, status="active")
            db_session.add(entry)
        
        db_session.commit()
        
        # Phase 1: Select winners
        prize_tiers = [
            {"position": 1, "prize": "$1000 Grand Prize"},
            {"position": 2, "prize": "$500 Second Prize"},
            {"position": 3, "prize": "$250 Third Prize"},
            {"position": 4, "prize": "$100 Fourth Prize"}
        ]
        
        response = client.post(
            f"/admin/contests/{contest.id}/select-winners",
            headers=auth_headers,
            json={
                "winner_count": 4,
                "selection_method": "random",
                "prize_tiers": prize_tiers
            }
        )
        
        assert response.status_code == 200
        
        # Phase 2: Notify winners
        response = client.post(
            f"/admin/contests/{contest.id}/winners/notify",
            headers=auth_headers,
            json={
                "custom_message": "Congratulations! You won {prize_description}!",
                "test_mode": True
            }
        )
        
        assert response.status_code == 200
        notify_data = response.json()
        assert notify_data["notifications_sent"] == 4
        
        # Phase 3: Track claims
        for position in [1, 3]:  # Mark positions 1 and 3 as claimed
            response = client.post(
                f"/admin/contests/{contest.id}/winners/{position}/manage",
                headers=auth_headers,
                json={"action": "mark_claimed"}
            )
            assert response.status_code == 200
        
        # Phase 4: Reselect a winner
        response = client.post(
            f"/admin/contests/{contest.id}/winners/2/manage",
            headers=auth_headers,
            json={"action": "reselect"}
        )
        
        assert response.status_code == 200
        
        # Phase 5: Get final statistics
        response = client.get(
            f"/admin/contests/{contest.id}/winners/stats",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        stats = response.json()
        
        assert stats["selected_winners"] == 4
        assert stats["notified_winners"] == 4  # All were notified initially
        assert stats["claimed_winners"] == 2   # Positions 1 and 3
        assert stats["has_prize_tiers"] is True
        
        # Verify final database state
        final_winners = db_session.query(ContestWinner).filter(
            ContestWinner.contest_id == contest.id
        ).order_by(ContestWinner.winner_position).all()
        
        assert len(final_winners) == 4
        
        # Check claim status
        claimed_positions = [w.winner_position for w in final_winners if w.claimed_at is not None]
        assert sorted(claimed_positions) == [1, 3]
        
        # Check that position 2 was reselected (notified_at should be None)
        position_2_winner = next(w for w in final_winners if w.winner_position == 2)
        assert position_2_winner.notified_at is None  # Reset after reselection
    
    def test_error_propagation_integration(self, client: TestClient, db_session: Session, auth_headers):
        """Test that errors propagate correctly through the integration layers"""
        test_data = self.create_test_data(db_session, num_users=3, winner_count=2)
        contest = test_data["contest"]
        
        # Test business logic error propagation
        # Try to select more winners than entries
        response = client.post(
            f"/admin/contests/{contest.id}/select-winners",
            headers=auth_headers,
            json={"winner_count": 10, "selection_method": "random"}
        )
        
        assert response.status_code == 400
        error_data = response.json()
        assert "Not enough eligible entries" in error_data["detail"]
        
        # Select winners first
        response = client.post(
            f"/admin/contests/{contest.id}/select-winners",
            headers=auth_headers,
            json={"winner_count": 2, "selection_method": "random"}
        )
        assert response.status_code == 200
        
        # Try to select winners again (should fail)
        response = client.post(
            f"/admin/contests/{contest.id}/select-winners",
            headers=auth_headers,
            json={"winner_count": 1, "selection_method": "random"}
        )
        
        assert response.status_code == 400
        error_data = response.json()
        assert "already has" in error_data["detail"]
        
        # Test validation error propagation
        response = client.post(
            f"/admin/contests/{contest.id}/winners/99/manage",
            headers=auth_headers,
            json={"action": "reselect"}
        )
        
        assert response.status_code == 404 or response.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
