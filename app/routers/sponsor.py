"""
Sponsor Contest Management Endpoints

This router provides the `/sponsor/contests/` endpoint that the frontend expects.
It allows sponsors to view and manage their own contests with proper pagination,
filtering, and authentication.
"""

from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from app.database.database import get_db
from app.models.user import User
from app.models.contest import Contest
from app.core.dependencies.auth import get_admin_or_sponsor_user
from app.shared.types.responses import APIResponse, PaginatedResponse, PaginationMeta
from app.schemas.contest import ContestResponse
from app.api.responses.contest import ContestListResponse, ContestDetailResponse
from datetime import datetime

router = APIRouter(prefix="/sponsor", tags=["sponsor"])


@router.get("/contests/", response_model=ContestListResponse)
async def get_sponsor_contests(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    sort: str = Query("end_time", description="Sort field"),
    order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    status: Optional[str] = Query(None, description="Filter by contest status"),
    current_user: User = Depends(get_admin_or_sponsor_user),
    db: Session = Depends(get_db)
) -> ContestListResponse:
    """
    Get contests created by the authenticated sponsor.
    
    - **Authentication**: Requires sponsor or admin role
    - **Scope**: Returns only contests created by the authenticated sponsor (admins can see all)
    - **Pagination**: Supports page-based pagination
    - **Sorting**: Supports sorting by various fields
    - **Filtering**: Supports filtering by contest status
    """
    
    # Build base query with eager loading
    query = db.query(Contest).options(
        joinedload(Contest.sponsor_profile),
        joinedload(Contest.entries)
    )
    
    # Filter by sponsor (sponsors only see their own, admins see all)
    if current_user.role != "admin":
        query = query.filter(Contest.created_by_user_id == current_user.id)
    
    # Apply status filter if provided
    if status:
        query = query.filter(Contest.status == status)
    
    # Apply sorting
    sort_field = getattr(Contest, sort, Contest.end_time)
    if order == "desc":
        query = query.order_by(sort_field.desc())
    else:
        query = query.order_by(sort_field.asc())
    
    # Get total count for pagination
    total_items = query.count()
    
    # Apply pagination
    offset = (page - 1) * size
    contests = query.offset(offset).limit(size).all()
    
    # Convert to response format
    contest_responses = []
    for contest in contests:
        # Populate sponsor_name from sponsor_profile
        sponsor_name = None
        if contest.sponsor_profile and contest.sponsor_profile.company_name:
            sponsor_name = contest.sponsor_profile.company_name
        
        # Create response object
        contest_data = ContestResponse(
            id=contest.id,
            name=contest.name,
            description=contest.description,
            start_time=contest.start_time,
            end_time=contest.end_time,
            prize_description=contest.prize_description,
            location=contest.location,
            image_url=contest.image_url,
            sponsor_url=contest.sponsor_url,
            sponsor_name=sponsor_name,
            sponsor_profile_id=contest.sponsor_profile_id,
            is_approved=contest.approved_at is not None,  # Computed from approved_at
            approved_by_user_id=contest.approved_by_user_id,
            approved_at=contest.approved_at,
            created_by_user_id=contest.created_by_user_id,
            created_at=contest.created_at,
            updated_at=contest.created_at,  # Contest model doesn't have updated_at
            status=contest.status,
            entry_count=len(contest.entries) if contest.entries else 0,
            # Location targeting fields (using correct field names)
            location_type=contest.location_type or "united_states",
            selected_states=contest.selected_states,
            radius_address=contest.radius_address,
            radius_miles=contest.radius_miles,
            radius_latitude=contest.radius_latitude,
            radius_longitude=contest.radius_longitude
        )
        contest_responses.append(contest_data)
    
    # Calculate pagination metadata
    total_pages = (total_items + size - 1) // size
    has_next = page < total_pages
    has_previous = page > 1
    
    # Create pagination metadata
    pagination_meta = PaginationMeta(
        total=total_items,
        page=page,
        size=size,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_previous
    )
    
    # Create paginated response
    paginated_data = PaginatedResponse(
        items=contest_responses,
        pagination=pagination_meta
    )
    
    return APIResponse(
        success=True,
        data=paginated_data,
        message=f"Retrieved {len(contest_responses)} contests for sponsor"
    )


@router.get("/contests/{contest_id}", response_model=ContestDetailResponse)
async def get_sponsor_contest_detail(
    contest_id: int = Path(..., gt=0, description="Contest ID"),
    current_user: User = Depends(get_admin_or_sponsor_user),
    db: Session = Depends(get_db)
) -> ContestDetailResponse:
    """
    Get detailed information about a specific contest.
    
    - **Authentication**: Requires sponsor or admin role
    - **Authorization**: Sponsors can only view their own contests, admins can view all
    """
    
    # Query contest with eager loading
    query = db.query(Contest).options(
        joinedload(Contest.sponsor_profile),
        joinedload(Contest.entries)
    ).filter(Contest.id == contest_id)
    
    # Apply ownership filter for sponsors
    if current_user.role != "admin":
        query = query.filter(Contest.created_by_user_id == current_user.id)
    
    contest = query.first()
    
    if not contest:
        return APIResponse(
            success=False,
            data=None,
            message="Contest not found or access denied"
        )
    
    # Populate sponsor_name from sponsor_profile
    sponsor_name = None
    if contest.sponsor_profile and contest.sponsor_profile.company_name:
        sponsor_name = contest.sponsor_profile.company_name
    
    # Create response object
    contest_data = ContestResponse(
        id=contest.id,
        name=contest.name,
        description=contest.description,
        start_time=contest.start_time,
        end_time=contest.end_time,
        prize_description=contest.prize_description,
        location=contest.location,
        image_url=contest.image_url,
        sponsor_url=contest.sponsor_url,
        sponsor_name=sponsor_name,
        sponsor_profile_id=contest.sponsor_profile_id,
        is_approved=contest.approved_at is not None,  # Computed from approved_at
        approved_by_user_id=contest.approved_by_user_id,
        approved_at=contest.approved_at,
        created_by_user_id=contest.created_by_user_id,
        created_at=contest.created_at,
        updated_at=contest.created_at,  # Contest model doesn't have updated_at
        status=contest.status,
        entry_count=len(contest.entries) if contest.entries else 0,
        # Location targeting fields (using correct field names)
        location_type=contest.location_type or "united_states",
        selected_states=contest.selected_states,
        radius_address=contest.radius_address,
        radius_miles=contest.radius_miles,
        radius_latitude=contest.radius_latitude,
        radius_longitude=contest.radius_longitude
    )
    
    return APIResponse(
        success=True,
        data=contest_data,
        message="Contest details retrieved successfully"
    )
