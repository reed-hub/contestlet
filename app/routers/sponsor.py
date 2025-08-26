"""
Sponsor API Endpoints

Role-specific endpoints for sponsor users including:
- Sponsor profile management
- Contest creation and management
- Sponsor analytics
- Contest approval workflow
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from app.database.database import get_db
from app.core.dependencies import get_sponsor_user, get_current_user
from app.models import User, Contest, Entry, SponsorProfile, ContestApprovalAudit
from app.schemas.role_system import (
    SponsorProfileCreate, 
    SponsorProfileUpdate, 
    SponsorProfileResponse,
    UnifiedSponsorProfileResponse,
    RoleUpgradeRequest,
    RoleUpgradeResponse,
    UserWithRole
)
from app.schemas.admin import AdminContestCreate, AdminContestResponse, AdminContestUpdate
from app.schemas.contest import ContestResponse
from app.core.datetime_utils import utc_now

router = APIRouter(prefix="/sponsor", tags=["sponsor"])


# =====================================================
# SPONSOR PROFILE MANAGEMENT
# =====================================================

@router.get("/profile", response_model=UnifiedSponsorProfileResponse, deprecated=True)
async def get_sponsor_user_profile(
    sponsor_user: User = Depends(get_sponsor_user),
    db: Session = Depends(get_db)
):
    """
    DEPRECATED: Use GET /users/me instead.
    
    Get sponsor's unified profile combining user and company information.
    """
    # Create unified response
    unified_profile = UnifiedSponsorProfileResponse(
        user_id=sponsor_user.id,
        phone=sponsor_user.phone,
        role=sponsor_user.role,
        is_verified=sponsor_user.is_verified,
        created_at=sponsor_user.created_at,
        role_assigned_at=sponsor_user.role_assigned_at,
        company_profile=sponsor_user.sponsor_profile
    )
    
    return unified_profile


@router.get("/company-profile", response_model=SponsorProfileResponse)
async def get_sponsor_company_profile(
    sponsor_user: User = Depends(get_sponsor_user),
    db: Session = Depends(get_db)
):
    """Get sponsor's company profile information"""
    if not sponsor_user.sponsor_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sponsor profile not found"
        )
    
    return sponsor_user.sponsor_profile


@router.put("/profile", response_model=UnifiedSponsorProfileResponse, deprecated=True)
async def update_sponsor_profile(
    profile_update: SponsorProfileUpdate,
    sponsor_user: User = Depends(get_sponsor_user),
    db: Session = Depends(get_db)
):
    """
    DEPRECATED: Use PUT /users/me instead.
    
    Update sponsor's profile information.
    """
    if not sponsor_user.sponsor_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sponsor profile not found"
        )
    
    # Update profile fields
    update_data = profile_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(sponsor_user.sponsor_profile, field, value)
    
    sponsor_user.sponsor_profile.updated_at = utc_now()
    
    db.commit()
    db.refresh(sponsor_user.sponsor_profile)
    
    # Return unified profile response
    unified_profile = UnifiedSponsorProfileResponse(
        user_id=sponsor_user.id,
        phone=sponsor_user.phone,
        role=sponsor_user.role,
        is_verified=sponsor_user.is_verified,
        created_at=sponsor_user.created_at,
        role_assigned_at=sponsor_user.role_assigned_at,
        company_profile=sponsor_user.sponsor_profile
    )
    
    return unified_profile


# =====================================================
# SPONSOR CONTEST MANAGEMENT
# =====================================================

@router.get("/contests", response_model=List[AdminContestResponse])
async def get_sponsor_contests(
    sponsor_user: User = Depends(get_sponsor_user),
    db: Session = Depends(get_db)
):
    """Get all contests created by this sponsor"""
    contests = db.query(Contest).options(
        joinedload(Contest.official_rules)
    ).filter(
        Contest.created_by_user_id == sponsor_user.id
    ).order_by(Contest.created_at.desc()).all()
    
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


@router.get("/contests/{contest_id}", response_model=AdminContestResponse)
async def get_sponsor_contest(
    contest_id: int,
    sponsor_user: User = Depends(get_sponsor_user),
    db: Session = Depends(get_db)
):
    """Get a specific contest created by this sponsor"""
    contest = db.query(Contest).options(
        joinedload(Contest.official_rules)
    ).filter(
        Contest.id == contest_id,
        Contest.created_by_user_id == sponsor_user.id
    ).first()
    
    if not contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found or not owned by sponsor"
        )
    
    entry_count = db.query(Entry).filter(Entry.contest_id == contest.id).count()
    response_data = {
        **contest.__dict__,
        "entry_count": entry_count,
        "official_rules": contest.official_rules
    }
    
    return AdminContestResponse(**response_data)


@router.post("/contests", response_model=AdminContestResponse)
async def create_sponsor_contest(
    contest_data: AdminContestCreate,
    sponsor_user: User = Depends(get_sponsor_user),
    db: Session = Depends(get_db)
):
    """Create a new contest as a sponsor (requires admin approval)"""
    # Convert Pydantic models to dict for validation
    contest_dict = contest_data.dict(exclude={'official_rules', 'sms_templates'})
    rules_dict = contest_data.official_rules.dict()
    sms_templates = contest_data.sms_templates
    
    # Add sponsor metadata to contest
    contest_dict['created_by_user_id'] = sponsor_user.id
    contest_dict['sponsor_profile_id'] = sponsor_user.sponsor_profile.id if sponsor_user.sponsor_profile else None
    contest_dict['is_approved'] = False  # Sponsor contests require approval
    contest_dict['admin_user_id'] = str(sponsor_user.id)
    contest_dict['created_timezone'] = "UTC"  # Default for sponsors
    
    # Create contest
    from app.models.contest import Contest
    from app.models.official_rules import OfficialRules
    from app.models.sms_template import SMSTemplate
    
    contest = Contest(**contest_dict)
    db.add(contest)
    db.flush()  # Get the contest ID
    
    # Create official rules
    official_rules = OfficialRules(
        contest_id=contest.id,
        **rules_dict
    )
    db.add(official_rules)
    
    # Create SMS templates if provided
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
    
    # Create approval audit entry
    approval_audit = ContestApprovalAudit(
        contest_id=contest.id,
        action="pending",
        reason="Contest created by sponsor, awaiting admin approval"
    )
    db.add(approval_audit)
    
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
async def update_sponsor_contest(
    contest_id: int,
    contest_update: AdminContestUpdate,
    sponsor_user: User = Depends(get_sponsor_user),
    db: Session = Depends(get_db)
):
    """Update a contest created by this sponsor"""
    # Get existing contest
    contest = db.query(Contest).options(
        joinedload(Contest.official_rules)
    ).filter(
        Contest.id == contest_id,
        Contest.created_by_user_id == sponsor_user.id
    ).first()
    
    if not contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found or not owned by sponsor"
        )
    
    # Check if contest is approved - sponsors can only edit unapproved contests
    if contest.is_approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot edit approved contests. Contact admin for changes."
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
            contest.official_rules.updated_at = utc_now()
        else:
            # Create new rules if none exist
            from app.models.official_rules import OfficialRules
            rules_data = contest_update.official_rules.dict(exclude_unset=True)
            official_rules = OfficialRules(contest_id=contest.id, **rules_data)
            db.add(official_rules)
    
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


@router.delete("/contests/{contest_id}")
async def delete_sponsor_contest(
    contest_id: int,
    sponsor_user: User = Depends(get_sponsor_user),
    db: Session = Depends(get_db)
):
    """Delete a contest created by this sponsor (only if not approved)"""
    contest = db.query(Contest).filter(
        Contest.id == contest_id,
        Contest.created_by_user_id == sponsor_user.id
    ).first()
    
    if not contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found or not owned by sponsor"
        )
    
    # Check if contest is approved
    if contest.is_approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete approved contests. Contact admin for assistance."
        )
    
    # Check if contest has entries
    entry_count = db.query(Entry).filter(Entry.contest_id == contest_id).count()
    if entry_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete contest with {entry_count} entries"
        )
    
    # Delete contest (cascade will handle related records)
    db.delete(contest)
    db.commit()
    
    return {"message": "Contest deleted successfully"}


# =====================================================
# SPONSOR ANALYTICS
# =====================================================

@router.get("/analytics")
async def get_sponsor_analytics(
    sponsor_user: User = Depends(get_sponsor_user),
    db: Session = Depends(get_db)
):
    """Get analytics for sponsor's contests"""
    # Get contest counts
    total_contests = db.query(Contest).filter(
        Contest.created_by_user_id == sponsor_user.id
    ).count()
    
    approved_contests = db.query(Contest).filter(
        Contest.created_by_user_id == sponsor_user.id,
        Contest.is_approved == True
    ).count()
    
    pending_contests = db.query(Contest).filter(
        Contest.created_by_user_id == sponsor_user.id,
        Contest.is_approved == False
    ).count()
    
    # Get total entries across all sponsor contests
    total_entries = db.query(Entry).join(Contest).filter(
        Contest.created_by_user_id == sponsor_user.id
    ).count()
    
    # Get active contests (approved and within time range)
    from app.core.datetime_utils import utc_now
    now = utc_now()
    active_contests = db.query(Contest).filter(
        Contest.created_by_user_id == sponsor_user.id,
        Contest.is_approved == True,
        Contest.start_time <= now,
        Contest.end_time >= now
    ).count()
    
    return {
        "total_contests": total_contests,
        "approved_contests": approved_contests,
        "pending_contests": pending_contests,
        "active_contests": active_contests,
        "total_entries": total_entries,
        "approval_rate": round((approved_contests / total_contests * 100) if total_contests > 0 else 0, 1)
    }


@router.get("/contests/{contest_id}/analytics")
async def get_contest_analytics(
    contest_id: int,
    sponsor_user: User = Depends(get_sponsor_user),
    db: Session = Depends(get_db)
):
    """Get detailed analytics for a specific contest"""
    contest = db.query(Contest).filter(
        Contest.id == contest_id,
        Contest.created_by_user_id == sponsor_user.id
    ).first()
    
    if not contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found or not owned by sponsor"
        )
    
    # Get entry statistics
    total_entries = db.query(Entry).filter(Entry.contest_id == contest_id).count()
    
    # Get entries by day (last 30 days)
    from datetime import timedelta
    from sqlalchemy import func, Date
    
    thirty_days_ago = utc_now() - timedelta(days=30)
    entries_by_day = db.query(
        func.date(Entry.created_at).label('date'),
        func.count(Entry.id).label('count')
    ).filter(
        Entry.contest_id == contest_id,
        Entry.created_at >= thirty_days_ago
    ).group_by(func.date(Entry.created_at)).all()
    
    return {
        "contest_id": contest_id,
        "contest_name": contest.name,
        "total_entries": total_entries,
        "is_approved": contest.is_approved,
        "is_active": contest.start_time <= utc_now() <= contest.end_time,
        "entries_by_day": [{"date": str(day.date), "count": day.count} for day in entries_by_day]
    }


# =====================================================
# ROLE UPGRADE REQUEST
# =====================================================

@router.post("/upgrade-request", response_model=RoleUpgradeResponse)
async def request_sponsor_upgrade(
    upgrade_request: RoleUpgradeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Request upgrade from user to sponsor role"""
    if current_user.role != "user":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot upgrade from {current_user.role} role. Only users can upgrade to sponsor."
        )
    
    # Check if user already has a sponsor profile
    if current_user.sponsor_profile:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already has a sponsor profile"
        )
    
    # Create sponsor profile (unverified)
    sponsor_profile = SponsorProfile(
        user_id=current_user.id,
        company_name=upgrade_request.company_name,
        contact_name=upgrade_request.contact_name,
        contact_email=upgrade_request.contact_email,
        website_url=upgrade_request.website_url,
        industry=upgrade_request.industry,
        description=upgrade_request.description,
        verification_document_url=upgrade_request.verification_document_url,
        is_verified=False  # Requires admin verification
    )
    
    db.add(sponsor_profile)
    
    # Update user role to sponsor
    old_role = current_user.role
    current_user.role = "sponsor"
    current_user.role_assigned_at = utc_now()
    
    # Create role audit entry
    from app.models.role_audit import RoleAudit
    role_audit = RoleAudit(
        user_id=current_user.id,
        old_role=old_role,
        new_role="sponsor",
        reason="User requested upgrade to sponsor role"
    )
    db.add(role_audit)
    
    db.commit()
    db.refresh(sponsor_profile)
    
    return RoleUpgradeResponse(
        message="Sponsor role upgrade successful. Profile created and awaiting admin verification.",
        status="pending_verification",
        user_id=current_user.id,
        new_role="sponsor",
        sponsor_profile_id=sponsor_profile.id
    )
