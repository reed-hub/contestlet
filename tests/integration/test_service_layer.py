"""
Integration tests for service layer interactions
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.contest import Contest
from app.models.entry import Entry
from app.models.contest_status_audit import ContestStatusAudit
from app.services.contest_service import ContestService
from app.services.admin_service import AdminService
from app.services.notification_service import NotificationService
from app.core.contest_status import ContestStatus


class TestContestServiceIntegration:
    """Test contest service integration with other components"""
    
    def test_create_draft_contest_integration(self, db_session: Session):
        """Test draft contest creation with all dependencies"""
        # Create sponsor user
        sponsor = User(phone="+15551234567", role="sponsor", is_verified=True)
        db_session.add(sponsor)
        db_session.commit()
        
        # Create contest service
        contest_service = ContestService(db_session)
        
        contest_data = {
            "name": "Integration Test Contest",
            "description": "Contest for testing service integration",
            "location": "Test City, TS 12345",
            "start_time": datetime.utcnow() + timedelta(days=1),
            "end_time": datetime.utcnow() + timedelta(days=8),
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
        
        # Create draft contest
        contest = contest_service.create_draft_contest(contest_data, sponsor.id)
        
        # Verify contest was created correctly
        assert contest.id is not None
        assert contest.name == "Integration Test Contest"
        assert contest.status == "draft"
        assert contest.created_by_user_id == sponsor.id
        
        # Verify official rules were created
        assert contest.official_rules is not None
        assert contest.official_rules.eligibility == "Must be 18 or older"
        
        # Verify relationships work
        assert contest.creator.id == sponsor.id
        assert contest.creator.phone == "+15551234567"
    
    def test_contest_submission_workflow(self, db_session: Session):
        """Test complete contest submission workflow"""
        # Create users
        sponsor = User(phone="+15551234567", role="sponsor", is_verified=True)
        admin = User(phone="+18187958204", role="admin", is_verified=True)
        db_session.add_all([sponsor, admin])
        db_session.commit()
        
        # Create services
        contest_service = ContestService(db_session)
        admin_service = AdminService(db_session)
        
        # Create draft contest
        contest_data = {
            "name": "Submission Workflow Test",
            "description": "Testing submission workflow",
            "start_time": datetime.utcnow() + timedelta(days=1),
            "end_time": datetime.utcnow() + timedelta(days=8),
            "prize_description": "Test prize",
            "contest_type": "general",
            "entry_method": "sms",
            "winner_selection_method": "random",
            "minimum_age": 18,
            "max_entries_per_person": 1,
            "total_entry_limit": 100,
            "official_rules": {
                "eligibility": "Must be 18 or older",
                "entry_requirements": "Valid phone number required",
                "prize_details": "Prize details",
                "winner_selection": "Random selection",
                "contact_info": "contest@example.com"
            }
        }
        
        contest = contest_service.create_draft_contest(contest_data, sponsor.id)
        assert contest.status == "draft"
        
        # Submit for approval
        submitted_contest = contest_service.submit_contest_for_approval(contest.id, sponsor.id)
        assert submitted_contest.status == "awaiting_approval"
        assert submitted_contest.submitted_at is not None
        
        # Admin approves contest
        approval_data = {"approval_message": "Contest looks great!"}
        approved_contest = admin_service.approve_contest(contest.id, admin.id, approval_data)
        assert approved_contest.status == "upcoming"
        assert approved_contest.approved_at is not None
        assert approved_contest.approval_message == "Contest looks great!"
        
        # Verify audit trail
        audit_records = db_session.query(ContestStatusAudit).filter_by(contest_id=contest.id).all()
        assert len(audit_records) >= 2  # draft->awaiting_approval, awaiting_approval->upcoming
        
        # Verify final state
        final_contest = db_session.query(Contest).get(contest.id)
        assert final_contest.status == "upcoming"
        assert final_contest.approved_by_user_id == admin.id
    
    def test_contest_rejection_workflow(self, db_session: Session):
        """Test contest rejection workflow"""
        # Create users
        sponsor = User(phone="+15551234567", role="sponsor", is_verified=True)
        admin = User(phone="+18187958204", role="admin", is_verified=True)
        db_session.add_all([sponsor, admin])
        db_session.commit()
        
        # Create services
        contest_service = ContestService(db_session)
        admin_service = AdminService(db_session)
        
        # Create and submit contest
        contest_data = {
            "name": "Rejection Test Contest",
            "description": "Contest for testing rejection",
            "start_time": datetime.utcnow() + timedelta(days=1),
            "end_time": datetime.utcnow() + timedelta(days=8),
            "prize_description": "Incomplete prize description",
            "contest_type": "general",
            "entry_method": "sms",
            "winner_selection_method": "random",
            "minimum_age": 18,
            "max_entries_per_person": 1,
            "total_entry_limit": 100,
            "official_rules": {
                "eligibility": "Incomplete eligibility",
                "entry_requirements": "Incomplete requirements",
                "prize_details": "Incomplete details",
                "winner_selection": "Random selection",
                "contact_info": "contest@example.com"
            }
        }
        
        contest = contest_service.create_draft_contest(contest_data, sponsor.id)
        contest = contest_service.submit_contest_for_approval(contest.id, sponsor.id)
        
        # Admin rejects contest
        rejection_data = {
            "rejection_reason": "Prize description needs more details and terms & conditions."
        }
        rejected_contest = admin_service.reject_contest(contest.id, admin.id, rejection_data)
        
        assert rejected_contest.status == "rejected"
        assert rejected_contest.rejected_at is not None
        assert rejected_contest.rejection_reason == "Prize description needs more details and terms & conditions."
        
        # Sponsor can now edit and resubmit
        updated_data = {
            "prize_description": "Updated prize description with full terms and conditions"
        }
        updated_contest = contest_service.update_draft_contest(contest.id, updated_data, sponsor.id)
        assert updated_contest.prize_description == "Updated prize description with full terms and conditions"
        
        # Resubmit for approval
        resubmitted_contest = contest_service.submit_contest_for_approval(contest.id, sponsor.id)
        assert resubmitted_contest.status == "awaiting_approval"
    
    def test_contest_lifecycle_management(self, db_session: Session):
        """Test complete contest lifecycle management"""
        # Create users
        sponsor = User(phone="+15551234567", role="sponsor", is_verified=True)
        admin = User(phone="+18187958204", role="admin", is_verified=True)
        user = User(phone="+15559876543", role="user", is_verified=True)
        db_session.add_all([sponsor, admin, user])
        db_session.commit()
        
        # Create services
        contest_service = ContestService(db_session)
        admin_service = AdminService(db_session)
        
        # Create contest that starts soon
        contest_data = {
            "name": "Lifecycle Test Contest",
            "description": "Contest for testing full lifecycle",
            "start_time": datetime.utcnow() + timedelta(minutes=30),  # Starts in 30 minutes
            "end_time": datetime.utcnow() + timedelta(days=1),
            "prize_description": "Lifecycle test prize",
            "contest_type": "general",
            "entry_method": "sms",
            "winner_selection_method": "random",
            "minimum_age": 18,
            "max_entries_per_person": 1,
            "total_entry_limit": 100,
            "official_rules": {
                "eligibility": "Must be 18 or older",
                "entry_requirements": "Valid phone number required",
                "prize_details": "Prize details",
                "winner_selection": "Random selection",
                "contact_info": "contest@example.com"
            }
        }
        
        # Create, submit, and approve contest
        contest = contest_service.create_draft_contest(contest_data, sponsor.id)
        contest = contest_service.submit_contest_for_approval(contest.id, sponsor.id)
        contest = admin_service.approve_contest(contest.id, admin.id, {"approval_message": "Approved"})
        
        assert contest.status == "upcoming"
        
        # Simulate contest becoming active (time-based)
        contest.start_time = datetime.utcnow() - timedelta(minutes=30)  # Started 30 minutes ago
        db_session.commit()
        
        from app.core.contest_status import calculate_contest_status
        calculated_status = calculate_contest_status(contest)
        assert calculated_status == "active"
        
        # Add entry to contest
        entry = Entry(contest_id=contest.id, user_id=user.id, is_valid=True)
        db_session.add(entry)
        db_session.commit()
        
        # Simulate contest ending
        contest.end_time = datetime.utcnow() - timedelta(minutes=30)  # Ended 30 minutes ago
        db_session.commit()
        
        calculated_status = calculate_contest_status(contest)
        assert calculated_status == "ended"
        
        # Admin selects winner
        contest.winner_entry_id = entry.id
        contest.status = "complete"
        db_session.commit()
        
        # Verify final state
        final_contest = db_session.query(Contest).get(contest.id)
        assert final_contest.status == "complete"
        assert final_contest.winner_entry_id == entry.id
    
    def test_bulk_contest_operations(self, db_session: Session):
        """Test bulk contest operations"""
        # Create users
        admin = User(phone="+18187958204", role="admin", is_verified=True)
        sponsor = User(phone="+15551234567", role="sponsor", is_verified=True)
        db_session.add_all([admin, sponsor])
        db_session.commit()
        
        # Create services
        contest_service = ContestService(db_session)
        admin_service = AdminService(db_session)
        
        # Create multiple contests awaiting approval
        contests = []
        for i in range(5):
            contest_data = {
                "name": f"Bulk Test Contest {i+1}",
                "description": f"Contest {i+1} for bulk testing",
                "start_time": datetime.utcnow() + timedelta(days=1),
                "end_time": datetime.utcnow() + timedelta(days=8),
                "prize_description": f"Prize {i+1}",
                "contest_type": "general",
                "entry_method": "sms",
                "winner_selection_method": "random",
                "minimum_age": 18,
                "max_entries_per_person": 1,
                "total_entry_limit": 100,
                "official_rules": {
                    "eligibility": "Must be 18 or older",
                    "entry_requirements": "Valid phone number required",
                    "prize_details": "Prize details",
                    "winner_selection": "Random selection",
                    "contact_info": "contest@example.com"
                }
            }
            
            contest = contest_service.create_draft_contest(contest_data, sponsor.id)
            contest = contest_service.submit_contest_for_approval(contest.id, sponsor.id)
            contests.append(contest)
        
        # Bulk approve contests
        contest_ids = [c.id for c in contests]
        bulk_data = {
            "contest_ids": contest_ids,
            "action": "approve",
            "message": "Bulk approved for testing"
        }
        
        results = admin_service.bulk_approve_contests(bulk_data, admin.id)
        
        assert results["success"] is True
        assert results["processed_count"] == 5
        assert len(results["results"]) == 5
        
        # Verify all contests are now upcoming
        for contest_id in contest_ids:
            contest = db_session.query(Contest).get(contest_id)
            assert contest.status == "upcoming"
            assert contest.approved_by_user_id == admin.id


class TestNotificationServiceIntegration:
    """Test notification service integration"""
    
    def test_contest_approval_notification(self, db_session: Session):
        """Test notification when contest is approved"""
        # Create users
        sponsor = User(phone="+15551234567", role="sponsor", is_verified=True)
        admin = User(phone="+18187958204", role="admin", is_verified=True)
        db_session.add_all([sponsor, admin])
        db_session.commit()
        
        # Create services
        contest_service = ContestService(db_session)
        admin_service = AdminService(db_session)
        notification_service = NotificationService(db_session)
        
        # Create and submit contest
        contest_data = {
            "name": "Notification Test Contest",
            "description": "Contest for testing notifications",
            "start_time": datetime.utcnow() + timedelta(days=1),
            "end_time": datetime.utcnow() + timedelta(days=8),
            "prize_description": "Test prize",
            "contest_type": "general",
            "entry_method": "sms",
            "winner_selection_method": "random",
            "minimum_age": 18,
            "max_entries_per_person": 1,
            "total_entry_limit": 100,
            "official_rules": {
                "eligibility": "Must be 18 or older",
                "entry_requirements": "Valid phone number required",
                "prize_details": "Prize details",
                "winner_selection": "Random selection",
                "contact_info": "contest@example.com"
            }
        }
        
        contest = contest_service.create_draft_contest(contest_data, sponsor.id)
        contest = contest_service.submit_contest_for_approval(contest.id, sponsor.id)
        
        # Approve contest (should trigger notification)
        approval_data = {"approval_message": "Your contest has been approved!"}
        approved_contest = admin_service.approve_contest(contest.id, admin.id, approval_data)
        
        # In a real scenario, this would send an SMS notification
        # For testing, we verify the notification would be sent
        notification_data = {
            "user_phone": sponsor.phone,
            "contest_id": contest.id,
            "contest_name": contest.name,
            "notification_type": "contest_approved",
            "message": f"Your contest '{contest.name}' has been approved and is now live!"
        }
        
        # Simulate sending notification
        result = notification_service.send_contest_notification(notification_data)
        
        # In mock mode, this should succeed
        assert result is not None
    
    def test_contest_rejection_notification(self, db_session: Session):
        """Test notification when contest is rejected"""
        # Create users
        sponsor = User(phone="+15551234567", role="sponsor", is_verified=True)
        admin = User(phone="+18187958204", role="admin", is_verified=True)
        db_session.add_all([sponsor, admin])
        db_session.commit()
        
        # Create services
        contest_service = ContestService(db_session)
        admin_service = AdminService(db_session)
        notification_service = NotificationService(db_session)
        
        # Create and submit contest
        contest_data = {
            "name": "Rejection Notification Test",
            "description": "Contest for testing rejection notifications",
            "start_time": datetime.utcnow() + timedelta(days=1),
            "end_time": datetime.utcnow() + timedelta(days=8),
            "prize_description": "Test prize",
            "contest_type": "general",
            "entry_method": "sms",
            "winner_selection_method": "random",
            "minimum_age": 18,
            "max_entries_per_person": 1,
            "total_entry_limit": 100,
            "official_rules": {
                "eligibility": "Must be 18 or older",
                "entry_requirements": "Valid phone number required",
                "prize_details": "Prize details",
                "winner_selection": "Random selection",
                "contact_info": "contest@example.com"
            }
        }
        
        contest = contest_service.create_draft_contest(contest_data, sponsor.id)
        contest = contest_service.submit_contest_for_approval(contest.id, sponsor.id)
        
        # Reject contest (should trigger notification)
        rejection_data = {
            "rejection_reason": "Prize description needs more details."
        }
        rejected_contest = admin_service.reject_contest(contest.id, admin.id, rejection_data)
        
        # Simulate rejection notification
        notification_data = {
            "user_phone": sponsor.phone,
            "contest_id": contest.id,
            "contest_name": contest.name,
            "notification_type": "contest_rejected",
            "message": f"Your contest '{contest.name}' needs revisions: {rejection_data['rejection_reason']}"
        }
        
        result = notification_service.send_contest_notification(notification_data)
        assert result is not None


class TestAdminServiceIntegration:
    """Test admin service integration with other components"""
    
    def test_admin_dashboard_data_aggregation(self, db_session: Session):
        """Test admin dashboard data aggregation"""
        # Create users
        admin = User(phone="+18187958204", role="admin", is_verified=True)
        sponsor1 = User(phone="+15551234567", role="sponsor", is_verified=True)
        sponsor2 = User(phone="+15552345678", role="sponsor", is_verified=True)
        user1 = User(phone="+15559876543", role="user", is_verified=True)
        user2 = User(phone="+15558765432", role="user", is_verified=True)
        db_session.add_all([admin, sponsor1, sponsor2, user1, user2])
        db_session.commit()
        
        # Create contests in different statuses
        contest_statuses = ["draft", "awaiting_approval", "upcoming", "active", "ended", "complete"]
        contests = []
        
        for i, status in enumerate(contest_statuses):
            contest = Contest(
                name=f"Dashboard Test Contest {i+1}",
                description=f"Contest {i+1} for dashboard testing",
                status=status,
                start_time=datetime.utcnow() + timedelta(days=1),
                end_time=datetime.utcnow() + timedelta(days=8),
                created_by_user_id=sponsor1.id if i % 2 == 0 else sponsor2.id,
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
        
        # Create entries for some contests
        for contest in contests[:3]:  # Add entries to first 3 contests
            entry1 = Entry(contest_id=contest.id, user_id=user1.id, is_valid=True)
            entry2 = Entry(contest_id=contest.id, user_id=user2.id, is_valid=True)
            db_session.add_all([entry1, entry2])
        
        db_session.commit()
        
        # Create admin service and get dashboard data
        admin_service = AdminService(db_session)
        dashboard_data = admin_service.get_dashboard_statistics()
        
        # Verify aggregated data
        assert dashboard_data["total_contests"] >= 6
        assert dashboard_data["total_users"] >= 5  # 2 sponsors + 2 users + 1 admin
        assert dashboard_data["total_entries"] >= 6  # 2 entries per first 3 contests
        
        # Verify status breakdown
        status_counts = dashboard_data["contest_status_breakdown"]
        for status in contest_statuses:
            assert status in status_counts
            assert status_counts[status] >= 1
    
    def test_admin_approval_queue_management(self, db_session: Session):
        """Test admin approval queue management"""
        # Create users
        admin = User(phone="+18187958204", role="admin", is_verified=True)
        sponsor = User(phone="+15551234567", role="sponsor", is_verified=True)
        db_session.add_all([admin, sponsor])
        db_session.commit()
        
        # Create services
        contest_service = ContestService(db_session)
        admin_service = AdminService(db_session)
        
        # Create contests in different statuses
        contest_data_template = {
            "description": "Contest for approval queue testing",
            "start_time": datetime.utcnow() + timedelta(days=1),
            "end_time": datetime.utcnow() + timedelta(days=8),
            "prize_description": "Test prize",
            "contest_type": "general",
            "entry_method": "sms",
            "winner_selection_method": "random",
            "minimum_age": 18,
            "max_entries_per_person": 1,
            "total_entry_limit": 100,
            "official_rules": {
                "eligibility": "Must be 18 or older",
                "entry_requirements": "Valid phone number required",
                "prize_details": "Prize details",
                "winner_selection": "Random selection",
                "contact_info": "contest@example.com"
            }
        }
        
        # Create contests awaiting approval
        awaiting_contests = []
        for i in range(3):
            contest_data = {**contest_data_template, "name": f"Awaiting Contest {i+1}"}
            contest = contest_service.create_draft_contest(contest_data, sponsor.id)
            contest = contest_service.submit_contest_for_approval(contest.id, sponsor.id)
            awaiting_contests.append(contest)
        
        # Create some approved contests
        approved_contests = []
        for i in range(2):
            contest_data = {**contest_data_template, "name": f"Approved Contest {i+1}"}
            contest = contest_service.create_draft_contest(contest_data, sponsor.id)
            contest = contest_service.submit_contest_for_approval(contest.id, sponsor.id)
            contest = admin_service.approve_contest(contest.id, admin.id, {"approval_message": "Approved"})
            approved_contests.append(contest)
        
        # Get approval queue
        approval_queue = admin_service.get_approval_queue()
        
        # Should only contain awaiting approval contests
        assert len(approval_queue["contests"]) == 3
        for contest in approval_queue["contests"]:
            assert contest["status"] == "awaiting_approval"
        
        # Get approval statistics
        stats = admin_service.get_approval_statistics()
        assert stats["total_pending"] == 3
        assert stats["total_approved_today"] >= 2
    
    def test_admin_user_management(self, db_session: Session):
        """Test admin user management functionality"""
        # Create users
        admin = User(phone="+18187958204", role="admin", is_verified=True)
        sponsor = User(phone="+15551234567", role="sponsor", is_verified=True, company_name="Test Company")
        user = User(phone="+15559876543", role="user", is_verified=True, first_name="Test", last_name="User")
        unverified_user = User(phone="+15558765432", role="user", is_verified=False)
        db_session.add_all([admin, sponsor, user, unverified_user])
        db_session.commit()
        
        # Create admin service
        admin_service = AdminService(db_session)
        
        # Get all users
        all_users = admin_service.get_all_users()
        assert len(all_users) >= 4
        
        # Verify user data structure
        user_phones = [u["phone"] for u in all_users]
        assert "+18187958204" in user_phones  # admin
        assert "+15551234567" in user_phones  # sponsor
        assert "+15559876543" in user_phones  # user
        assert "+15558765432" in user_phones  # unverified user
        
        # Get users by role
        sponsors = admin_service.get_users_by_role("sponsor")
        assert len(sponsors) >= 1
        assert sponsors[0]["phone"] == "+15551234567"
        assert sponsors[0]["company_name"] == "Test Company"
        
        # Get user statistics
        user_stats = admin_service.get_user_statistics()
        assert user_stats["total_users"] >= 4
        assert user_stats["verified_users"] >= 3
        assert user_stats["unverified_users"] >= 1
        
        # Verify role breakdown
        role_breakdown = user_stats["role_breakdown"]
        assert role_breakdown["admin"] >= 1
        assert role_breakdown["sponsor"] >= 1
        assert role_breakdown["user"] >= 2


class TestServiceLayerErrorHandling:
    """Test error handling across service layer"""
    
    def test_contest_service_error_handling(self, db_session: Session):
        """Test contest service error handling"""
        contest_service = ContestService(db_session)
        
        # Test creating contest with non-existent user
        contest_data = {
            "name": "Error Test Contest",
            "description": "Contest for testing error handling",
            "start_time": datetime.utcnow() + timedelta(days=1),
            "end_time": datetime.utcnow() + timedelta(days=8),
            "prize_description": "Test prize",
            "contest_type": "general",
            "entry_method": "sms",
            "winner_selection_method": "random",
            "minimum_age": 18,
            "max_entries_per_person": 1,
            "total_entry_limit": 100,
            "official_rules": {
                "eligibility": "Must be 18 or older",
                "entry_requirements": "Valid phone number required",
                "prize_details": "Prize details",
                "winner_selection": "Random selection",
                "contact_info": "contest@example.com"
            }
        }
        
        # Should raise error for non-existent user
        with pytest.raises(Exception):
            contest_service.create_draft_contest(contest_data, 99999)  # Non-existent user ID
        
        # Test submitting non-existent contest
        with pytest.raises(Exception):
            contest_service.submit_contest_for_approval(99999, 1)  # Non-existent contest ID
    
    def test_admin_service_error_handling(self, db_session: Session):
        """Test admin service error handling"""
        admin_service = AdminService(db_session)
        
        # Test approving non-existent contest
        with pytest.raises(Exception):
            admin_service.approve_contest(99999, 1, {"approval_message": "Test"})
        
        # Test bulk operations with invalid data
        bulk_data = {
            "contest_ids": [99999, 99998],  # Non-existent contests
            "action": "approve",
            "message": "Test bulk approval"
        }
        
        # Should handle errors gracefully
        results = admin_service.bulk_approve_contests(bulk_data, 1)
        assert results["success"] is False or results["processed_count"] == 0
    
    def test_service_transaction_rollback(self, db_session: Session):
        """Test service transaction rollback on errors"""
        # Create sponsor user
        sponsor = User(phone="+15551234567", role="sponsor", is_verified=True)
        db_session.add(sponsor)
        db_session.commit()
        
        contest_service = ContestService(db_session)
        
        # Create contest data with invalid official rules structure
        contest_data = {
            "name": "Transaction Test Contest",
            "description": "Contest for testing transaction rollback",
            "start_time": datetime.utcnow() + timedelta(days=1),
            "end_time": datetime.utcnow() + timedelta(days=8),
            "prize_description": "Test prize",
            "contest_type": "general",
            "entry_method": "sms",
            "winner_selection_method": "random",
            "minimum_age": 18,
            "max_entries_per_person": 1,
            "total_entry_limit": 100,
            "official_rules": "invalid_structure"  # Should be dict, not string
        }
        
        # Count contests before operation
        initial_count = db_session.query(Contest).count()
        
        # Attempt to create contest (should fail)
        try:
            contest_service.create_draft_contest(contest_data, sponsor.id)
        except Exception:
            pass  # Expected to fail
        
        # Verify no partial data was saved (transaction rolled back)
        final_count = db_session.query(Contest).count()
        assert final_count == initial_count, "Transaction should have been rolled back"


class TestServiceLayerPerformance:
    """Test service layer performance characteristics"""
    
    def test_bulk_operations_performance(self, db_session: Session):
        """Test performance of bulk operations"""
        import time
        
        # Create users
        admin = User(phone="+18187958204", role="admin", is_verified=True)
        sponsor = User(phone="+15551234567", role="sponsor", is_verified=True)
        db_session.add_all([admin, sponsor])
        db_session.commit()
        
        # Create services
        contest_service = ContestService(db_session)
        admin_service = AdminService(db_session)
        
        # Create multiple contests
        contest_ids = []
        start_time = time.time()
        
        for i in range(20):  # Create 20 contests
            contest_data = {
                "name": f"Performance Test Contest {i+1}",
                "description": f"Contest {i+1} for performance testing",
                "start_time": datetime.utcnow() + timedelta(days=1),
                "end_time": datetime.utcnow() + timedelta(days=8),
                "prize_description": "Test prize",
                "contest_type": "general",
                "entry_method": "sms",
                "winner_selection_method": "random",
                "minimum_age": 18,
                "max_entries_per_person": 1,
                "total_entry_limit": 100,
                "official_rules": {
                    "eligibility": "Must be 18 or older",
                    "entry_requirements": "Valid phone number required",
                    "prize_details": "Prize details",
                    "winner_selection": "Random selection",
                    "contact_info": "contest@example.com"
                }
            }
            
            contest = contest_service.create_draft_contest(contest_data, sponsor.id)
            contest = contest_service.submit_contest_for_approval(contest.id, sponsor.id)
            contest_ids.append(contest.id)
        
        creation_time = time.time() - start_time
        
        # Bulk approve contests
        start_time = time.time()
        bulk_data = {
            "contest_ids": contest_ids,
            "action": "approve",
            "message": "Bulk approved for performance testing"
        }
        
        results = admin_service.bulk_approve_contests(bulk_data, admin.id)
        bulk_approval_time = time.time() - start_time
        
        # Performance assertions
        assert creation_time < 10.0, f"Creating 20 contests took {creation_time:.2f}s, expected < 10s"
        assert bulk_approval_time < 5.0, f"Bulk approving 20 contests took {bulk_approval_time:.2f}s, expected < 5s"
        assert results["processed_count"] == 20
    
    def test_database_query_optimization(self, db_session: Session):
        """Test database query optimization in services"""
        import time
        
        # Create test data
        admin = User(phone="+18187958204", role="admin", is_verified=True)
        db_session.add(admin)
        db_session.commit()
        
        # Create many contests
        contests = []
        for i in range(100):
            contest = Contest(
                name=f"Query Optimization Test {i+1}",
                description=f"Contest {i+1} for query optimization testing",
                status="upcoming",
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
        
        # Test admin service query performance
        admin_service = AdminService(db_session)
        
        start_time = time.time()
        all_contests = admin_service.get_all_contests()
        query_time = time.time() - start_time
        
        # Should handle 100 contests quickly
        assert query_time < 1.0, f"Querying 100 contests took {query_time:.3f}s, expected < 1s"
        assert len(all_contests) >= 100
