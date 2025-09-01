from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.database.database import get_db
from app.models.user import User
from app.models.entry import Entry
from app.core.contest_status import calculate_contest_status
from app.core.datetime_utils import utc_now
from app.schemas.admin import (
    AdminContestCreate, AdminContestUpdate, AdminContestResponse,
    AdminEntryResponse, WinnerSelectionResponse, WinnerNotificationResponse,
    ContestDeleteResponse, ContestDeletionSummary
)
from app.schemas.role_system import UserWithRole
from app.core.admin_auth import get_admin_user
from app.core.dependencies import get_admin_user as get_admin_user_dependency
from app.core.exceptions import raise_authorization_error
from app.services.contest_service import ContestService
from app.services.admin_service import AdminService

router = APIRouter(prefix="/admin/contests", tags=["admin-contests"])


@router.post("/", response_model=AdminContestResponse)
async def create_contest(
    contest_data: AdminContestCreate,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Create a new contest with admin validation"""
    contest_service = ContestService(db)
    contest = contest_service.create_contest(contest_data, int(admin_user["user_id"]) if admin_user["user_id"] != "legacy_admin" else 1)
    
    # Get entry count for this contest
    entry_count = db.query(Entry).filter(Entry.contest_id == contest.id).count()
    
    # Manually construct response with required fields
    contest_dict = {
        "id": contest.id,
        "name": contest.name,
        "description": contest.description,
        "location": contest.location,
        "latitude": contest.latitude,
        "longitude": contest.longitude,
        "start_time": contest.start_time,
        "end_time": contest.end_time,
        "prize_description": contest.prize_description,
        "created_at": contest.created_at,
        "entry_count": entry_count,
        "status": contest.status,
        "winner_entry_id": contest.winner_entry_id,
        "winner_phone": contest.winner_phone,
        "winner_selected_at": contest.winner_selected_at,
        "created_timezone": contest.created_timezone,
        "admin_user_id": contest.admin_user_id,
        "image_url": contest.image_url,
        "sponsor_url": contest.sponsor_url,
        "official_rules": contest.official_rules
    }
    
    return AdminContestResponse(**contest_dict)


@router.put("/{contest_id}", response_model=AdminContestResponse)
async def update_contest(
    contest_id: int,
    contest_data: AdminContestUpdate,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Update existing contest with admin override support"""
    contest_service = ContestService(db)
    contest = contest_service.update_contest(contest_id, contest_data, admin_user_id=int(admin_user["user_id"]) if admin_user["user_id"] != "legacy_admin" else 1)
    
    # Check if admin override was used for response message
    override_used = contest_data.admin_override and contest_data.override_reason
    
    # Create response with enhanced status system
    current_time = utc_now()
    calculated_status = calculate_contest_status(
        contest.status,
        contest.start_time,
        contest.end_time,
        contest.winner_selected_at,
        current_time
    )
    
    contest_data_dict = {
        'id': contest.id,
        'name': contest.name,
        'description': contest.description,
        'location': contest.location,
        'latitude': contest.latitude,
        'longitude': contest.longitude,
        'start_time': contest.start_time,
        'end_time': contest.end_time,
        'prize_description': contest.prize_description,

        'created_at': contest.created_at,
        'entry_count': len(contest.entries) if contest.entries else 0,
        'status': calculated_status,  # Enhanced status calculation
        'winner_entry_id': contest.winner_entry_id,
        'winner_phone': contest.winner_phone,
        'winner_selected_at': contest.winner_selected_at,
        'created_timezone': contest.created_timezone,
        'admin_user_id': contest.admin_user_id,
        'image_url': contest.image_url,
        'sponsor_url': contest.sponsor_url,
        'official_rules': None,
        
        # Enhanced Status System fields
        'submitted_at': getattr(contest, 'submitted_at', None),
        'approved_at': getattr(contest, 'approved_at', None),
        'rejected_at': getattr(contest, 'rejected_at', None),
        'rejection_reason': getattr(contest, 'rejection_reason', None),
        'approval_message': getattr(contest, 'approval_message', None),

        'created_by_user_id': getattr(contest, 'created_by_user_id', None),
        'sponsor_name': contest.sponsor_profile.company_name if contest.sponsor_profile else None
    }
    
    return AdminContestResponse(**contest_data_dict)


@router.get("/{contest_id}", response_model=AdminContestResponse)
async def get_admin_contest_by_id(
    contest_id: int,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get single contest details for admin editing.
    
    - Requires admin authentication
    - Returns full contest data including sensitive fields
    - Used by admin edit interface
    """
    contest_service = ContestService(db)
    contest = contest_service.get_contest_by_id(contest_id)
    
    if not contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found"
        )
    
    # Use Enhanced Status System calculation
    current_time = utc_now()
    calculated_status = calculate_contest_status(
        contest.status,
        contest.start_time,
        contest.end_time,
        contest.winner_selected_at,
        current_time
    )
    
    # Create response with enhanced status system fields
    contest_data = {
        'id': contest.id,
        'name': contest.name,
        'description': contest.description,
        'location': contest.location,
        'latitude': contest.latitude,
        'longitude': contest.longitude,
        'start_time': contest.start_time,
        'end_time': contest.end_time,
        'prize_description': contest.prize_description,

        'created_at': contest.created_at,
        'entry_count': len(contest.entries) if contest.entries else 0,
        'status': calculated_status,  # Enhanced status calculation
        'winner_entry_id': contest.winner_entry_id,
        'winner_phone': contest.winner_phone,
        'winner_selected_at': contest.winner_selected_at,
        'created_timezone': contest.created_timezone,
        'admin_user_id': contest.admin_user_id,
        'image_url': contest.image_url,
        'sponsor_url': contest.sponsor_url,
        'official_rules': None,  # TODO: Load if needed
        
        # Enhanced Status System fields
        'submitted_at': getattr(contest, 'submitted_at', None),
        'approved_at': getattr(contest, 'approved_at', None),
        'rejected_at': getattr(contest, 'rejected_at', None),
        'rejection_reason': getattr(contest, 'rejection_reason', None),
        'approval_message': getattr(contest, 'approval_message', None),

        'created_by_user_id': getattr(contest, 'created_by_user_id', None),
        'sponsor_name': contest.sponsor_profile.company_name if contest.sponsor_profile else None
    }
    
    return AdminContestResponse(**contest_data)


@router.get("/", response_model=List[AdminContestResponse])
async def get_all_contests(
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get all contests with admin access"""
    contest_service = ContestService(db)
    contests = contest_service.get_all_contests()
    
    # Convert contests to response format with enhanced status system
    contest_responses = []
    for contest in contests:
        # Use Enhanced Status System calculation
        current_time = utc_now()
        calculated_status = calculate_contest_status(
            contest.status,
            contest.start_time,
            contest.end_time,
            contest.winner_selected_at,
            current_time
        )
        
        # Create response dict with enhanced status system fields
        contest_data = {
            'id': contest.id,
            'name': contest.name,
            'description': contest.description,
            'location': contest.location,
            'latitude': contest.latitude,
            'longitude': contest.longitude,
            'start_time': contest.start_time,
            'end_time': contest.end_time,
            'prize_description': contest.prize_description,
    
            'created_at': contest.created_at,
            'entry_count': len(contest.entries) if contest.entries else 0,
            'status': calculated_status,  # Enhanced status calculation
            'winner_entry_id': contest.winner_entry_id,
            'winner_phone': contest.winner_phone,
            'winner_selected_at': contest.winner_selected_at,
            'created_timezone': contest.created_timezone,
            'admin_user_id': contest.admin_user_id,
            'image_url': contest.image_url,
            'sponsor_url': contest.sponsor_url,
            'official_rules': None,  # TODO: Load if needed
            
            # Enhanced Status System fields
            'submitted_at': getattr(contest, 'submitted_at', None),
            'approved_at': getattr(contest, 'approved_at', None),
            'rejected_at': getattr(contest, 'rejected_at', None),
            'rejection_reason': getattr(contest, 'rejection_reason', None),
            'approval_message': getattr(contest, 'approval_message', None),
    
            'created_by_user_id': getattr(contest, 'created_by_user_id', None),
            'sponsor_name': contest.sponsor_profile.company_name if contest.sponsor_profile else None
        }
        contest_responses.append(AdminContestResponse(**contest_data))
    
    return contest_responses


@router.get("/{contest_id}/entries", response_model=List[AdminEntryResponse])
async def get_contest_entries(
    contest_id: int,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get all entries for a specific contest"""
    contest_service = ContestService(db)
    entries = contest_service.get_contest_entries(contest_id)
    return [AdminEntryResponse.from_orm(entry) for entry in entries]


@router.post("/{contest_id}/select-winner", response_model=WinnerSelectionResponse)
async def select_winner(
    contest_id: int,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Select a random winner for a contest"""
    contest_service = ContestService(db)
    winner = contest_service.select_winner(contest_id, admin_user["sub"])
    
    if not winner:
        return WinnerSelectionResponse(
            success=False,
            message="No eligible entries found for winner selection"
        )
    
    return WinnerSelectionResponse(
        success=True,
        message=f"Winner selected: {winner.user.phone}",
        winner_entry_id=winner.id,
        winner_phone=winner.user.phone
    )


@router.delete("/{contest_id}", response_model=ContestDeleteResponse)
async def delete_contest(
    contest_id: int,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Delete contest and related data"""
    contest_service = ContestService(db)
    success = contest_service.delete_contest(contest_id)
    
    return ContestDeleteResponse(
        success=success,
        message=f"Contest {contest_id} deleted successfully"
    )


@router.get("/{contest_id}/statistics")
async def get_contest_statistics(
    contest_id: int,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive statistics for a contest"""
    contest_service = ContestService(db)
    stats = contest_service.get_contest_statistics(contest_id)
    return stats
