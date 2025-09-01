"""
Universal Contest Management Endpoints

Unified endpoints for contest creation and editing using the universal form.
Provides consistent validation and user experience across both operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from app.database.database import get_db
from app.models.contest import Contest
from app.models.entry import Entry
from app.schemas.universal_contest import UniversalContestForm, UniversalContestResponse
from app.schemas.universal_contest_edit import UniversalContestFormEdit
from app.services.contest_service import ContestService
from app.core.admin_auth import get_admin_user
from app.core.datetime_utils import utc_now
from app.core.contest_status import calculate_contest_status, can_edit_contest

router = APIRouter(prefix="/universal/contests", tags=["universal-contests"])


def build_universal_response(contest: Contest, db: Session) -> UniversalContestResponse:
    """Build a universal contest response with all required fields"""
    
    # Get entry count
    entry_count = db.query(Entry).filter(Entry.contest_id == contest.id).count()
    
    # Calculate current status
    current_time = utc_now()
    calculated_status = calculate_contest_status(
        contest.status,
        contest.start_time,
        contest.end_time,
        contest.winner_selected_at,
        current_time
    )
    
    # Get sponsor information
    sponsor_name = None
    if contest.sponsor_profile:
        sponsor_name = contest.sponsor_profile.company_name
    
    # Generate location summary
    contest_service = ContestService(db)
    location_summary = contest_service._generate_location_summary(contest)
    
    # Determine edit permissions
    can_edit = can_edit_contest(contest.status, "admin", True)
    edit_restrictions = []
    
    if contest.status == 'active':
        edit_restrictions = [
            'start_time', 'end_time', 'contest_type', 'entry_method',
            'winner_selection_method', 'minimum_age', 'max_entries_per_person',
            'total_entry_limit', 'location_type', 'selected_states'
        ]
    elif contest.status == 'ended':
        edit_restrictions = [
            'start_time', 'end_time', 'contest_type', 'entry_method',
            'winner_selection_method', 'minimum_age', 'max_entries_per_person',
            'total_entry_limit', 'location_type', 'selected_states', 'name'
        ]
    elif contest.status == 'complete':
        can_edit = False
        edit_restrictions = ['*']
    
    # Build official rules data
    official_rules_data = None
    if contest.official_rules:
        official_rules_data = {
            'eligibility_text': contest.official_rules.eligibility_text,
            'sponsor_name': contest.official_rules.sponsor_name,
            'prize_value_usd': contest.official_rules.prize_value_usd,
            'start_date': contest.official_rules.start_date,
            'end_date': contest.official_rules.end_date,
            'terms_url': contest.official_rules.terms_url
        }
    
    return UniversalContestResponse(
        # Core Contest Data
        id=contest.id,
        name=contest.name,
        description=contest.description,
        start_time=contest.start_time,
        end_time=contest.end_time,
        prize_description=contest.prize_description,
        status=calculated_status,
        created_at=contest.created_at,
        
        # Sponsor Information
        sponsor_profile_id=contest.sponsor_profile_id,
        sponsor_name=sponsor_name,
        
        # Location Data
        location=contest.location,
        location_type=contest.location_type or "united_states",
        selected_states=contest.selected_states or [],
        radius_address=contest.radius_address,
        radius_miles=contest.radius_miles,
        location_summary=location_summary,
        
        # Configuration
        contest_type=contest.contest_type or "general",
        entry_method=contest.entry_method or "sms",
        winner_selection_method=contest.winner_selection_method or "random",
        minimum_age=contest.minimum_age or 18,
        max_entries_per_person=contest.max_entries_per_person,
        total_entry_limit=contest.total_entry_limit,
        
        # Additional Data
        consolation_offer=contest.consolation_offer,
        geographic_restrictions=contest.geographic_restrictions,
        contest_tags=contest.contest_tags or [],
        promotion_channels=contest.promotion_channels or [],
        
        # Visual Branding
        image_url=contest.image_url,
        sponsor_url=contest.sponsor_url,
        
        # Metadata
        entry_count=entry_count,
        winner_entry_id=contest.winner_entry_id,
        winner_phone=contest.winner_phone,
        winner_selected_at=contest.winner_selected_at,
        
        # Official Rules
        official_rules=official_rules_data,
        
        # Status Information
        is_active=(calculated_status == 'active'),
        can_edit=can_edit,
        edit_restrictions=edit_restrictions if edit_restrictions else None
    )


@router.post("/", response_model=UniversalContestResponse)
async def create_contest_universal(
    contest_data: UniversalContestForm,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Create a new contest using the universal form.
    
    This endpoint provides the same interface as the edit endpoint,
    ensuring consistent user experience across creation and editing.
    """
    try:
        contest_service = ContestService(db)
        admin_user_id = int(admin_user["user_id"]) if admin_user["user_id"] != "legacy_admin" else 1
        
        # Create contest using universal form
        contest = contest_service.create_contest_universal(contest_data, admin_user_id)
        
        # Build and return response
        return build_universal_response(contest, db)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create contest: {str(e)}"
        )


@router.put("/{contest_id}", response_model=UniversalContestResponse)
async def update_contest_universal(
    contest_id: int,
    contest_data: UniversalContestFormEdit,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing contest using the universal form.
    
    This endpoint provides the same interface as the create endpoint,
    ensuring consistent user experience across creation and editing.
    
    Features:
    - Status-based field restrictions
    - Admin override support for active contests
    - Automatic validation based on contest state
    """
    try:
        contest_service = ContestService(db)
        admin_user_id = int(admin_user["user_id"]) if admin_user["user_id"] != "legacy_admin" else 1
        
        # Update contest using universal form
        contest = contest_service.update_contest_universal(contest_id, contest_data, admin_user_id)
        
        # Build and return response
        return build_universal_response(contest, db)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update contest: {str(e)}"
        )


@router.get("/{contest_id}", response_model=UniversalContestResponse)
async def get_contest_universal(
    contest_id: int,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get contest data in universal form format.
    
    This endpoint returns contest data in the same format used by the
    universal form, making it easy to populate edit forms.
    """
    try:
        contest_service = ContestService(db)
        contest = contest_service.get_contest_by_id(contest_id)
        
        if not contest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contest with ID {contest_id} not found"
            )
        
        return build_universal_response(contest, db)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve contest: {str(e)}"
        )


@router.get("/{contest_id}/edit-info")
async def get_contest_edit_info(
    contest_id: int,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get information about what fields can be edited for a contest.
    
    Returns:
    - can_edit: Whether the contest can be edited at all
    - restricted_fields: List of fields that cannot be edited without override
    - requires_override: Whether admin override is required for any edits
    - status: Current contest status
    """
    try:
        contest_service = ContestService(db)
        contest = contest_service.get_contest_by_id(contest_id)
        
        if not contest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contest with ID {contest_id} not found"
            )
        
        # Calculate current status
        current_time = utc_now()
        calculated_status = calculate_contest_status(
            contest.status,
            contest.start_time,
            contest.end_time,
            contest.winner_selected_at,
            current_time
        )
        
        # Determine edit permissions
        can_edit = can_edit_contest(contest.status, "admin", True)
        
        # Define restricted fields based on status
        restricted_fields = []
        requires_override = False
        
        if contest.status == 'active':
            restricted_fields = [
                'start_time', 'end_time', 'contest_type', 'entry_method',
                'winner_selection_method', 'minimum_age', 'max_entries_per_person',
                'total_entry_limit', 'location_type', 'selected_states'
            ]
            requires_override = True
        elif contest.status == 'ended':
            restricted_fields = [
                'start_time', 'end_time', 'contest_type', 'entry_method',
                'winner_selection_method', 'minimum_age', 'max_entries_per_person',
                'total_entry_limit', 'location_type', 'selected_states', 'name'
            ]
            requires_override = True
        elif contest.status == 'complete':
            can_edit = False
            restricted_fields = ['*']
            requires_override = False  # Override won't help for complete contests
        
        return {
            "contest_id": contest_id,
            "status": calculated_status,
            "can_edit": can_edit,
            "restricted_fields": restricted_fields,
            "requires_override": requires_override,
            "entry_count": db.query(Entry).filter(Entry.contest_id == contest.id).count(),
            "has_winner": contest.winner_entry_id is not None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get edit info: {str(e)}"
        )
