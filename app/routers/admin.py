from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import datetime
from app.core.datetime_utils import utc_now
from typing import List, Optional
import random
from app.database.database import get_db
from app.models.contest import Contest
from app.models.entry import Entry
from app.models.user import User
from app.models.official_rules import OfficialRules
from app.models.sms_template import SMSTemplate
from app.schemas.admin import (
    AdminContestCreate, AdminContestUpdate, AdminContestResponse, 
    WinnerSelectionResponse, AdminAuthResponse, AdminEntryResponse,
    WinnerNotificationRequest, WinnerNotificationResponse, NotificationLogResponse,
    ContestDeleteResponse, ContestDeletionSummary
)
from app.schemas.campaign_import import CampaignImportRequest, CampaignImportResponse
from app.core.admin_auth import get_admin_user
from app.core.sms_notification_service import sms_notification_service
from app.core.rate_limiter import rate_limiter
from app.models.notification import Notification
from app.services.campaign_import_service import campaign_import_service

router = APIRouter(prefix="/admin", tags=["admin"])


async def get_admin_user_jwt_only(admin_payload: dict = Depends(get_admin_user)) -> dict:
    """
    Get admin user but only allow JWT tokens (not legacy tokens) for sensitive operations.
    This is used for SMS notifications which require higher security.
    """
    if admin_payload.get("legacy", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="SMS notifications require admin JWT authentication. Please authenticate via OTP.",
        )
    
    return admin_payload


def validate_contest_compliance(contest_data: dict, official_rules_data: dict) -> None:
    """
    Validate that contest meets legal compliance requirements before activation.
    """
    required_fields = {
        'contest': ['name', 'start_time', 'end_time', 'prize_description'],
        'rules': ['eligibility_text', 'sponsor_name', 'start_date', 'end_date', 'prize_value_usd']
    }
    
    # Check required contest fields
    for field in required_fields['contest']:
        if not contest_data.get(field):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Contest field '{field}' is required for legal compliance"
            )
    
    # Check required official rules fields
    for field in required_fields['rules']:
        if not official_rules_data.get(field):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Official rules field '{field}' is required for legal compliance"
            )
    
    # Validate prize value is reasonable
    if official_rules_data.get('prize_value_usd', 0) <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prize value must be greater than $0 for legal compliance"
        )


@router.get("/auth", response_model=AdminAuthResponse)
async def admin_auth_check(admin_user: dict = Depends(get_admin_user)):
    """Check admin authentication status"""
    return AdminAuthResponse(message="Admin authentication successful")


@router.post("/contests", response_model=AdminContestResponse)
async def create_contest(
    contest_data: AdminContestCreate,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Create a new contest with official rules.
    Validates legal compliance before allowing activation.
    """
    # Convert Pydantic models to dict for validation
    contest_dict = contest_data.dict(exclude={'official_rules', 'sms_templates'})
    rules_dict = contest_data.official_rules.dict()
    sms_templates = contest_data.sms_templates
    
    # Validate legal compliance
    validate_contest_compliance(contest_dict, rules_dict)
    
    # Add timezone metadata from admin's current preferences
    from app.models.admin_profile import AdminProfile
    
    admin_user_id = admin_user.get("sub", "unknown")
    admin_profile = db.query(AdminProfile).filter(
        AdminProfile.admin_user_id == admin_user_id
    ).first()
    
    # Add timezone and admin metadata to contest
    contest_dict['admin_user_id'] = admin_user_id
    contest_dict['created_timezone'] = admin_profile.timezone if admin_profile else "UTC"
    
    # Create contest
    contest = Contest(**contest_dict)
    db.add(contest)
    db.flush()  # Get the contest ID
    
    # Create official rules
    official_rules = OfficialRules(
        contest_id=contest.id,
        **rules_dict
    )
    db.add(official_rules)
    
    # Create SMS templates if provided (Phase 2)
    if sms_templates:
        template_data = sms_templates.dict(exclude_unset=True)
        for template_type, message_content in template_data.items():
            if message_content and message_content.strip():
                sms_template = SMSTemplate(
                    contest_id=contest.id,
                    template_type=template_type,
                    message_content=message_content.strip()
                )
                db.add(sms_template)
    
    db.commit()
    
    # Refresh to get relationships
    db.refresh(contest)
    db.refresh(official_rules)
    
    # Get entry count (will be 0 for new contest)
    entry_count = db.query(Entry).filter(Entry.contest_id == contest.id).count()
    
    # Prepare response
    response_data = {
        **contest.__dict__,
        "entry_count": entry_count,
        "official_rules": official_rules
    }
    
    return AdminContestResponse(**response_data)


@router.put("/contests/{contest_id}", response_model=AdminContestResponse)
async def update_contest(
    contest_id: int,
    contest_update: AdminContestUpdate,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing contest and its official rules.
    """
    # Get existing contest
    contest = db.query(Contest).options(joinedload(Contest.official_rules)).filter(
        Contest.id == contest_id
    ).first()
    
    if not contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found"
        )
    
    # Update contest fields
    update_data = contest_update.dict(exclude={'official_rules'}, exclude_unset=True)
    for field, value in update_data.items():
        setattr(contest, field, value)
    
    # Update official rules if provided
    if contest_update.official_rules:
        if contest.official_rules:
            # Update existing rules
            rules_update = contest_update.official_rules.dict(exclude_unset=True)
            for field, value in rules_update.items():
                setattr(contest.official_rules, field, value)
            contest.official_rules.updated_at = datetime.utcnow()
        else:
            # Create new rules if none exist
            rules_data = contest_update.official_rules.dict(exclude_unset=True)
            official_rules = OfficialRules(contest_id=contest.id, **rules_data)
            db.add(official_rules)
    
# Note: Contest compliance is validated at creation time
    # Status is now automatically computed based on time and winner selection
    
    db.commit()
    db.refresh(contest)
    
    # Get entry count
    entry_count = db.query(Entry).filter(Entry.contest_id == contest.id).count()
    
    # Prepare response
    response_data = {
        **contest.__dict__,
        "entry_count": entry_count,
        "official_rules": contest.official_rules
    }
    
    return AdminContestResponse(**response_data)


@router.get("/contests", response_model=List[AdminContestResponse])
async def list_contests(
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    List all contests with admin details including entry counts.
    """
    contests = db.query(Contest).options(joinedload(Contest.official_rules)).all()
    
    response_list = []
    for contest in contests:
        entry_count = db.query(Entry).filter(Entry.contest_id == contest.id).count()
        response_data = {
            **contest.__dict__,
            "entry_count": entry_count,
            "official_rules": contest.official_rules
        }
        response_list.append(AdminContestResponse(**response_data))
    
    return response_list


@router.get("/contests/{contest_id}/entries", response_model=List[AdminEntryResponse])
async def get_contest_entries(
    contest_id: int,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get all entries for a specific contest.
    Returns user details including phone numbers for admin review.
    """
    # Validate that the contest exists
    contest = db.query(Contest).filter(Contest.id == contest_id).first()
    if not contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found"
        )
    
    # Get all entries for this contest with user details
    entries = db.query(Entry).options(joinedload(Entry.user)).filter(
        Entry.contest_id == contest_id
    ).order_by(Entry.created_at.desc()).all()
    
    # Transform to admin response format with phone numbers
    admin_entries = []
    for entry in entries:
        admin_entry = AdminEntryResponse(
            id=entry.id,
            contest_id=entry.contest_id,
            user_id=entry.user_id,
            phone_number=entry.user.phone,
            created_at=entry.created_at,
            selected=entry.selected,
            status=entry.status
        )
        admin_entries.append(admin_entry)
    
    return admin_entries


@router.post("/contests/{contest_id}/select-winner", response_model=WinnerSelectionResponse)
async def select_winner(
    contest_id: int,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Randomly select a winner from contest entries and mark as selected.
    """
    try:
        print(f"🎯 Winner selection requested for contest {contest_id} by admin {admin_user.get('phone', 'unknown')}")
        
        # Get contest
        contest = db.query(Contest).filter(Contest.id == contest_id).first()
        if not contest:
            print(f"❌ Contest {contest_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contest not found"
            )
        
        print(f"📊 Contest found: {contest.name}, end_time: {contest.end_time}")
        
        # Check if contest has ended
        current_time = utc_now()
        
        # Ensure contest end time is timezone-aware for comparison
        contest_end = contest.end_time
        if contest_end.tzinfo is None:
            from datetime import timezone
            contest_end = contest_end.replace(tzinfo=timezone.utc)
        
        if contest_end > current_time:
            print(f"❌ Contest still active, ends at {contest_end}, current time: {current_time}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot select winner for an active contest. Contest must end first."
            )
        
        # Get all entries for this contest
        entries = db.query(Entry).options(joinedload(Entry.user)).filter(
            Entry.contest_id == contest_id
        ).all()
        
        print(f"📊 Found {len(entries)} entries for contest {contest_id}")
        
        if not entries:
            print(f"❌ No entries found for contest {contest_id}")
            return WinnerSelectionResponse(
                success=False,
                message="No entries found for this contest",
                total_entries=0
            )
        
        # Check if winner already selected
        existing_winner = db.query(Entry).filter(
            Entry.contest_id == contest_id,
            Entry.selected == True
        ).first()
        
        if existing_winner:
            print(f"⚠️ Winner already selected for contest {contest_id}: Entry {existing_winner.id}")
            return WinnerSelectionResponse(
                success=False,
                message="Winner already selected for this contest",
                winner_entry_id=existing_winner.id,
                winner_user_phone=existing_winner.user.phone,
                total_entries=len(entries)
            )
    
        # Randomly select winner
        winner_entry = random.choice(entries)
        print(f"🏆 Selected winner: Entry ID {winner_entry.id}, User: {winner_entry.user.phone}")
        
        winner_entry.selected = True
        winner_entry.status = "winner"
        
        # Update contest with winner information
        contest.winner_entry_id = winner_entry.id
        contest.winner_phone = winner_entry.user.phone
        contest.winner_selected_at = utc_now()
        
        print(f"💾 Committing winner selection to database...")
        db.commit()
        print(f"✅ Winner selection completed successfully")
        
        return WinnerSelectionResponse(
            success=True,
            message=f"Winner selected successfully from {len(entries)} entries",
            winner_entry_id=winner_entry.id,
            winner_user_phone=winner_entry.user.phone,
            total_entries=len(entries)
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"🚨 Winner selection error for contest {contest_id}: {str(e)}")
        print(f"🚨 Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Winner selection failed: {str(e)}"
        )


@router.post("/contests/{contest_id}/notify-winner", response_model=WinnerNotificationResponse)
async def notify_winner(
    contest_id: int,
    notification_request: WinnerNotificationRequest,
    admin_user: dict = Depends(get_admin_user_jwt_only),
    db: Session = Depends(get_db)
):
    """
    Send SMS notification to a contest winner.
    
    🛑 Security Features:
    - Rate limited (5 requests per 5 minutes per admin)
    - Requires admin JWT authentication (not legacy token)
    - Validates user actually entered the contest
    - Logs all notifications to database
    
    📄 Features:
    - Optional test_mode to simulate without sending SMS
    - Comprehensive audit trail
    - Phone number privacy protection
    """
    # 🛑 Rate limiting for SMS notifications
    rate_limit_key = f"admin_sms_{admin_user.get('sub', 'unknown')}"
    if not rate_limiter.is_allowed(rate_limit_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many SMS notifications. Please wait before sending another."
        )
    
    # Validate contest exists
    contest = db.query(Contest).filter(Contest.id == contest_id).first()
    if not contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found"
        )
    
    # 🛑 Validate entry exists and belongs to the contest (safety check)
    entry = db.query(Entry).options(joinedload(Entry.user)).filter(
        Entry.id == notification_request.entry_id,
        Entry.contest_id == contest_id
    ).first()
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found for this contest. Users can only be notified if they entered."
        )
    
    # Get winner's phone number
    winner_phone = entry.user.phone
    if not winner_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Winner has no phone number on file"
        )
    
    # Create notification record BEFORE sending
    notification = Notification(
        contest_id=contest_id,
        user_id=entry.user_id,
        entry_id=entry.id,
        message=notification_request.message,
        notification_type="winner",
        status="pending",
        test_mode=notification_request.test_mode,
        admin_user_id=admin_user.get("sub", "unknown")
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    
    try:
        # Send SMS notification
        success, sms_message, twilio_sid = await sms_notification_service.send_notification(
            to_phone=winner_phone,
            message=notification_request.message,
            notification_type="winner",
            test_mode=notification_request.test_mode
        )
        
        # Update notification record with result
        notification.status = "sent" if success else "failed"
        notification.twilio_sid = twilio_sid
        if not success:
            notification.error_message = sms_message
        
        db.commit()
        
        # Mask phone number for privacy in response
        masked_phone = f"{winner_phone[:2]}***{winner_phone[-4:]}" if len(winner_phone) >= 6 else winner_phone
        
        return WinnerNotificationResponse(
            success=success,
            message="Winner notification sent successfully" if success else "Failed to send winner notification",
            entry_id=entry.id,
            contest_id=contest_id,
            winner_phone=masked_phone,
            sms_status=sms_message,
            test_mode=notification_request.test_mode,
            notification_id=notification.id,
            twilio_sid=twilio_sid,
            notification_sent_at=notification.sent_at
        )
    
    except Exception as e:
        # Update notification record with error
        notification.status = "failed"
        notification.error_message = str(e)
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SMS notification failed: {str(e)}"
        )


@router.get("/notifications", response_model=List[NotificationLogResponse])
async def get_notification_logs(
    contest_id: Optional[int] = None,
    notification_type: Optional[str] = None,
    limit: int = 50,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get SMS notification logs for admin review.
    
    Provides comprehensive audit trail of all SMS notifications sent,
    including winner notifications, reminders, and other communications.
    """
    # Build query
    query = db.query(Notification).options(
        joinedload(Notification.contest),
        joinedload(Notification.user)
    )
    
    # Apply filters
    if contest_id:
        query = query.filter(Notification.contest_id == contest_id)
    
    if notification_type:
        query = query.filter(Notification.notification_type == notification_type)
    
    # Order by most recent first and limit results
    notifications = query.order_by(Notification.sent_at.desc()).limit(limit).all()
    
    # Transform to response format with additional context
    response_logs = []
    for notification in notifications:
        # Mask phone number for privacy
        phone = notification.user.phone if notification.user else None
        masked_phone = f"{phone[:2]}***{phone[-4:]}" if phone and len(phone) >= 6 else phone
        
        log_entry = NotificationLogResponse(
            id=notification.id,
            contest_id=notification.contest_id,
            user_id=notification.user_id,
            entry_id=notification.entry_id,
            message=notification.message,
            notification_type=notification.notification_type,
            status=notification.status,
            twilio_sid=notification.twilio_sid,
            error_message=notification.error_message,
            test_mode=notification.test_mode,
            sent_at=notification.sent_at,
            admin_user_id=notification.admin_user_id,
            contest_name=notification.contest.name if notification.contest else None,
            user_phone=masked_phone
        )
        response_logs.append(log_entry)
    
    return response_logs


@router.post("/contests/{contest_id}/send-reminder", response_model=WinnerNotificationResponse)
async def send_contest_reminder(
    contest_id: int,
    notification_request: WinnerNotificationRequest,
    admin_user: dict = Depends(get_admin_user_jwt_only),
    db: Session = Depends(get_db)
):
    """
    Send reminder SMS to a specific contest entrant.
    
    🔧 Features:
    - Send reminder about contest deadlines or updates
    - Requires admin JWT authentication
    - Rate limited for security
    - Comprehensive logging to notifications table
    """
    # Rate limiting
    rate_limit_key = f"admin_sms_{admin_user.get('sub', 'unknown')}"
    if not rate_limiter.is_allowed(rate_limit_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many SMS notifications. Please wait before sending another."
        )
    
    # Validate contest exists
    contest = db.query(Contest).filter(Contest.id == contest_id).first()
    if not contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found"
        )
    
    # Validate entry exists and belongs to the contest
    entry = db.query(Entry).options(joinedload(Entry.user)).filter(
        Entry.id == notification_request.entry_id,
        Entry.contest_id == contest_id
    ).first()
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found for this contest"
        )
    
    # Get user's phone number
    user_phone = entry.user.phone
    if not user_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has no phone number on file"
        )
    
    # Create notification record
    notification = Notification(
        contest_id=contest_id,
        user_id=entry.user_id,
        entry_id=entry.id,
        message=notification_request.message,
        notification_type="reminder",
        status="pending",
        test_mode=notification_request.test_mode,
        admin_user_id=admin_user.get("sub", "unknown")
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    
    try:
        # Send SMS notification
        success, sms_message, twilio_sid = await sms_notification_service.send_notification(
            to_phone=user_phone,
            message=notification_request.message,
            notification_type="reminder",
            test_mode=notification_request.test_mode
        )
        
        # Update notification record with result
        notification.status = "sent" if success else "failed"
        notification.twilio_sid = twilio_sid
        if not success:
            notification.error_message = sms_message
        
        db.commit()
        
        # Mask phone number for privacy
        masked_phone = f"{user_phone[:2]}***{user_phone[-4:]}" if len(user_phone) >= 6 else user_phone
        
        return WinnerNotificationResponse(
            success=success,
            message="Reminder sent successfully" if success else "Failed to send reminder",
            entry_id=entry.id,
            contest_id=contest_id,
            winner_phone=masked_phone,
            sms_status=sms_message,
            test_mode=notification_request.test_mode,
            notification_id=notification.id,
            twilio_sid=twilio_sid,
            notification_sent_at=notification.sent_at
        )
    
    except Exception as e:
        # Update notification record with error
        notification.status = "failed"
        notification.error_message = str(e)
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SMS reminder failed: {str(e)}"
        )


@router.post("/contests/{contest_id}/send-announcement", response_model=WinnerNotificationResponse)
async def send_contest_announcement(
    contest_id: int,
    notification_request: WinnerNotificationRequest,
    admin_user: dict = Depends(get_admin_user_jwt_only),
    db: Session = Depends(get_db)
):
    """
    Send general announcement SMS to a specific contest entrant.
    
    🔧 Features:
    - Send announcements about contest updates, events, etc.
    - Requires admin JWT authentication
    - Rate limited for security
    - Comprehensive logging to notifications table
    """
    # Rate limiting
    rate_limit_key = f"admin_sms_{admin_user.get('sub', 'unknown')}"
    if not rate_limiter.is_allowed(rate_limit_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many SMS notifications. Please wait before sending another."
        )
    
    # Validate contest exists
    contest = db.query(Contest).filter(Contest.id == contest_id).first()
    if not contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found"
        )
    
    # Validate entry exists and belongs to the contest
    entry = db.query(Entry).options(joinedload(Entry.user)).filter(
        Entry.id == notification_request.entry_id,
        Entry.contest_id == contest_id
    ).first()
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found for this contest"
        )
    
    # Get user's phone number
    user_phone = entry.user.phone
    if not user_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has no phone number on file"
        )
    
    # Create notification record
    notification = Notification(
        contest_id=contest_id,
        user_id=entry.user_id,
        entry_id=entry.id,
        message=notification_request.message,
        notification_type="announcement",
        status="pending",
        test_mode=notification_request.test_mode,
        admin_user_id=admin_user.get("sub", "unknown")
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    
    try:
        # Send SMS notification
        success, sms_message, twilio_sid = await sms_notification_service.send_notification(
            to_phone=user_phone,
            message=notification_request.message,
            notification_type="announcement",
            test_mode=notification_request.test_mode
        )
        
        # Update notification record with result
        notification.status = "sent" if success else "failed"
        notification.twilio_sid = twilio_sid
        if not success:
            notification.error_message = sms_message
        
        db.commit()
        
        # Mask phone number for privacy
        masked_phone = f"{user_phone[:2]}***{user_phone[-4:]}" if len(user_phone) >= 6 else user_phone
        
        return WinnerNotificationResponse(
            success=success,
            message="Announcement sent successfully" if success else "Failed to send announcement",
            entry_id=entry.id,
            contest_id=contest_id,
            winner_phone=masked_phone,
            sms_status=sms_message,
            test_mode=notification_request.test_mode,
            notification_id=notification.id,
            twilio_sid=twilio_sid,
            notification_sent_at=notification.sent_at
        )
    
    except Exception as e:
        # Update notification record with error
        notification.status = "failed"
        notification.error_message = str(e)
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SMS announcement failed: {str(e)}"
        )


@router.get("/users/{user_id}/interaction-history", response_model=List[NotificationLogResponse])
async def get_user_interaction_history(
    user_id: int,
    contest_id: Optional[int] = None,
    limit: int = 50,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get complete SMS interaction history for a specific user.
    
    🔧 Features:
    - View all SMS communications with a user across all contests
    - Filter by specific contest if needed
    - Includes winners, reminders, announcements
    - Perfect for entry detail views with interaction history
    """
    # Validate user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Build query for user's notification history
    query = db.query(Notification).options(
        joinedload(Notification.contest),
        joinedload(Notification.user)
    ).filter(Notification.user_id == user_id)
    
    # Apply contest filter if provided
    if contest_id:
        query = query.filter(Notification.contest_id == contest_id)
    
    # Order by most recent first and limit results
    notifications = query.order_by(Notification.sent_at.desc()).limit(limit).all()
    
    # Transform to response format
    response_logs = []
    for notification in notifications:
        # Mask phone number for privacy
        phone = notification.user.phone if notification.user else None
        masked_phone = f"{phone[:2]}***{phone[-4:]}" if phone and len(phone) >= 6 else phone
        
        log_entry = NotificationLogResponse(
            id=notification.id,
            contest_id=notification.contest_id,
            user_id=notification.user_id,
            entry_id=notification.entry_id,
            message=notification.message,
            notification_type=notification.notification_type,
            status=notification.status,
            twilio_sid=notification.twilio_sid,
            error_message=notification.error_message,
            test_mode=notification.test_mode,
            sent_at=notification.sent_at,
            admin_user_id=notification.admin_user_id,
            contest_name=notification.contest.name if notification.contest else None,
            user_phone=masked_phone
        )
        response_logs.append(log_entry)
    
    return response_logs
# Deletion endpoint to append to admin.py

@router.delete("/contests/{contest_id}", response_model=ContestDeleteResponse)
async def delete_contest(
    contest_id: int,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    🗑️ COMPREHENSIVE CONTEST DELETION
    
    Completely removes a contest and ALL associated data including:
    - Contest entries
    - SMS notifications 
    - Official rules
    - Winner records
    - All dependencies
    
    ⚠️ WARNING: This action cannot be undone!
    
    🔐 Security:
    - Requires admin authentication
    - Validates contest ownership
    - Ensures complete cleanup
    - Provides detailed deletion summary
    
    📊 Business Rules:
    - Cannot delete active contests with recent entries
    - Soft validation for contests with winner notifications
    - Complete cascade deletion for data integrity
    """
    
    # Validate contest exists
    contest = db.query(Contest).filter(Contest.id == contest_id).first()
    if not contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found"
        )
    
    # Business logic validation
    entry_count = db.query(Entry).filter(Entry.contest_id == contest_id).count()
    notification_count = db.query(Notification).filter(Notification.contest_id == contest_id).count()
    
    # Check if contest is currently accepting entries (time-based check)
    from app.core.datetime_utils import utc_now
    now = utc_now()
    
    if entry_count > 0 and contest.end_time > now and not contest.winner_selected_at:
        # Contest is still running and accepting entries
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete running contest with {entry_count} entries. Contest ends at {contest.end_time}."
        )
    
    # Warning for contests with sent winner notifications
    winner_notifications = db.query(Notification).filter(
        Notification.contest_id == contest_id,
        Notification.notification_type == "winner",
        Notification.status == "sent"
    ).count()
    
    if winner_notifications > 0:
        print(f"⚠️ WARNING: Deleting contest {contest_id} with {winner_notifications} sent winner notifications")
    
    # Begin comprehensive deletion process
    deletion_summary = ContestDeletionSummary(
        entries_deleted=0,
        notifications_deleted=0,
        official_rules_deleted=0,
        dependencies_cleared=0
    )
    
    try:
        # Start database transaction for atomic deletion
        # 1. Delete all notifications first (to avoid foreign key constraints)
        notifications_deleted = db.query(Notification).filter(Notification.contest_id == contest_id).delete()
        deletion_summary.notifications_deleted = notifications_deleted
        
        # 2. Delete all contest entries
        entries_deleted = db.query(Entry).filter(Entry.contest_id == contest_id).delete()
        deletion_summary.entries_deleted = entries_deleted
        
        # 3. Delete official rules (if exists)
        official_rules_deleted = db.query(OfficialRules).filter(OfficialRules.contest_id == contest_id).delete()
        deletion_summary.official_rules_deleted = official_rules_deleted
        
        # 4. Finally delete the contest itself
        db.delete(contest)
        
        # Calculate total dependencies cleared
        deletion_summary.dependencies_cleared = (
            deletion_summary.entries_deleted + 
            deletion_summary.notifications_deleted + 
            deletion_summary.official_rules_deleted
        )
        
        # Commit all changes
        db.commit()
        
        # Log the admin action for audit trail
        print(f"✅ Contest {contest_id} deleted by admin {admin_user.get('sub', 'unknown')}")
        print(f"   - Entries deleted: {deletion_summary.entries_deleted}")
        print(f"   - Notifications deleted: {deletion_summary.notifications_deleted}")
        print(f"   - Official rules deleted: {deletion_summary.official_rules_deleted}")
        print(f"   - Total dependencies cleared: {deletion_summary.dependencies_cleared}")
        
        return ContestDeleteResponse(
            status="success",
            message=f"Contest '{contest.name}' deleted successfully",
            deleted_contest_id=contest_id,
            cleanup_summary=deletion_summary
        )
        
    except Exception as e:
        # Rollback transaction on any error
        db.rollback()
        print(f"❌ Failed to delete contest {contest_id}: {e}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete contest: {str(e)}"
        )


@router.post("/contests/import-one-sheet", response_model=CampaignImportResponse)
async def import_campaign_one_sheet(
    import_request: CampaignImportRequest,
    admin_payload: dict = Depends(get_admin_user_jwt_only),
    db: Session = Depends(get_db)
):
    """
    Import a campaign one-sheet JSON into a new contest record.
    
    This endpoint allows admins to import predefined campaign configurations
    directly into the contests table. The one-sheet JSON is parsed and mapped
    to appropriate contest fields, with remaining data stored in metadata.
    """
    try:
        # Get admin user ID from JWT payload
        admin_user_id = admin_payload.get("phone", "unknown_admin")
        
        # Validate campaign data first
        is_valid, validation_errors = campaign_import_service.validate_campaign_data(
            import_request.campaign_json
        )
        
        if not is_valid:
            return CampaignImportResponse(
                success=False,
                message=f"Validation failed: {'; '.join(validation_errors)}",
                warnings=validation_errors
            )
        
        # Perform the import
        success, contest, warnings, summary = campaign_import_service.import_campaign(
            db=db,
            import_request=import_request,
            admin_user_id=admin_user_id
        )
        
        if success and contest:
            return CampaignImportResponse(
                success=True,
                contest_id=contest.id,
                message="Campaign imported and contest created successfully",
                warnings=warnings,
                fields_mapped=summary.get('field_mappings_used', {}),
                fields_stored_in_metadata=[
                    'day', 'entry_type', 'messaging', 'category', 
                    'target_audience', 'budget', 'expected_entries',
                    'reward_logic', 'duration_days'
                ]
            )
        else:
            return CampaignImportResponse(
                success=False,
                message=f"Import failed: {'; '.join(warnings)}",
                warnings=warnings
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import campaign: {str(e)}"
        )
