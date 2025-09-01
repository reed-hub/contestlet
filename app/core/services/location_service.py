"""
Clean location service with centralized location operations.
Handles geocoding, validation, and eligibility checking.
"""

import math
from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session

from app.models.contest import Contest
from app.schemas.location import ContestLocation, UserLocation, GeoCoordinates
from app.shared.exceptions.base import (
    ResourceNotFoundException, 
    ValidationException, 
    BusinessException,
    ErrorCode
)
from app.shared.constants.location import LocationConstants, LocationMessages, LocationErrors
from app.core.location_utils import validate_contest_location, check_contest_eligibility, format_location_display
from app.services.geocoding_service import geocoding_service


class LocationValidationResult:
    """Result object for location validation"""
    
    def __init__(self, valid: bool, errors: list = None, warnings: list = None, processed_location=None):
        self.valid = valid
        self.errors = errors or []
        self.warnings = warnings or []
        self.processed_location = processed_location


class GeocodeResult:
    """Result object for geocoding operations"""
    
    def __init__(self, success: bool, coordinates=None, formatted_address: str = None, error_message: str = None):
        self.success = success
        self.coordinates = coordinates
        self.formatted_address = formatted_address
        self.error_message = error_message


class EligibilityResult:
    """Result object for eligibility checking"""
    
    def __init__(self, eligible: bool, reason: str, location_requirements: str = None):
        self.eligible = eligible
        self.reason = reason
        self.location_requirements = location_requirements


class DistanceResult:
    """Result object for distance calculations"""
    
    def __init__(self, distance_miles: float, distance_km: float):
        self.distance_miles = distance_miles
        self.distance_km = distance_km


class LocationService:
    """
    Clean location service with centralized location operations.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    async def validate_contest_location(self, location_data: ContestLocation) -> LocationValidationResult:
        """
        Validate contest location data with comprehensive checks.
        
        Args:
            location_data: Contest location configuration
            
        Returns:
            LocationValidationResult with validation details
            
        Raises:
            ValidationException: If location data is invalid
        """
        try:
            # Use existing validation logic
            is_valid, errors, warnings = validate_contest_location(location_data)
            
            # Process location if valid
            processed_location = None
            if is_valid:
                # Ensure display_text is properly generated
                if not location_data.display_text or not location_data.display_text.strip():
                    location_data.display_text = format_location_display(location_data)
                processed_location = location_data
            
            return LocationValidationResult(
                valid=is_valid,
                errors=errors,
                warnings=warnings,
                processed_location=processed_location
            )
            
        except Exception as e:
            raise BusinessException(
                error_code=ErrorCode.VALIDATION_FAILED,
                message=LocationMessages.VALIDATION_FAILED,
                details={"error": str(e)}
            )
    
    async def geocode_address(self, address: str) -> GeocodeResult:
        """
        Geocode an address to coordinates using external service.
        
        Args:
            address: Address to geocode
            
        Returns:
            GeocodeResult with coordinates and formatted address
            
        Raises:
            ValidationException: If address format is invalid
        """
        # Validate address
        if not address or len(address.strip()) < LocationConstants.MIN_ADDRESS_LENGTH:
            raise ValidationException(
                message=LocationMessages.INVALID_ADDRESS,
                field_errors={"address": f"Address must be at least {LocationConstants.MIN_ADDRESS_LENGTH} characters"}
            )
        
        if len(address) > LocationConstants.MAX_ADDRESS_LENGTH:
            raise ValidationException(
                message=LocationMessages.INVALID_ADDRESS,
                field_errors={"address": f"Address must be less than {LocationConstants.MAX_ADDRESS_LENGTH} characters"}
            )
        
        try:
            # Use the geocoding service
            result = await geocoding_service.geocode_address(address)
            
            if result["success"]:
                coordinates = GeoCoordinates(
                    latitude=result["coordinates"]["latitude"],
                    longitude=result["coordinates"]["longitude"]
                )
                
                return GeocodeResult(
                    success=True,
                    coordinates=coordinates,
                    formatted_address=result["formatted_address"]
                )
            else:
                return GeocodeResult(
                    success=False,
                    error_message=result.get("message", LocationMessages.ADDRESS_NOT_FOUND)
                )
                
        except Exception as e:
            return GeocodeResult(
                success=False,
                error_message=f"{LocationMessages.GEOCODING_ERROR}: {str(e)}"
            )
    
    async def check_contest_eligibility(self, contest_id: int, user_location: UserLocation) -> EligibilityResult:
        """
        Check if user is eligible for contest based on location.
        
        Args:
            contest_id: Contest ID
            user_location: User's location data
            
        Returns:
            EligibilityResult with eligibility status and reason
            
        Raises:
            ResourceNotFoundException: If contest not found
        """
        # Get contest from database
        contest = self.db.query(Contest).filter(Contest.id == contest_id).first()
        if not contest:
            raise ResourceNotFoundException("Contest", contest_id)
        
        try:
            # Build ContestLocation from contest data
            contest_location = ContestLocation(
                location_type=contest.location_type or LocationConstants.DEFAULT_LOCATION_TYPE,
                selected_states=contest.selected_states,
                radius_address=contest.radius_address,
                radius_miles=contest.radius_miles,
                radius_coordinates=GeoCoordinates(
                    latitude=contest.radius_latitude,
                    longitude=contest.radius_longitude
                ) if contest.radius_latitude and contest.radius_longitude else None,
                custom_text=contest.location if contest.location_type == LocationConstants.LOCATION_TYPE_CUSTOM else None,
                display_text=contest.location or LocationMessages.LOCATION_NOT_CONFIGURED
            )
            
            # Check eligibility using existing logic
            is_eligible, reason = await check_contest_eligibility(contest_location, user_location)
            
            # Generate location requirements text
            location_requirements = format_location_display(contest_location)
            
            return EligibilityResult(
                eligible=is_eligible,
                reason=reason,
                location_requirements=location_requirements
            )
            
        except Exception as e:
            raise BusinessException(
                error_code=ErrorCode.BUSINESS_RULE_VIOLATION,
                message=LocationMessages.ELIGIBILITY_CHECK_FAILED,
                details={"contest_id": contest_id, "error": str(e)}
            )
    
    async def get_contest_location(self, contest_id: int) -> ContestLocation:
        """
        Get contest location configuration.
        
        Args:
            contest_id: Contest ID
            
        Returns:
            ContestLocation configuration
            
        Raises:
            ResourceNotFoundException: If contest not found
        """
        contest = self.db.query(Contest).filter(Contest.id == contest_id).first()
        if not contest:
            raise ResourceNotFoundException("Contest", contest_id)
        
        # Build ContestLocation from contest data
        contest_location = ContestLocation(
            location_type=contest.location_type or LocationConstants.DEFAULT_LOCATION_TYPE,
            selected_states=contest.selected_states,
            radius_address=contest.radius_address,
            radius_miles=contest.radius_miles,
            radius_coordinates=GeoCoordinates(
                latitude=contest.radius_latitude,
                longitude=contest.radius_longitude
            ) if contest.radius_latitude and contest.radius_longitude else None,
            custom_text=contest.location if contest.location_type == LocationConstants.LOCATION_TYPE_CUSTOM else None,
            display_text=contest.location or format_location_display(ContestLocation(
                location_type=contest.location_type or LocationConstants.DEFAULT_LOCATION_TYPE,
                selected_states=contest.selected_states,
                radius_miles=contest.radius_miles,
                custom_text=contest.location
            ))
        )
        
        return contest_location
    
    async def calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> DistanceResult:
        """
        Calculate distance between two coordinates using Haversine formula.
        
        Args:
            lat1, lng1: First coordinate pair
            lat2, lng2: Second coordinate pair
            
        Returns:
            DistanceResult with distance in miles and kilometers
            
        Raises:
            ValidationException: If coordinates are invalid
        """
        # Validate coordinates
        coords = [(lat1, "lat1"), (lng1, "lng1"), (lat2, "lat2"), (lng2, "lng2")]
        for coord, name in coords:
            if name.startswith("lat"):
                if not (LocationConstants.MIN_LATITUDE <= coord <= LocationConstants.MAX_LATITUDE):
                    raise ValidationException(
                        message=LocationMessages.INVALID_COORDINATES,
                        field_errors={name: f"Latitude must be between {LocationConstants.MIN_LATITUDE} and {LocationConstants.MAX_LATITUDE}"}
                    )
            else:
                if not (LocationConstants.MIN_LONGITUDE <= coord <= LocationConstants.MAX_LONGITUDE):
                    raise ValidationException(
                        message=LocationMessages.INVALID_COORDINATES,
                        field_errors={name: f"Longitude must be between {LocationConstants.MIN_LONGITUDE} and {LocationConstants.MAX_LONGITUDE}"}
                    )
        
        try:
            # Haversine formula
            lat1_rad = math.radians(lat1)
            lng1_rad = math.radians(lng1)
            lat2_rad = math.radians(lat2)
            lng2_rad = math.radians(lng2)
            
            dlat = lat2_rad - lat1_rad
            dlng = lng2_rad - lng1_rad
            
            a = (math.sin(dlat / 2) ** 2 + 
                 math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng / 2) ** 2)
            c = 2 * math.asin(math.sqrt(a))
            
            distance_miles = LocationConstants.EARTH_RADIUS_MILES * c
            distance_km = LocationConstants.EARTH_RADIUS_KM * c
            
            return DistanceResult(
                distance_miles=round(distance_miles, 2),
                distance_km=round(distance_km, 2)
            )
            
        except Exception as e:
            raise BusinessException(
                error_code=ErrorCode.VALIDATION_FAILED,
                message=LocationMessages.DISTANCE_CALCULATION_FAILED,
                details={"error": str(e)}
            )
