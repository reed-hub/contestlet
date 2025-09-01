"""
Comprehensive tests for Enhanced Contest Status System
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.contest import Contest
from app.models.contest_status_audit import ContestStatusAudit
from app.core.contest_status import ContestStatus, calculate_contest_status, can_delete_contest


class TestEnhancedContestStatusSystem:
    """Test Enhanced Contest Status System functionality"""
    
    def test_contest_status_enum_values(self):
        """Test that all status enum values are defined correctly"""
        expected_statuses = [
            "draft", "awaiting_approval", "rejected", 
            "upcoming", "active", "ended", "complete", "cancelled"
        ]
        
        for status in expected_statuses:
            assert hasattr(ContestStatus, status.upper())
            assert getattr(ContestStatus, status.upper()) == status
    
    def test_draft_contest_creation(self, client: TestClient, db_session: Session, sponsor_headers: dict):
        """Test draft contest creation"""
        # Create sponsor user
        sponsor = User(phone="+15551234567", role="sponsor", is_verified=True)
        db_session.add(sponsor)
        db_session.commit()
        
        contest_data = {
            "name": "Draft Contest",
            "description": "A draft contest for testing",
            "location": "Test City, TS 12345",
            "start_time": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            "end_time": (datetime.utcnow() + timedelta(days=8)).isoformat(),
            "prize_description": "Test prize worth $100",
            "contest_type": "general",
            "entry_method": "sms",
            "winner_selection_method": "random",
            "minimum_age": 18,
            "max_entries_per_person": 1,
            "total_entry_limit": 100,
            "official_rules": {
                "eligibility": "Must be 18 or older",
                "entry_requirements": "Valid phone number required",
                "prize_details": "Prize worth $100",
                "winner_selection": "Random selection",
                "contact_info": "contest@example.com"
            }
        }
        
        response = client.post("/sponsor/workflow/contests/draft", json=contest_data, headers=sponsor_headers)
        assert response.status_code == 201
        
        data = response.json()
        assert data["status"] == "draft"
        assert data["name"] == "Draft Contest"
        assert data["is_draft"] is True
        assert data["is_published"] is False
    
    def test_submit_contest_for_approval(self, client: TestClient, db_session: Session, sponsor_headers: dict):
        """Test submitting contest for approval"""
        # Create sponsor and draft contest
        sponsor = User(phone="+15551234567", role="sponsor", is_verified=True)
        db_session.add(sponsor)
        db_session.commit()
        
        contest = Contest(
            name="Draft Contest",
            description="Contest to be submitted",
            status="draft",
            start_time=datetime.utcnow() + timedelta(days=1),
            end_time=datetime.utcnow() + timedelta(days=8),
            created_by_user_id=sponsor.id,
            prize_description="Test prize",
            contest_type="general",
            entry_method="sms",
            winner_selection_method="random",
            minimum_age=18,
            max_entries_per_person=1,
            total_entry_limit=100
        )
        db_session.add(contest)
        db_session.commit()
        
        response = client.post(f"/sponsor/workflow/contests/{contest.id}/submit", headers=sponsor_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "awaiting_approval"
        assert data["is_awaiting_approval"] is True
        assert data["submitted_at"] is not None
    
    def test_admin_approve_contest(self, client: TestClient, db_session: Session, auth_headers: dict):
        """Test admin approving contest"""
        # Create admin and sponsor users
        admin = User(phone="+18187958204", role="admin", is_verified=True)
        sponsor = User(phone="+15551234567", role="sponsor", is_verified=True)
        db_session.add_all([admin, sponsor])
        db_session.commit()
        
        # Create contest awaiting approval
        contest = Contest(
            name="Awaiting Approval Contest",
            description="Contest awaiting approval",
            status="awaiting_approval",
            start_time=datetime.utcnow() + timedelta(days=1),
            end_time=datetime.utcnow() + timedelta(days=8),
            created_by_user_id=sponsor.id,
            submitted_at=datetime.utcnow(),
            prize_description="Test prize",
            contest_type="general",
            entry_method="sms",
            winner_selection_method="random",
            minimum_age=18,
            max_entries_per_person=1,
            total_entry_limit=100
        )
        db_session.add(contest)
        db_session.commit()
        
        approval_data = {
            "approval_message": "Contest looks great! Approved for publication."
        }
        
        response = client.post(f"/admin/approval/contests/{contest.id}/approve", 
                             json=approval_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "upcoming"
        assert data["is_published"] is True
        assert data["approved_at"] is not None
        assert data["approval_message"] == "Contest looks great! Approved for publication."
    
    def test_admin_reject_contest(self, client: TestClient, db_session: Session, auth_headers: dict):
        """Test admin rejecting contest"""
        # Create admin and sponsor users
        admin = User(phone="+18187958204", role="admin", is_verified=True)
        sponsor = User(phone="+15551234567", role="sponsor", is_verified=True)
        db_session.add_all([admin, sponsor])
        db_session.commit()
        
        # Create contest awaiting approval
        contest = Contest(
            name="Contest to Reject",
            description="Contest that will be rejected",
            status="awaiting_approval",
            start_time=datetime.utcnow() + timedelta(days=1),
            end_time=datetime.utcnow() + timedelta(days=8),
            created_by_user_id=sponsor.id,
            submitted_at=datetime.utcnow(),
            prize_description="Test prize",
            contest_type="general",
            entry_method="sms",
            winner_selection_method="random",
            minimum_age=18,
            max_entries_per_person=1,
            total_entry_limit=100
        )
        db_session.add(contest)
        db_session.commit()
        
        rejection_data = {
            "rejection_reason": "Prize description needs more details. Please provide specific terms and conditions."
        }
        
        response = client.post(f"/admin/approval/contests/{contest.id}/reject", 
                             json=rejection_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "rejected"
        assert data["is_rejected"] is True
        assert data["rejected_at"] is not None
        assert data["rejection_reason"] == "Prize description needs more details. Please provide specific terms and conditions."
    
    def test_contest_lifecycle_transitions(self, client: TestClient, db_session: Session):
        """Test contest lifecycle status transitions"""
        # Create contest in upcoming status
        contest = Contest(
            name="Lifecycle Test Contest",
            description="Contest for testing lifecycle",
            status="upcoming",
            start_time=datetime.utcnow() - timedelta(minutes=30),  # Started 30 minutes ago
            end_time=datetime.utcnow() + timedelta(days=7),
            prize_description="Test prize",
            contest_type="general",
            entry_method="sms",
            winner_selection_method="random",
            minimum_age=18,
            max_entries_per_person=1,
            total_entry_limit=100
        )
        db_session.add(contest)
        db_session.commit()
        
        # Test that contest is now active (based on time)
        calculated_status = calculate_contest_status(contest)
        assert calculated_status == "active"
        
        # Test ended contest
        contest.end_time = datetime.utcnow() - timedelta(hours=1)  # Ended 1 hour ago
        db_session.commit()
        
        calculated_status = calculate_contest_status(contest)
        assert calculated_status == "ended"
    
    def test_contest_deletion_rules(self, client: TestClient, db_session: Session):
        """Test contest deletion rules based on status"""
        # Test cases for deletion rules
        test_cases = [
            ("draft", True, "Draft contests can be deleted"),
            ("awaiting_approval", True, "Awaiting approval contests can be deleted"),
            ("rejected", True, "Rejected contests can be deleted"),
            ("upcoming", True, "Upcoming contests with no entries can be deleted"),
            ("active", False, "Active contests cannot be deleted"),
            ("ended", True, "Ended contests with no entries can be deleted"),
            ("complete", False, "Complete contests cannot be deleted"),
            ("cancelled", True, "Cancelled contests can be deleted")
        ]
        
        for status, can_delete, description in test_cases:
            contest = Contest(
                name=f"Test Contest - {status}",
                description=description,
                status=status,
                start_time=datetime.utcnow() + timedelta(days=1),
                end_time=datetime.utcnow() + timedelta(days=8),
                prize_description="Test prize",
                contest_type="general",
                entry_method="sms",
                winner_selection_method="random",
                minimum_age=18,
                max_entries_per_person=1,
                total_entry_limit=100
            )
            db_session.add(contest)
            db_session.commit()
            
            result = can_delete_contest(contest)
            assert result == can_delete, f"Expected {can_delete} for {status} contest, got {result}"
            
            db_session.delete(contest)
            db_session.commit()
    
    def test_status_audit_trail(self, client: TestClient, db_session: Session, auth_headers: dict):
        """Test status change audit trail"""
        # Create admin user
        admin = User(phone="+18187958204", role="admin", is_verified=True)
        db_session.add(admin)
        db_session.commit()
        
        # Create contest
        contest = Contest(
            name="Audit Trail Contest",
            description="Contest for testing audit trail",
            status="awaiting_approval",
            start_time=datetime.utcnow() + timedelta(days=1),
            end_time=datetime.utcnow() + timedelta(days=8),
            submitted_at=datetime.utcnow(),
            prize_description="Test prize",
            contest_type="general",
            entry_method="sms",
            winner_selection_method="random",
            minimum_age=18,
            max_entries_per_person=1,
            total_entry_limit=100
        )
        db_session.add(contest)
        db_session.commit()
        
        # Approve contest (should create audit record)
        approval_data = {"approval_message": "Approved for testing audit trail"}
        response = client.post(f"/admin/approval/contests/{contest.id}/approve", 
                             json=approval_data, headers=auth_headers)
        assert response.status_code == 200
        
        # Check audit trail
        audit_records = db_session.query(ContestStatusAudit).filter_by(contest_id=contest.id).all()
        assert len(audit_records) >= 1
        
        latest_audit = audit_records[-1]
        assert latest_audit.old_status == "awaiting_approval"
        assert latest_audit.new_status == "upcoming"
        assert latest_audit.changed_by_user_id == admin.id
        assert latest_audit.reason == "Approved for testing audit trail"
    
    def test_bulk_approval_operations(self, client: TestClient, db_session: Session, auth_headers: dict):
        """Test bulk approval operations"""
        # Create admin and sponsor users
        admin = User(phone="+18187958204", role="admin", is_verified=True)
        sponsor = User(phone="+15551234567", role="sponsor", is_verified=True)
        db_session.add_all([admin, sponsor])
        db_session.commit()
        
        # Create multiple contests awaiting approval
        contests = []
        for i in range(3):
            contest = Contest(
                name=f"Bulk Test Contest {i+1}",
                description=f"Contest {i+1} for bulk testing",
                status="awaiting_approval",
                start_time=datetime.utcnow() + timedelta(days=1),
                end_time=datetime.utcnow() + timedelta(days=8),
                created_by_user_id=sponsor.id,
                submitted_at=datetime.utcnow(),
                prize_description="Test prize",
                contest_type="general",
                entry_method="sms",
                winner_selection_method="random",
                minimum_age=18,
                max_entries_per_person=1,
                total_entry_limit=100
            )
            contests.append(contest)
        
        db_session.add_all(contests)
        db_session.commit()
        
        # Bulk approve contests
        bulk_data = {
            "contest_ids": [c.id for c in contests],
            "action": "approve",
            "message": "Bulk approved for testing"
        }
        
        response = client.post("/admin/approval/contests/bulk-approve", 
                             json=bulk_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["processed_count"] == 3
        assert len(data["results"]) == 3
        
        # Verify all contests are now upcoming
        for contest in contests:
            db_session.refresh(contest)
            assert contest.status == "upcoming"
    
    def test_approval_queue_filtering(self, client: TestClient, db_session: Session, auth_headers: dict):
        """Test approval queue filtering and pagination"""
        # Create admin and sponsor users
        admin = User(phone="+18187958204", role="admin", is_verified=True)
        sponsor = User(phone="+15551234567", role="sponsor", is_verified=True)
        db_session.add_all([admin, sponsor])
        db_session.commit()
        
        # Create contests in different statuses
        statuses = ["draft", "awaiting_approval", "awaiting_approval", "rejected", "upcoming"]
        contests = []
        
        for i, status in enumerate(statuses):
            contest = Contest(
                name=f"Filter Test Contest {i+1}",
                description=f"Contest {i+1} for filter testing",
                status=status,
                start_time=datetime.utcnow() + timedelta(days=1),
                end_time=datetime.utcnow() + timedelta(days=8),
                created_by_user_id=sponsor.id,
                prize_description="Test prize",
                contest_type="general",
                entry_method="sms",
                winner_selection_method="random",
                minimum_age=18,
                max_entries_per_person=1,
                total_entry_limit=100
            )
            if status == "awaiting_approval":
                contest.submitted_at = datetime.utcnow()
            contests.append(contest)
        
        db_session.add_all(contests)
        db_session.commit()
        
        # Test approval queue (should only show awaiting_approval)
        response = client.get("/admin/approval/queue", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["contests"]) == 2  # Only awaiting_approval contests
        
        for contest in data["contests"]:
            assert contest["status"] == "awaiting_approval"
    
    def test_sponsor_workflow_permissions(self, client: TestClient, db_session: Session, sponsor_headers: dict, user_headers: dict):
        """Test sponsor workflow permissions"""
        # Create sponsor and regular user
        sponsor = User(phone="+15551234567", role="sponsor", is_verified=True)
        regular_user = User(phone="+15559876543", role="user", is_verified=True)
        db_session.add_all([sponsor, regular_user])
        db_session.commit()
        
        # Create draft contest by sponsor
        contest_data = {
            "name": "Sponsor Permission Test",
            "description": "Testing sponsor permissions",
            "location": "Test City, TS 12345",
            "start_time": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            "end_time": (datetime.utcnow() + timedelta(days=8)).isoformat(),
            "prize_description": "Test prize worth $100",
            "contest_type": "general",
            "entry_method": "sms",
            "winner_selection_method": "random",
            "minimum_age": 18,
            "max_entries_per_person": 1,
            "total_entry_limit": 100,
            "official_rules": {
                "eligibility": "Must be 18 or older",
                "entry_requirements": "Valid phone number required",
                "prize_details": "Prize worth $100",
                "winner_selection": "Random selection",
                "contact_info": "contest@example.com"
            }
        }
        
        # Sponsor should be able to create draft
        response = client.post("/sponsor/workflow/contests/draft", json=contest_data, headers=sponsor_headers)
        assert response.status_code == 201
        
        # Regular user should not be able to create draft
        response = client.post("/sponsor/workflow/contests/draft", json=contest_data, headers=user_headers)
        assert response.status_code == 403
        
        # Regular user should not be able to access sponsor drafts
        response = client.get("/sponsor/workflow/contests/drafts", headers=user_headers)
        assert response.status_code == 403
    
    def test_contest_status_computed_fields(self, client: TestClient, db_session: Session):
        """Test contest status computed fields"""
        # Test all status types
        test_statuses = [
            ("draft", {"is_draft": True, "is_awaiting_approval": False, "is_rejected": False, "is_published": False}),
            ("awaiting_approval", {"is_draft": False, "is_awaiting_approval": True, "is_rejected": False, "is_published": False}),
            ("rejected", {"is_draft": False, "is_awaiting_approval": False, "is_rejected": True, "is_published": False}),
            ("upcoming", {"is_draft": False, "is_awaiting_approval": False, "is_rejected": False, "is_published": True}),
            ("active", {"is_draft": False, "is_awaiting_approval": False, "is_rejected": False, "is_published": True}),
            ("ended", {"is_draft": False, "is_awaiting_approval": False, "is_rejected": False, "is_published": True}),
            ("complete", {"is_draft": False, "is_awaiting_approval": False, "is_rejected": False, "is_published": True}),
            ("cancelled", {"is_draft": False, "is_awaiting_approval": False, "is_rejected": False, "is_published": False})
        ]
        
        for status, expected_fields in test_statuses:
            contest = Contest(
                name=f"Computed Fields Test - {status}",
                description="Testing computed fields",
                status=status,
                start_time=datetime.utcnow() + timedelta(days=1),
                end_time=datetime.utcnow() + timedelta(days=8),
                prize_description="Test prize",
                contest_type="general",
                entry_method="sms",
                winner_selection_method="random",
                minimum_age=18,
                max_entries_per_person=1,
                total_entry_limit=100
            )
            db_session.add(contest)
            db_session.commit()
            
            # Test public contest view
            response = client.get(f"/contests/{contest.id}")
            assert response.status_code == 200
            
            data = response.json()
            for field, expected_value in expected_fields.items():
                assert data[field] == expected_value, f"Expected {field}={expected_value} for {status}, got {data[field]}"
            
            db_session.delete(contest)
            db_session.commit()


class TestEnhancedStatusSystemIntegration:
    """Test Enhanced Status System integration with other features"""
    
    def test_status_system_with_entries(self, client: TestClient, db_session: Session):
        """Test status system behavior with contest entries"""
        from app.models.entry import Entry
        
        # Create user and contest
        user = User(phone="+15559876543", role="user", is_verified=True)
        db_session.add(user)
        db_session.commit()
        
        contest = Contest(
            name="Contest with Entries",
            description="Testing status with entries",
            status="active",
            start_time=datetime.utcnow() - timedelta(hours=1),
            end_time=datetime.utcnow() + timedelta(days=7),
            prize_description="Test prize",
            contest_type="general",
            entry_method="sms",
            winner_selection_method="random",
            minimum_age=18,
            max_entries_per_person=1,
            total_entry_limit=100
        )
        db_session.add(contest)
        db_session.commit()
        
        # Add entry to contest
        entry = Entry(contest_id=contest.id, user_id=user.id, is_valid=True)
        db_session.add(entry)
        db_session.commit()
        
        # Contest with entries should not be deletable
        assert can_delete_contest(contest) is False
        
        # Test deletion attempt
        response = client.delete(f"/contests/{contest.id}")
        assert response.status_code == 403
        
        data = response.json()
        assert "CONTEST_PROTECTED" in data["error"]
        assert "active_with_entries" in data["details"]["protection_reason"]
    
    def test_status_system_with_notifications(self, client: TestClient, db_session: Session, auth_headers: dict):
        """Test status system integration with notifications"""
        # Create admin and sponsor users
        admin = User(phone="+18187958204", role="admin", is_verified=True)
        sponsor = User(phone="+15551234567", role="sponsor", is_verified=True)
        db_session.add_all([admin, sponsor])
        db_session.commit()
        
        # Create contest awaiting approval
        contest = Contest(
            name="Notification Test Contest",
            description="Testing notifications with status changes",
            status="awaiting_approval",
            start_time=datetime.utcnow() + timedelta(days=1),
            end_time=datetime.utcnow() + timedelta(days=8),
            created_by_user_id=sponsor.id,
            submitted_at=datetime.utcnow(),
            prize_description="Test prize",
            contest_type="general",
            entry_method="sms",
            winner_selection_method="random",
            minimum_age=18,
            max_entries_per_person=1,
            total_entry_limit=100
        )
        db_session.add(contest)
        db_session.commit()
        
        # Approve contest (should trigger notification)
        approval_data = {"approval_message": "Contest approved!"}
        response = client.post(f"/admin/approval/contests/{contest.id}/approve", 
                             json=approval_data, headers=auth_headers)
        assert response.status_code == 200
        
        # Check that contest status changed
        db_session.refresh(contest)
        assert contest.status == "upcoming"
        assert contest.approved_at is not None
    
    def test_status_system_performance(self, client: TestClient, db_session: Session):
        """Test Enhanced Status System performance with large datasets"""
        import time
        
        # Create multiple contests in different statuses
        contests = []
        statuses = ["draft", "awaiting_approval", "rejected", "upcoming", "active", "ended", "complete", "cancelled"]
        
        for i in range(100):
            status = statuses[i % len(statuses)]
            contest = Contest(
                name=f"Performance Test Contest {i+1}",
                description=f"Contest {i+1} for performance testing",
                status=status,
                start_time=datetime.utcnow() + timedelta(days=1),
                end_time=datetime.utcnow() + timedelta(days=8),
                prize_description="Test prize",
                contest_type="general",
                entry_method="sms",
                winner_selection_method="random",
                minimum_age=18,
                max_entries_per_person=1,
                total_entry_limit=100
            )
            contests.append(contest)
        
        db_session.add_all(contests)
        db_session.commit()
        
        # Test performance of status filtering
        start_time = time.time()
        response = client.get("/contests/active")
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = end_time - start_time
        
        # Should handle 100 contests quickly (< 300ms)
        assert response_time < 0.3, f"Status filtering took {response_time:.3f}s, expected < 0.3s"
        
        data = response.json()
        # Should only return active contests
        for contest in data["contests"]:
            calculated_status = contest.get("enhanced_status", contest.get("status"))
            assert calculated_status in ["active"], f"Expected active status, got {calculated_status}"
