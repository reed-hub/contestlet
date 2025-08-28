"""
Location API endpoints for contest geographic targeting
"""

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import Optional
import httpx
import asyncio

from app.database.database import get_db
from app.core.admin_auth import get_admin_user
from app.schemas.location import (
    LocationValidationRequest, LocationValidationResponse,
    GeocodeRequest, GeocodeResponse,
    EligibilityCheckRequest, EligibilityCheckResponse,
    ContestLocation, UserLocation, GeoCoordinates
)
from app.core.location_utils import (
    validate_contest_location, 
    check_contest_eligibility,
    format_location_display
)
from app.services.geocoding_service import geocoding_service
from app.models.contest import Contest

router = APIRouter(prefix="/location", tags=["location"])

@router.post("/validate", response_model=LocationValidationResponse)
async def validate_location(
    request: LocationValidationRequest,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    🔍 Validate contest location data
    
    Validates location targeting configuration including:
    - State code validation for specific_states type
    - Radius and coordinate validation for radius type
    - Required field validation for each location type
    
    **Admin Authentication Required**
    """
    try:
        location = request.location_data
        
        # Validate the location data
        is_valid, errors, warnings = validate_contest_location(location)
        
        # If valid, return processed location with generated display text
        processed_location = None
        if is_valid:
            # Ensure display_text is properly generated
            if not location.display_text or not location.display_text.strip():
                location.display_text = format_location_display(location)
            processed_location = location
        
        return LocationValidationResponse(
            valid=is_valid,
            errors=errors,
            warnings=warnings,
            processed_location=processed_location
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Location validation failed: {str(e)}"
        )

@router.post("/geocode", response_model=GeocodeResponse)
async def geocode_address(
    request: GeocodeRequest,
    admin_user: dict = Depends(get_admin_user)
):
    """
    🌍 Geocode an address to coordinates
    
    Uses OpenStreetMap Nominatim service to convert addresses to coordinates.
    This is used for radius-based contest targeting.
    
    **Features:**
    - Free geocoding service (no API key required)
    - Returns formatted address and coordinates
    - Comprehensive error handling and validation
    
    **Admin Authentication Required**
    """
    try:
        # Use the geocoding service for consistent handling
        result = await geocoding_service.geocode_address(request.address)
        
        if result["success"]:
            return GeocodeResponse(
                success=True,
                coordinates=GeoCoordinates(
                    latitude=result["coordinates"]["latitude"],
                    longitude=result["coordinates"]["longitude"]
                ),
                formatted_address=result["formatted_address"]
            )
        else:
            return GeocodeResponse(
                success=False,
                error_message=result.get("message", "Address not found")
            )
    
    except HTTPException as e:
        # Convert HTTPException to GeocodeResponse for consistent API
        return GeocodeResponse(
            success=False,
            error_message=e.detail
        )
    except Exception as e:
        return GeocodeResponse(
            success=False,
            error_message=f"Geocoding failed: {str(e)}"
        )

@router.post("/check-eligibility", response_model=EligibilityCheckResponse)
async def check_eligibility(
    request: EligibilityCheckRequest,
    db: Session = Depends(get_db)
):
    """
    ✅ Check contest eligibility based on location
    
    Determines if a user is eligible for a contest based on:
    - Contest location restrictions
    - User's provided location data
    
    **Location Types Supported:**
    - `united_states`: Open to all US residents
    - `specific_states`: Restricted to specific states
    - `radius`: Within specified miles of contest location
    - `custom`: Custom restrictions (manual review)
    
    **No Authentication Required** (public endpoint for contest entry)
    """
    try:
        # Get contest from database
        contest = db.query(Contest).filter(Contest.id == request.contest_id).first()
        
        if not contest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contest not found"
            )
        
        # Build ContestLocation from contest data
        contest_location = ContestLocation(
            location_type=contest.location_type or "united_states",
            selected_states=contest.selected_states,
            radius_address=contest.radius_address,
            radius_miles=contest.radius_miles,
            radius_coordinates=GeoCoordinates(
                latitude=contest.radius_latitude,
                longitude=contest.radius_longitude
            ) if contest.radius_latitude and contest.radius_longitude else None,
            custom_text=contest.location if contest.location_type == "custom" else None,
            display_text=contest.location or "Location restrictions apply"
        )
        
        # Check eligibility
        is_eligible, reason = await check_contest_eligibility(
            contest_location, 
            request.user_location
        )
        
        return EligibilityCheckResponse(
            eligible=is_eligible,
            reason=reason,
            location_requirements=format_location_display(contest_location)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Eligibility check failed: {str(e)}"
        )

@router.get("/states")
async def get_valid_states():
    """
    📋 Get list of valid US state codes and names
    
    Returns all valid US state codes and their full names for use in
    state-specific contest targeting.
    
    **No Authentication Required** (public reference data)
    """
    from app.schemas.location import VALID_STATE_CODES
    
    states = [
        {"code": code, "name": name}
        for code, name in VALID_STATE_CODES.items()
    ]
    
    # Sort by state name for better UX
    states.sort(key=lambda x: x["name"])
    
    return {
        "states": states,
        "total": len(states)
    }

@router.get("/contest/{contest_id}/location", response_model=ContestLocation)
async def get_contest_location(
    contest_id: int,
    db: Session = Depends(get_db)
):
    """
    📍 Get contest location configuration
    
    Returns the complete location targeting configuration for a contest.
    
    **No Authentication Required** (public contest information)
    """
    try:
        contest = db.query(Contest).filter(Contest.id == contest_id).first()
        
        if not contest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contest not found"
            )
        
        # Build ContestLocation from contest data
        contest_location = ContestLocation(
            location_type=contest.location_type or "united_states",
            selected_states=contest.selected_states,
            radius_address=contest.radius_address,
            radius_miles=contest.radius_miles,
            radius_coordinates=GeoCoordinates(
                latitude=contest.radius_latitude,
                longitude=contest.radius_longitude
            ) if contest.radius_latitude and contest.radius_longitude else None,
            custom_text=contest.location if contest.location_type == "custom" else None,
            display_text=contest.location or format_location_display(ContestLocation(
                location_type=contest.location_type or "united_states",
                selected_states=contest.selected_states,
                radius_miles=contest.radius_miles,
                custom_text=contest.location
            ))
        )
        
        return contest_location
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get contest location: {str(e)}"
        )
