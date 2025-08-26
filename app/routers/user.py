"""
User API Endpoints

Role-specific endpoints for regular users including:
- User profile management
- Contest participation
- Entry history
- User-specific contest viewing
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from app.database.database import get_db
from app.core.dependencies import get_current_user, get_verified_user
from app.models import User, Contest, Entry
from app.schemas.contest import ContestResponse
from app.schemas.entry import EntryResponse
from app.schemas.role_system import UserWithRole, RoleUpgradeRequest, RoleUpgradeResponse
from app.core.datetime_utils import utc_now

router = APIRouter(prefix="/user", tags=["user"])


# =====================================================
# USER PROFILE MANAGEMENT
# =====================================================

@router.get("/profile", response_model=UserWithRole, deprecated=True)
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    DEPRECATED: Use GET /users/me instead.
    
    Get user's profile information.
    """
    return current_user


@router.put("/profile", response_model=UserWithRole, deprecated=True)
async def update_user_profile(
    # For now, users can only update verification status through admin
    # Future: Add fields like name, email, preferences, etc.
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    DEPRECATED: Use PUT /users/me instead.
    
    Update user's profile information.
    """
    # Currently, users have limited profile fields to update
    # This endpoint is prepared for future profile expansions
    
    # For now, just return current user info
    # Future: Allow updating name, email, preferences, etc.
    
    return current_user


# =====================================================
# CONTEST PARTICIPATION
# =====================================================

@router.get("/contests/available", response_model=List[ContestResponse])
async def get_available_contests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all contests available for user participation (approved and active)"""
    now = utc_now()
    
    contests = db.query(Contest).filter(
        Contest.is_approved == True,  # Only approved contests
        Contest.start_time <= now,    # Contest has started
        Contest.end_time >= now       # Contest hasn't ended
    ).order_by(Contest.created_at.desc()).all()
    
    response_list = []
    for contest in contests:
        # Check if user has already entered this contest
        user_entry = db.query(Entry).filter(
            Entry.contest_id == contest.id,
            Entry.user_id == current_user.id
        ).first()
        
        # Create response with user-specific information
        contest_data = contest.__dict__.copy()
        contest_data['user_has_entered'] = user_entry is not None
        contest_data['user_entry_id'] = user_entry.id if user_entry else None
        
        response_list.append(ContestResponse(**contest_data))
    
    return response_list


@router.get("/contests/upcoming", response_model=List[ContestResponse])
async def get_upcoming_contests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get upcoming contests that haven't started yet"""
    now = utc_now()
    
    contests = db.query(Contest).filter(
        Contest.is_approved == True,  # Only approved contests
        Contest.start_time > now      # Contest hasn't started yet
    ).order_by(Contest.start_time.asc()).all()
    
    response_list = []
    for contest in contests:
        contest_data = contest.__dict__.copy()
        contest_data['user_has_entered'] = False  # Can't enter upcoming contests
        contest_data['user_entry_id'] = None
        
        response_list.append(ContestResponse(**contest_data))
    
    return response_list


@router.post("/contests/{contest_id}/enter", response_model=EntryResponse)
async def enter_contest(
    contest_id: int,
    current_user: User = Depends(get_verified_user),  # Require verified user
    db: Session = Depends(get_db)
):
    """Enter a contest (verified users only)"""
    # Get contest
    contest = db.query(Contest).filter(Contest.id == contest_id).first()
    if not contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found"
        )
    
    # Check if contest is approved
    if not contest.is_approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Contest is not approved for entries"
        )
    
    # Check if contest is active
    now = utc_now()
    if now < contest.start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contest has not started yet"
        )
    
    if now > contest.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contest has ended"
        )
    
    # Check if user has already entered
    existing_entry = db.query(Entry).filter(
        Entry.contest_id == contest_id,
        Entry.user_id == current_user.id
    ).first()
    
    if existing_entry:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already entered this contest"
        )
    
    # Check entry limits
    if contest.max_entries_per_person:
        user_entries_count = db.query(Entry).filter(
            Entry.contest_id == contest_id,
            Entry.user_id == current_user.id
        ).count()
        
        if user_entries_count >= contest.max_entries_per_person:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum entries per person ({contest.max_entries_per_person}) exceeded"
            )
    
    if contest.total_entry_limit:
        total_entries = db.query(Entry).filter(Entry.contest_id == contest_id).count()
        if total_entries >= contest.total_entry_limit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contest has reached maximum entry limit"
            )
    
    # Create entry
    entry = Entry(
        contest_id=contest_id,
        user_id=current_user.id
    )
    
    db.add(entry)
    db.commit()
    db.refresh(entry)
    
    return EntryResponse(
        id=entry.id,
        contest_id=entry.contest_id,
        user_id=entry.user_id,
        created_at=entry.created_at,
        selected=entry.selected,
        status=entry.status
    )


# =====================================================
# USER ENTRY HISTORY
# =====================================================

@router.get("/entries", response_model=List[EntryResponse])
async def get_user_entries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all entries made by the current user"""
    entries = db.query(Entry).options(
        joinedload(Entry.contest)
    ).filter(
        Entry.user_id == current_user.id
    ).order_by(Entry.created_at.desc()).all()
    
    response_list = []
    for entry in entries:
        entry_data = {
            "id": entry.id,
            "contest_id": entry.contest_id,
            "user_id": entry.user_id,
            "created_at": entry.created_at,
            "selected": entry.selected,
            "status": entry.status,
            "contest_name": entry.contest.name if entry.contest else None,
            "contest_end_time": entry.contest.end_time if entry.contest else None,
            "prize_description": entry.contest.prize_description if entry.contest else None
        }
        response_list.append(EntryResponse(**entry_data))
    
    return response_list


@router.get("/entries/active", response_model=List[EntryResponse])
async def get_active_entries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's entries in currently active contests"""
    now = utc_now()
    
    entries = db.query(Entry).options(
        joinedload(Entry.contest)
    ).join(Contest).filter(
        Entry.user_id == current_user.id,
        Contest.is_approved == True,
        Contest.start_time <= now,
        Contest.end_time >= now
    ).order_by(Entry.created_at.desc()).all()
    
    response_list = []
    for entry in entries:
        entry_data = {
            "id": entry.id,
            "contest_id": entry.contest_id,
            "user_id": entry.user_id,
            "created_at": entry.created_at,
            "selected": entry.selected,
            "status": entry.status,
            "contest_name": entry.contest.name if entry.contest else None,
            "contest_end_time": entry.contest.end_time if entry.contest else None,
            "prize_description": entry.contest.prize_description if entry.contest else None
        }
        response_list.append(EntryResponse(**entry_data))
    
    return response_list


@router.get("/entries/won", response_model=List[EntryResponse])
async def get_winning_entries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's winning entries"""
    entries = db.query(Entry).options(
        joinedload(Entry.contest)
    ).filter(
        Entry.user_id == current_user.id,
        Entry.selected == True
    ).order_by(Entry.created_at.desc()).all()
    
    response_list = []
    for entry in entries:
        entry_data = {
            "id": entry.id,
            "contest_id": entry.contest_id,
            "user_id": entry.user_id,
            "created_at": entry.created_at,
            "selected": entry.selected,
            "status": entry.status,
            "contest_name": entry.contest.name if entry.contest else None,
            "contest_end_time": entry.contest.end_time if entry.contest else None,
            "prize_description": entry.contest.prize_description if entry.contest else None
        }
        response_list.append(EntryResponse(**entry_data))
    
    return response_list


# =====================================================
# CONTEST DETAILS FOR USERS
# =====================================================

@router.get("/contests/{contest_id}", response_model=ContestResponse)
async def get_contest_details(
    contest_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific contest"""
    contest = db.query(Contest).filter(Contest.id == contest_id).first()
    
    if not contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found"
        )
    
    # Users can only see approved contests
    if not contest.is_approved:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found"
        )
    
    # Check if user has entered this contest
    user_entry = db.query(Entry).filter(
        Entry.contest_id == contest_id,
        Entry.user_id == current_user.id
    ).first()
    
    # Create response with user-specific information
    contest_data = contest.__dict__.copy()
    contest_data['user_has_entered'] = user_entry is not None
    contest_data['user_entry_id'] = user_entry.id if user_entry else None
    
    return ContestResponse(**contest_data)


# =====================================================
# USER STATISTICS
# =====================================================

@router.get("/stats")
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's participation statistics"""
    # Total entries
    total_entries = db.query(Entry).filter(Entry.user_id == current_user.id).count()
    
    # Winning entries
    winning_entries = db.query(Entry).filter(
        Entry.user_id == current_user.id,
        Entry.selected == True
    ).count()
    
    # Active entries (in ongoing contests)
    now = utc_now()
    active_entries = db.query(Entry).join(Contest).filter(
        Entry.user_id == current_user.id,
        Contest.is_approved == True,
        Contest.start_time <= now,
        Contest.end_time >= now
    ).count()
    
    # Available contests (that user hasn't entered)
    available_contests = db.query(Contest).outerjoin(
        Entry, (Contest.id == Entry.contest_id) & (Entry.user_id == current_user.id)
    ).filter(
        Contest.is_approved == True,
        Contest.start_time <= now,
        Contest.end_time >= now,
        Entry.id.is_(None)  # User hasn't entered
    ).count()
    
    return {
        "user_id": current_user.id,
        "role": current_user.role,
        "is_verified": current_user.is_verified,
        "total_entries": total_entries,
        "winning_entries": winning_entries,
        "active_entries": active_entries,
        "available_contests": available_contests,
        "win_rate": round((winning_entries / total_entries * 100) if total_entries > 0 else 0, 1)
    }
