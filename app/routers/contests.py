from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from typing import Optional, List
from app.database.database import get_db
from app.models.user import User
from app.models.contest import Contest
from app.models.entry import Entry
from app.schemas.contest import ContestResponse, ContestListResponse
from app.schemas.entry import EntryResponse
from app.core.dependencies import get_current_user
from app.core.geolocation import haversine_distance, validate_coordinates

router = APIRouter(prefix="/contests", tags=["contests"])


@router.get("/active", response_model=ContestListResponse)
async def get_active_contests(
    location: Optional[str] = Query(None, description="Filter by location"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db)
):
    """Get list of currently active contests with optional location filtering"""
    from app.core.datetime_utils import utc_now
    current_time = utc_now()
    
    # Base query for currently active contests (time-based, no winner selected)
    query = db.query(Contest).filter(
        and_(
            Contest.start_time <= current_time,
            Contest.end_time > current_time,
            Contest.winner_selected_at.is_(None)  # No winner selected yet
        )
    )
    
    # Apply location filter if provided
    if location:
        query = query.filter(Contest.location.ilike(f"%{location}%"))
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    contests = query.offset((page - 1) * size).limit(size).all()
    
    return ContestListResponse(
        contests=contests,
        total=total,
        page=page,
        size=size
    )


@router.get("/nearby", response_model=ContestListResponse)
async def get_nearby_contests(
    lat: float = Query(..., description="Latitude of user location"),
    lng: float = Query(..., description="Longitude of user location"),
    radius: float = Query(25.0, ge=0.1, le=100, description="Search radius in miles (default: 25)"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db)
):
    """Get contests near a specific location within the given radius"""
    
    # Validate coordinates
    if not validate_coordinates(lat, lng):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid latitude or longitude coordinates"
        )
    
    from app.core.datetime_utils import utc_now
    current_time = utc_now()
    
    # Get all currently active contests with geolocation data (time-based, no winner selected)
    base_query = db.query(Contest).filter(
        and_(
            Contest.start_time <= current_time,
            Contest.end_time > current_time,
            Contest.winner_selected_at.is_(None),  # No winner selected yet
            Contest.latitude.isnot(None),
            Contest.longitude.isnot(None)
        )
    )
    
    # Get all contests first to calculate distances
    all_contests = base_query.all()
    
    # Filter contests within radius and calculate distances
    nearby_contests = []
    for contest in all_contests:
        distance = haversine_distance(lat, lng, contest.latitude, contest.longitude)
        if distance <= radius:
            # Create response object with distance
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
                "active": contest.active,
                "created_at": contest.created_at,
                "distance_miles": round(distance, 2)
            }
            nearby_contests.append(contest_dict)
    
    # Sort by distance
    nearby_contests.sort(key=lambda x: x["distance_miles"])
    
    # Apply pagination
    total = len(nearby_contests)
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    paginated_contests = nearby_contests[start_idx:end_idx]
    
    # Convert to ContestResponse objects
    contest_responses = [ContestResponse(**contest) for contest in paginated_contests]
    
    return ContestListResponse(
        contests=contest_responses,
        total=total,
        page=page,
        size=size
    )


@router.post("/{contest_id}/enter", response_model=EntryResponse)
async def enter_contest(
    contest_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Enter the current user into a contest"""
    # Check if contest exists
    contest = db.query(Contest).filter(Contest.id == contest_id).first()
    if not contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found"
        )
    
    # Check if contest is currently accepting entries (time-based check)
    from app.core.datetime_utils import utc_now
    current_time = utc_now()
    
    if current_time < contest.start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contest has not started yet"
        )
    
    if current_time >= contest.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contest has ended"
        )
    
    # Check if winner already selected (contest complete)
    if contest.winner_selected_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contest is complete - winner already selected"
        )
    
    # Check if user has already entered this contest (prevent duplicates)
    existing_entry = db.query(Entry).filter(
        and_(
            Entry.user_id == current_user.id,
            Entry.contest_id == contest_id
        )
    ).first()
    
    if existing_entry:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already entered this contest. Duplicate entries are not allowed."
        )
    
    # Create new entry
    entry = Entry(
        user_id=current_user.id,
        contest_id=contest_id
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    
    # Load the contest relationship for response
    db.refresh(entry)
    
    return entry
