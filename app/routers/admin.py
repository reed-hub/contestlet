from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import datetime
from typing import List
import random
from app.database.database import get_db
from app.models.contest import Contest
from app.models.entry import Entry
from app.models.user import User
from app.models.official_rules import OfficialRules
from app.schemas.admin import (
    AdminContestCreate, AdminContestUpdate, AdminContestResponse, 
    WinnerSelectionResponse, AdminAuthResponse, AdminEntryResponse,
    WinnerNotificationRequest, WinnerNotificationResponse
)
from app.core.admin_auth import get_admin_user
from app.core.sms_notification_service import sms_notification_service
from app.core.rate_limiter import rate_limiter
from app.models.notification import Notification

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
    contest_dict = contest_data.dict(exclude={'official_rules'})
    rules_dict = contest_data.official_rules.dict()
    
    # Validate legal compliance
    validate_contest_compliance(contest_dict, rules_dict)
    
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
    
    # If activating contest, validate compliance
    if contest_update.active and contest.active != contest_update.active:
        contest_dict = {
            "name": contest.name,
            "start_time": contest.start_time,
            "end_time": contest.end_time,
            "prize_description": contest.prize_description
        }
        rules_dict = {}
        if contest.official_rules:
            rules_dict = {
                "eligibility_text": contest.official_rules.eligibility_text,
                "sponsor_name": contest.official_rules.sponsor_name,
                "start_date": contest.official_rules.start_date,
                "end_date": contest.official_rules.end_date,
                "prize_value_usd": contest.official_rules.prize_value_usd
            }
        validate_contest_compliance(contest_dict, rules_dict)
    
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
            selected=entry.selected
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
    # Get contest
    contest = db.query(Contest).filter(Contest.id == contest_id).first()
    if not contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found"
        )
    
    # Check if contest has ended
    if contest.end_time > datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot select winner for an active contest. Contest must end first."
        )
    
    # Get all entries for this contest
    entries = db.query(Entry).options(joinedload(Entry.user)).filter(
        Entry.contest_id == contest_id
    ).all()
    
    if not entries:
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
        return WinnerSelectionResponse(
            success=False,
            message="Winner already selected for this contest",
            winner_entry_id=existing_winner.id,
            winner_user_phone=existing_winner.user.phone,
            total_entries=len(entries)
        )
    
    # Randomly select winner
    winner_entry = random.choice(entries)
    winner_entry.selected = True
    db.commit()
    
    return WinnerSelectionResponse(
        success=True,
        message=f"Winner selected successfully from {len(entries)} entries",
        winner_entry_id=winner_entry.id,
        winner_user_phone=winner_entry.user.phone,
        total_entries=len(entries)
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
