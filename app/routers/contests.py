"""
Clean, refactored contests API endpoints.
Uses new clean architecture with thin controllers and proper error handling.
"""

from fastapi import APIRouter, Depends, Query, Path, Body, HTTPException, status
from typing import Optional

from app.core.services.contest_service import ContestService
from app.core.dependencies.auth import get_current_user, get_optional_user
from app.core.dependencies.services import get_contest_service
from app.core.admin_auth import get_admin_user
from app.models.user import User
from app.schemas.manual_entry import ManualEntryRequest
from app.shared.types.pagination import PaginationParams, ContestFilterParams
from app.shared.types.responses import APIResponse, PaginatedResponse, PaginationMeta
from app.api.responses.contest import (
    ContestListResponse,
    ContestDetailResponse,
    ContestEntryResponse,
    ContestDeletionResponse,
    NearbyContestsResponse,
    ActiveContestsResponse
)
from app.shared.constants.contest import ContestConstants, ContestMessages
from app.schemas.contest import ContestResponse

router = APIRouter(prefix="/contests", tags=["contests"])


@router.get("/active", response_model=ActiveContestsResponse)
async def get_active_contests(
    pagination: PaginationParams = Depends(),
    filters: ContestFilterParams = Depends(),
    contest_service: ContestService = Depends(get_contest_service)
) -> ActiveContestsResponse:
    """
    Get currently active contests with pagination and filtering.
    Clean controller with single responsibility - delegates to service layer.
    """
    paginated_result = await contest_service.get_active_contests(pagination, filters)
    
    # Convert PaginatedResult to PaginatedResponse
    contest_responses = [ContestResponse.from_orm(contest) for contest in paginated_result.items]
    paginated_response = PaginatedResponse[ContestResponse](
        items=contest_responses,
        pagination=PaginationMeta(
            total=paginated_result.total,
            page=paginated_result.page,
            size=paginated_result.size,
            total_pages=paginated_result.total_pages,
            has_next=paginated_result.has_next,
            has_prev=paginated_result.has_prev
        )
    )
    
    return ActiveContestsResponse(
        success=True,
        data=paginated_response,
        message="Active contests retrieved successfully"
    )


@router.get("/nearby", response_model=NearbyContestsResponse)
async def get_nearby_contests(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lng: float = Query(..., ge=-180, le=180, description="Longitude"),
    radius: float = Query(
        default=ContestConstants.DEFAULT_SEARCH_RADIUS_MILES,
        ge=ContestConstants.MIN_SEARCH_RADIUS,
        le=ContestConstants.MAX_SEARCH_RADIUS,
        description="Search radius in miles"
    ),
    pagination: PaginationParams = Depends(),
    contest_service: ContestService = Depends(get_contest_service)
) -> NearbyContestsResponse:
    """
    Get contests near a specific location.
    Uses constants for validation and clean service delegation.
    """
    contests = await contest_service.get_nearby_contests(
        latitude=lat,
        longitude=lng,
        radius_miles=radius,
        pagination=pagination
    )
    
    return NearbyContestsResponse(
        success=True,
        data=contests,
        message=f"Found {contests.total} contests within {radius} miles"
    )


@router.get("/{contest_id}", response_model=ContestDetailResponse)
async def get_contest_details(
    contest_id: int = Path(..., gt=0, description="Contest ID"),
    current_user: Optional[User] = Depends(get_optional_user),
    contest_service: ContestService = Depends(get_contest_service)
) -> ContestDetailResponse:
    """
    Get public details for a specific contest.
    No authentication required, but user context provided if available.
    """
    contest = await contest_service.get_contest_details(contest_id, current_user)
    
    return ContestDetailResponse(
        success=True,
        data=contest,
        message="Contest details retrieved successfully"
    )


@router.post("/{contest_id}/enter", response_model=ContestEntryResponse)
async def enter_contest(
    contest_id: int = Path(..., gt=0, description="Contest ID"),
    manual_entry_data: Optional[ManualEntryRequest] = Body(None, description="Manual entry data for admin use"),
    current_user: Optional[User] = Depends(get_optional_user),
    contest_service: ContestService = Depends(get_contest_service)
) -> ContestEntryResponse:
    """
    Enter a user into a contest.
    
    - Regular users: Enter themselves (no request body needed)
    - Admins: Can create manual entries with phone_number and admin_override=true
    """
    
    # Check if this is a manual entry request
    if manual_entry_data and manual_entry_data.admin_override:
        # This is an admin manual entry request
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required for manual entry creation"
            )
        
        # Verify admin permissions
        try:
            # Import here to avoid circular imports
            from app.core.repositories.contest_repository import ContestRepository
            from app.core.repositories.entry_repository import EntryRepository
            from app.core.repositories.user_repository import UserRepository
            from app.database.database import get_db
            from sqlalchemy.orm import Session
            
            # Get database session (we need to handle this differently in the endpoint)
            db_gen = get_db()
            db = next(db_gen)
            
            try:
                # Check if user is admin
                if current_user.role not in ["admin", "sponsor"]:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Admin privileges required for manual entry creation"
                    )
                
                # Initialize service with repositories
                contest_repo = ContestRepository(db)
                entry_repo = EntryRepository(db)
                user_repo = UserRepository(db)
                manual_contest_service = ContestService(contest_repo, entry_repo, user_repo, db)
                
                # Create manual entry
                entry = await manual_contest_service.create_manual_entry(
                    contest_id=contest_id,
                    phone_number=manual_entry_data.phone_number,
                    admin_user_id=current_user.id,
                    source=manual_entry_data.source,
                    notes=manual_entry_data.notes
                )
                
                # Load user relationship for response
                db.refresh(entry)
                
                return ContestEntryResponse(
                    success=True,
                    message="Manual entry created successfully",
                    contest_id=contest_id,
                    entry_id=entry.id,
                    user_id=entry.user_id,
                    entered_at=entry.created_at
                )
                
            finally:
                db.close()
                
        except HTTPException:
            raise
        except Exception as e:
            if "already entered" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Phone number {manual_entry_data.phone_number} has already entered this contest"
                )
            elif "not found" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=str(e)
                )
            elif "limit" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to create manual entry: {str(e)}"
                )
    
    else:
        # Regular user entry
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        entry = await contest_service.enter_contest(contest_id, current_user.id)
        
        return ContestEntryResponse(
            success=True,
            message=ContestMessages.ENTRY_SUCCESSFUL,
            contest_id=contest_id,
            entry_id=entry.id,
            user_id=current_user.id,
            entered_at=entry.created_at
        )


@router.delete("/{contest_id}", response_model=ContestDeletionResponse)
async def delete_contest(
    contest_id: int = Path(..., gt=0, description="Contest ID"),
    current_user: User = Depends(get_current_user),
    contest_service: ContestService = Depends(get_contest_service)
) -> ContestDeletionResponse:
    """
    Delete a contest with proper authorization and business rules.
    Clean delegation to service layer for all business logic.
    """
    deletion_result = await contest_service.delete_contest(
        contest_id=contest_id,
        user_id=current_user.id,
        user_role=current_user.role
    )
    
    return ContestDeletionResponse(
        success=True,
        message=ContestMessages.DELETED_SUCCESSFULLY,
        contest_id=contest_id,
        contest_name=deletion_result.contest_name,
        deleted_at=deletion_result.deleted_at,
        deleted_by={
            "user_id": current_user.id,
            "role": current_user.role
        },
        cleanup_summary=deletion_result.cleanup_summary
    )
