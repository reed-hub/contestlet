"""
Location-specific response models with type safety.
Provides standardized responses for all location endpoints.
"""

from typing import Dict, Any, List
from pydantic import BaseModel, Field

from app.shared.types.responses import APIResponse
from app.schemas.location import ContestLocation, GeoCoordinates


class LocationValidationData(BaseModel):
    """Location validation result data"""
    valid: bool = Field(..., description="Whether location data is valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    processed_location: ContestLocation = Field(None, description="Processed location data")


class LocationValidationResponse(APIResponse[LocationValidationData]):
    """Type-safe response for location validation"""
    pass


class GeocodeData(BaseModel):
    """Geocoding result data"""
    success: bool = Field(..., description="Whether geocoding was successful")
    coordinates: GeoCoordinates = Field(None, description="Geocoded coordinates")
    formatted_address: str = Field(None, description="Formatted address")
    error_message: str = Field(None, description="Error message if failed")


class GeocodeResponse(APIResponse[GeocodeData]):
    """Type-safe response for geocoding"""
    pass


class EligibilityData(BaseModel):
    """Contest eligibility result data"""
    eligible: bool = Field(..., description="Whether user is eligible")
    reason: str = Field(..., description="Eligibility reason")
    location_requirements: str = Field(None, description="Contest location requirements")


class EligibilityCheckResponse(APIResponse[EligibilityData]):
    """Type-safe response for eligibility checking"""
    pass


class StatesData(BaseModel):
    """US states data"""
    states: List[Dict[str, str]] = Field(..., description="List of states with codes and names")
    total: int = Field(..., description="Total number of states")


class StatesListResponse(APIResponse[StatesData]):
    """Type-safe response for states list"""
    pass


class ContestLocationResponse(APIResponse[ContestLocation]):
    """Type-safe response for contest location"""
    pass


class DistanceData(BaseModel):
    """Distance calculation result data"""
    distance_miles: float = Field(..., description="Distance in miles")
    distance_km: float = Field(..., description="Distance in kilometers")


class DistanceResponse(APIResponse[DistanceData]):
    """Type-safe response for distance calculations"""
    pass
