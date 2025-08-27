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
    
    # Calculate total pages
    total_pages = (total + size - 1) // size if total > 0 else 1
    
    # Convert contests to response format
    contest_responses = []
    for contest in contests:
        # Compute status based on current time
        now = datetime.utcnow()
        if contest.start_time > now:
            status = "upcoming"
        elif contest.end_time <= now:
            status = "ended"
        else:
            status = "active"
        
        # Create a simple dict for the response with only existing fields
        contest_dict = {
            'id': contest.id,
            'name': contest.name,
            'description': contest.description,
            'location': contest.location,
            'latitude': contest.latitude,
            'longitude': contest.longitude,
            'start_time': contest.start_time,
            'end_time': contest.end_time,
            'prize_description': contest.prize_description,
            'winner_selection_method': contest.winner_selection_method,
            'contest_type': contest.contest_type,
            'entry_method': contest.entry_method,
            'active': contest.active,
            'minimum_age': contest.minimum_age,
            'max_entries_per_person': contest.max_entries_per_person,
            'total_entry_limit': contest.total_entry_limit,
            'consolation_offer': contest.consolation_offer,
            'geographic_restrictions': contest.geographic_restrictions,
            'contest_tags': contest.contest_tags,
            'promotion_channels': contest.promotion_channels,
            'image_url': contest.image_url,
            'sponsor_url': contest.sponsor_url,
            'created_by_user_id': contest.created_by_user_id,
            'sponsor_profile_id': contest.sponsor_profile_id,
            'is_approved': contest.is_approved,
            'approved_by_user_id': contest.approved_by_user_id,
            'approved_at': contest.approved_at,
            'location_type': contest.location_type or "united_states",
            'selected_states': contest.selected_states,
            'radius_address': contest.radius_address,
            'radius_miles': contest.radius_miles,
            'radius_latitude': contest.radius_latitude,
            'radius_longitude': contest.radius_longitude,
            'created_at': contest.created_at,
            'updated_at': getattr(contest, 'updated_at', None),
            'status': status,
            'entry_count': len(contest.entries) if contest.entries else 0,
            'is_winner_selected': contest.winner_entry_id is not None,
            # Add missing fields that the schema expects
            'prize_value': None,  # Not in model, set to None
            'distance_miles': None  # Not applicable for this endpoint
        }
        contest_responses.append(contest_dict)
    
    return ContestListResponse(
        contests=contest_responses,
        total=total,
        page=page,
        size=size,
        total_pages=total_pages
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


@router.get("/{contest_id}", response_model=ContestResponse)
async def get_contest_details(
    contest_id: int,
    db: Session = Depends(get_db)
):
    """Get public details for a specific contest (no authentication required)"""
    # Get contest with all basic details
    contest = db.query(Contest).filter(Contest.id == contest_id).first()
    
    if not contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found"
        )
    
    # Compute status based on current time
    now = datetime.utcnow()
    if contest.start_time > now:
        status = "upcoming"
    elif contest.end_time <= now:
        status = "ended"
    else:
        status = "active"
    
    # Return contest details for public viewing with computed fields
    # Note: This endpoint is public and doesn't require authentication
    # It returns contest information suitable for public display
    contest_dict = {
        'id': contest.id,
        'name': contest.name,
        'description': contest.description,
        'location': contest.location,
        'latitude': contest.latitude,
        'longitude': contest.longitude,
        'start_time': contest.start_time,
        'end_time': contest.end_time,
        'prize_description': contest.prize_description,
        'active': contest.active,
        'created_at': contest.created_at,
        'status': status,
        'entry_count': len(contest.entries) if contest.entries else 0,
        'is_winner_selected': contest.winner_entry_id is not None,
        'prize_value': None,  # Not in model for public endpoint
        'distance_miles': None  # Not applicable for this endpoint
    }
    
    return ContestResponse(**contest_dict)


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
    from datetime import timezone
    current_time = utc_now()
    
    # Ensure contest times are timezone-aware for comparison
    contest_start = contest.start_time
    contest_end = contest.end_time
    
    if contest_start.tzinfo is None:
        contest_start = contest_start.replace(tzinfo=timezone.utc)
    if contest_end.tzinfo is None:
        contest_end = contest_end.replace(tzinfo=timezone.utc)
    
    if current_time < contest_start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contest has not started yet"
        )
    
    if current_time >= contest_end:
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
    
    # Phase 1: Advanced entry validation based on contest configuration
    
    # Check maximum entries per person
    if contest.max_entries_per_person:
        user_entry_count = db.query(Entry).filter(
            and_(
                Entry.contest_id == contest.id,
                Entry.user_id == current_user.id
            )
        ).count()
        
        if user_entry_count >= contest.max_entries_per_person:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum {contest.max_entries_per_person} entries per person allowed"
            )
    
    # Check total entry limit for contest
    if contest.total_entry_limit:
        total_entries = db.query(Entry).filter(Entry.contest_id == contest.id).count()
        if total_entries >= contest.total_entry_limit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contest has reached maximum entry limit"
            )
    
    # Note: Age validation would require user birth_date field
    # This can be implemented when user profiles are extended
    # if contest.minimum_age > 18 and user.birth_date:
    #     age = calculate_age(user.birth_date)
    #     if age < contest.minimum_age:
    #         raise HTTPException(400, f"Must be at least {contest.minimum_age} years old")
    
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
