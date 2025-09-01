"""
Clean, refactored contests API endpoints.
Uses new clean architecture with thin controllers and proper error handling.
"""

from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session
from typing import Optional

from app.core.services.contest_service import ContestService
from app.database.database import get_db
from app.core.dependencies.auth import get_current_user, get_optional_user
from app.core.dependencies.services import get_contest_service
from app.models.user import User
from app.shared.types.pagination import PaginationParams, ContestFilterParams
from app.shared.types.responses import APIResponse
from app.api.responses.contest import (
    ContestListResponse,
    ContestDetailResponse,
    ContestEntryResponse,
    ContestDeletionResponse,
    NearbyContestsResponse,
    ActiveContestsResponse
)
from app.shared.constants.contest import ContestConstants, ContestMessages
from app.shared.exceptions.base import raise_not_found, raise_validation_error

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
    
    # Base query for currently active contests using enhanced status system
    # Get published contests and filter by calculated status
    query = db.query(Contest).filter(
        Contest.status.in_(["upcoming", "active", "ended"]),  # Published contests
        Contest.start_time <= current_time,  # Started
        Contest.end_time > current_time      # Not ended yet
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
        # Use enhanced status system - calculate current status
        status = calculate_contest_status(
            contest.status,
            contest.start_time,
            contest.end_time,
            contest.winner_selected_at,
            current_time
        )
        
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
    
    # Get all currently active contests with geolocation data using enhanced status
    base_query = db.query(Contest).filter(
        and_(
            Contest.status == "active",  # Enhanced status system
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
    
    # Use enhanced status system - calculate current status
    current_time = utc_now()
    status = calculate_contest_status(
        contest.status,
        contest.start_time,
        contest.end_time,
        contest.winner_selected_at,
        current_time
    )
    
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
        'is_active': status == 'active',
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
    
    # Check if contest is currently accepting entries using enhanced status system
    from app.core.datetime_utils import utc_now
    from app.core.contest_status import can_enter_contest
    
    current_time = utc_now()
    
    # Calculate current contest status
    current_status = calculate_contest_status(
        contest.status,
        contest.start_time,
        contest.end_time,
        contest.winner_selected_at,
        current_time
    )
    
    # Check if entries are allowed based on status
    if not can_enter_contest(current_status):
        status_messages = {
            "draft": "Contest is still in draft mode",
            "awaiting_approval": "Contest is awaiting admin approval",
            "rejected": "Contest has been rejected",
            "upcoming": "Contest has not started yet",
            "ended": "Contest has ended",
            "complete": "Contest is complete - winner already selected",
            "cancelled": "Contest has been cancelled"
        }
        
        message = status_messages.get(current_status, f"Contest is not accepting entries (status: {current_status})")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
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


@router.delete("/{contest_id}")
async def delete_contest(
    contest_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    🗑️ Unified Contest Deletion API with Built-in Protection Logic
    
    **Features:**
    - ✅ Role-based access (admin can delete any, sponsors can delete own)
    - ✅ Built-in protection logic (no frontend duplication)
    - ✅ Clear error responses with specific reasons
    - ✅ Proper CORS headers
    - ✅ Consistent response format
    
    **Protection Rules:**
    - 🚫 CANNOT DELETE: Active contests, contests with entries, completed contests
    - ✅ CAN DELETE: Upcoming contests with no entries, ended contests with no entries
    """
    
    # Extract and validate JWT token
    from app.core.auth import jwt_manager
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    payload = jwt_manager.verify_token(credentials.credentials, "access")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user_role = payload.get("role")
    user_id = int(payload.get("sub"))
    
    # Validate user role - only admin and sponsor can delete contests
    if user_role not in ["admin", "sponsor"]:
        return {
            "success": False,
            "error": "INSUFFICIENT_PERMISSIONS",
            "message": "Only admin and sponsor users can delete contests",
            "contest_id": contest_id,
            "user_role": user_role
        }
    
    # Get contest with related data
    contest = db.query(Contest).filter(Contest.id == contest_id).first()
    
    if not contest:
        return {
            "success": False,
            "error": "CONTEST_NOT_FOUND",
            "message": "Contest not found or not accessible",
            "contest_id": contest_id
        }
    
    # Permission validation: sponsors can only delete their own contests
    if user_role == "sponsor" and contest.created_by_user_id != user_id:
        return {
            "success": False,
            "error": "INSUFFICIENT_PERMISSIONS",
            "message": "You do not have permission to delete this contest",
            "contest_id": contest_id,
            "user_role": user_role,
            "contest_owner": contest.created_by_user_id
        }
    
    # Use enhanced contest status system
    from app.core.contest_status import calculate_contest_status
    now = utc_now()
    
    # Get the actual contest status using enhanced status system
    contest_status = calculate_contest_status(
        current_status=contest.status,
        start_time=contest.start_time,
        end_time=contest.end_time,
        winner_selected_at=contest.winner_selected_at,
        now=now
    )
    
    # Get entry count
    entry_count = db.query(Entry).filter(Entry.contest_id == contest_id).count()
    
    # Determine if contest is complete (has winner selected)
    is_complete = contest.winner_entry_id is not None
    
    # Apply enhanced status system protection rules
    from app.core.contest_status import can_delete_contest
    protection_errors = []
    
    # Use enhanced status system to check if contest can be deleted
    can_delete = can_delete_contest(
        status=contest_status,
        user_role=user_role,
        is_creator=(contest.created_by_user_id == user_id),
        has_entries=(entry_count > 0)
    )
    
    if not can_delete:
        # Determine specific protection reasons
        if contest_status == "active":
            protection_errors.append("Contest is currently active and accepting entries")
        elif contest_status == "complete":
            protection_errors.append("Contest is complete and archived")
        elif entry_count > 0:
            protection_errors.append(f"Contest has {entry_count} entries and cannot be deleted")
        else:
            protection_errors.append(f"Contest with status '{contest_status}' cannot be deleted")
    
    # If there are protection errors, return detailed error response
    if protection_errors:
        primary_reason = protection_errors[0]
        
        # Determine protection reason code using enhanced status
        if contest_status == "active":
            protection_reason = "active_contest"
        elif entry_count > 0:
            protection_reason = "has_entries"
        elif contest_status == "complete":
            protection_reason = "contest_complete"
        else:
            protection_reason = "protected"
        
        return {
            "success": False,
            "error": "CONTEST_PROTECTED",
            "message": f"Contest cannot be deleted: {primary_reason}",
            "contest_id": contest_id,
            "contest_name": contest.name,
            "protection_reason": protection_reason,
            "protection_errors": protection_errors,
            "details": {
                "is_active": contest_status == "active",
                "entry_count": entry_count,
                "start_time": contest.start_time.isoformat() if contest.start_time else None,
                "end_time": contest.end_time.isoformat() if contest.end_time else None,
                "status": contest_status,
                "enhanced_status": contest_status,
                "is_complete": contest_status == "complete",
                "winner_selected": contest.winner_selected_at.isoformat() if contest.winner_selected_at else None,
                "is_draft": contest_status == "draft",
                "is_awaiting_approval": contest_status == "awaiting_approval",
                "is_rejected": contest_status == "rejected",
                "is_published": contest_status in ["upcoming", "active", "ended", "complete"]
            }
        }
    
    # Contest can be safely deleted - perform deletion with cleanup
    try:
        # Track what we're deleting for the summary
        cleanup_summary = {
            "entries_deleted": 0,
            "notifications_deleted": 0,
            "official_rules_deleted": 0,
            "sms_templates_deleted": 0,
            "media_deleted": False,
            "dependencies_cleared": 0
        }
        
        # Delete related SMS templates
        from app.models.sms_template import SMSTemplate
        sms_count = db.query(SMSTemplate).filter(SMSTemplate.contest_id == contest_id).count()
        db.query(SMSTemplate).filter(SMSTemplate.contest_id == contest_id).delete()
        cleanup_summary["sms_templates_deleted"] = sms_count
        cleanup_summary["dependencies_cleared"] += sms_count
        
        # Delete official rules
        from app.models.official_rules import OfficialRules
        rules_count = db.query(OfficialRules).filter(OfficialRules.contest_id == contest_id).count()
        db.query(OfficialRules).filter(OfficialRules.contest_id == contest_id).delete()
        cleanup_summary["official_rules_deleted"] = rules_count
        cleanup_summary["dependencies_cleared"] += rules_count
        
        # Delete notifications (if any)
        from app.models.notification import Notification
        notification_count = db.query(Notification).filter(Notification.contest_id == contest_id).count()
        db.query(Notification).filter(Notification.contest_id == contest_id).delete()
        cleanup_summary["notifications_deleted"] = notification_count
        cleanup_summary["dependencies_cleared"] += notification_count
        
        # Delete contest approval audit records
        try:
            from app.models.role_audit import ContestApprovalAudit
            audit_count = db.query(ContestApprovalAudit).filter(ContestApprovalAudit.contest_id == contest_id).count()
            db.query(ContestApprovalAudit).filter(ContestApprovalAudit.contest_id == contest_id).delete()
            cleanup_summary["dependencies_cleared"] += audit_count
        except Exception as e:
            logger.warning(f"Could not delete approval audit records for contest {contest_id}: {e}")
        
        # Delete media from Cloudinary if it exists
        if contest.image_public_id:
            try:
                from app.services.media_service import MediaService
                media_service = MediaService()
                if media_service.enabled:
                    deletion_success = await media_service.delete_contest_hero(contest_id)
                    cleanup_summary["media_deleted"] = deletion_success
            except Exception as e:
                logger.warning(f"Could not delete media for contest {contest_id}: {e}")
        
        # Store contest info for response before deletion
        contest_name = contest.name
        deleted_at = utc_now()
        
        # Finally, delete the contest itself
        db.delete(contest)
        db.commit()
        
        logger.info(f"Successfully deleted contest {contest_id} ({contest_name}) by user {user_id} ({user_role})")
        
        return {
            "success": True,
            "message": "Contest deleted successfully",
            "contest_id": contest_id,
            "contest_name": contest_name,
            "deleted_at": deleted_at.isoformat(),
            "deleted_by": {
                "user_id": user_id,
                "role": user_role
            },
            "cleanup_summary": cleanup_summary
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete contest {contest_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete contest: {str(e)}"
        )
