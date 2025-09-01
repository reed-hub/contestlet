"""
Clean, refactored location API endpoints.
Uses new clean architecture with constants, service layer, and proper error handling.
"""

from fastapi import APIRouter, Depends, Path, Query
from typing import Optional

from app.core.services.location_service import LocationService
from app.core.dependencies.auth import get_admin_user, get_admin_or_sponsor_user, get_optional_user
from app.core.dependencies.services import get_location_service
from app.models.user import User
from app.shared.types.responses import APIResponse
from app.api.responses.location import (
    LocationValidationResponse,
    GeocodeResponse,
    EligibilityCheckResponse,
    StatesListResponse,
    ContestLocationResponse
)
from app.schemas.location import (
    LocationValidationRequest,
    GeocodeRequest,
    EligibilityCheckRequest,
    ContestLocation
)
from app.shared.constants.location import LocationConstants, LocationMessages
from app.shared.exceptions.base import ValidationException

router = APIRouter(prefix="/location", tags=["location"])


@router.post("/validate", response_model=LocationValidationResponse)
async def validate_location(
    request: LocationValidationRequest,
    admin_user: User = Depends(get_admin_user),
    location_service: LocationService = Depends(get_location_service)
) -> LocationValidationResponse:
    """
    Validate contest location data with proper error handling.
    Clean controller with service delegation and constants.
    """
    validation_result = await location_service.validate_contest_location(
        location_data=request.location_data
    )
    
    return LocationValidationResponse(
        success=True,
        data=validation_result,
        message=LocationMessages.VALIDATION_SUCCESS if validation_result.valid else LocationMessages.VALIDATION_FAILED
    )


@router.post("/geocode", response_model=GeocodeResponse)
async def geocode_address(
    request: GeocodeRequest,
    current_user: User = Depends(get_admin_or_sponsor_user),
    location_service: LocationService = Depends(get_location_service)
) -> GeocodeResponse:
    """
    Geocode an address to coordinates.
    Uses service layer with proper authentication and error handling.
    """
    # Validate address length
    if len(request.address.strip()) < LocationConstants.MIN_ADDRESS_LENGTH:
        raise ValidationException(
            message=LocationMessages.INVALID_ADDRESS,
            field_errors={"address": f"Address must be at least {LocationConstants.MIN_ADDRESS_LENGTH} characters"}
        )
    
    geocode_result = await location_service.geocode_address(request.address)
    
    return GeocodeResponse(
        success=True,
        data=geocode_result,
        message=LocationMessages.GEOCODING_SUCCESS if geocode_result.success else LocationMessages.GEOCODING_FAILED
    )


@router.post("/check-eligibility", response_model=EligibilityCheckResponse)
async def check_eligibility(
    request: EligibilityCheckRequest,
    location_service: LocationService = Depends(get_location_service)
) -> EligibilityCheckResponse:
    """
    Check contest eligibility based on location.
    Public endpoint with clean service delegation.
    """
    eligibility_result = await location_service.check_contest_eligibility(
        contest_id=request.contest_id,
        user_location=request.user_location
    )
    
    return EligibilityCheckResponse(
        success=True,
        data=eligibility_result,
        message=LocationMessages.ELIGIBILITY_CHECKED
    )


@router.get("/states", response_model=StatesListResponse)
async def get_valid_states() -> StatesListResponse:
    """
    Get list of valid US state codes and names.
    Clean endpoint with constants usage.
    """
    states = [
        {"code": code, "name": name}
        for code, name in LocationConstants.VALID_STATE_CODES.items()
    ]
    
    # Sort by state name for better UX
    states.sort(key=lambda x: x["name"])
    
    states_data = {
        "states": states,
        "total": len(states)
    }
    
    return StatesListResponse(
        success=True,
        data=states_data,
        message=f"Retrieved {len(states)} valid US states"
    )


@router.get("/contest/{contest_id}/location", response_model=ContestLocationResponse)
async def get_contest_location(
    contest_id: int = Path(..., gt=0, description="Contest ID"),
    location_service: LocationService = Depends(get_location_service)
) -> ContestLocationResponse:
    """
    Get contest location configuration.
    Clean controller with service delegation and type safety.
    """
    contest_location = await location_service.get_contest_location(contest_id)
    
    return ContestLocationResponse(
        success=True,
        data=contest_location,
        message="Contest location configuration retrieved successfully"
    )


@router.get("/distance")
async def calculate_distance(
    lat1: float = Query(..., ge=LocationConstants.MIN_LATITUDE, le=LocationConstants.MAX_LATITUDE),
    lng1: float = Query(..., ge=LocationConstants.MIN_LONGITUDE, le=LocationConstants.MAX_LONGITUDE),
    lat2: float = Query(..., ge=LocationConstants.MIN_LATITUDE, le=LocationConstants.MAX_LATITUDE),
    lng2: float = Query(..., ge=LocationConstants.MIN_LONGITUDE, le=LocationConstants.MAX_LONGITUDE),
    location_service: LocationService = Depends(get_location_service)
) -> APIResponse[dict]:
    """
    Calculate distance between two coordinates.
    Clean utility endpoint with proper validation.
    """
    distance_result = await location_service.calculate_distance(
        lat1=lat1, lng1=lng1, lat2=lat2, lng2=lng2
    )
    
    return APIResponse(
        success=True,
        data=distance_result,
        message="Distance calculated successfully"
    )
