"""
Geocoding service for address to coordinate conversion.
Uses OpenStreetMap Nominatim (free) with fallback options.
"""

import logging
from typing import Optional, Dict, Any, Tuple
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class GeocodingService:
    """Service for converting addresses to coordinates using OpenStreetMap Nominatim."""
    
    def __init__(self):
        """Initialize the geocoding service."""
        # Initialize Nominatim geocoder with a proper user agent and SSL context
        import ssl
        import certifi
        
        # Create SSL context with proper certificates
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        
        self.geocoder = Nominatim(
            user_agent="contestlet-api/1.0 (contest platform)",
            timeout=10,
            ssl_context=ssl_context
        )
    
    async def geocode_address(self, address: str) -> Dict[str, Any]:
        """
        Convert an address string to coordinates.
        
        Args:
            address: The address string to geocode
            
        Returns:
            Dictionary containing success status, coordinates, and formatted address
            
        Raises:
            HTTPException: If geocoding fails or address is invalid
        """
        if not address or not address.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Address is required"
            )
        
        # Validate address length
        address = address.strip()
        if len(address) < 1 or len(address) > 500:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Address must be between 1 and 500 characters"
            )
        
        try:
            logger.info(f"Geocoding address: {address}")
            
            # Perform geocoding
            location = self.geocoder.geocode(address, exactly_one=True)
            
            if location is None:
                logger.warning(f"Address not found: {address}")
                return {
                    "success": False,
                    "message": "Address not found"
                }
            
            # Extract coordinates and formatted address
            coordinates = {
                "latitude": float(location.latitude),
                "longitude": float(location.longitude)
            }
            
            formatted_address = location.address
            
            logger.info(f"Successfully geocoded: {address} -> {coordinates}")
            
            return {
                "success": True,
                "coordinates": coordinates,
                "formatted_address": formatted_address
            }
            
        except GeocoderTimedOut:
            logger.error(f"Geocoding timeout for address: {address}")
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail="Geocoding service timed out. Please try again."
            )
            
        except GeocoderServiceError as e:
            logger.error(f"Geocoding service error for address: {address}, error: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Geocoding service is temporarily unavailable"
            )
            
        except Exception as e:
            logger.error(f"Unexpected geocoding error for address: {address}, error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while geocoding the address"
            )
    
    async def validate_coordinates(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Validate coordinates and optionally get address information.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            Dictionary containing validation results and address information
        """
        # Validate coordinate ranges
        if not (-90 <= latitude <= 90):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Latitude must be between -90 and 90"
            )
        
        if not (-180 <= longitude <= 180):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Longitude must be between -180 and 180"
            )
        
        try:
            # Reverse geocode to get address information
            location = self.geocoder.reverse(
                (latitude, longitude), 
                exactly_one=True,
                timeout=10
            )
            
            if location is None:
                return {
                    "success": True,
                    "coordinates": {
                        "latitude": latitude,
                        "longitude": longitude
                    },
                    "address": "Unknown location"
                }
            
            return {
                "success": True,
                "coordinates": {
                    "latitude": latitude,
                    "longitude": longitude
                },
                "address": location.address
            }
            
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.warning(f"Reverse geocoding failed for {latitude}, {longitude}: {e}")
            # Return coordinates even if reverse geocoding fails
            return {
                "success": True,
                "coordinates": {
                    "latitude": latitude,
                    "longitude": longitude
                },
                "address": "Address lookup unavailable"
            }
        
        except Exception as e:
            logger.error(f"Unexpected error in coordinate validation: {e}")
            # Return coordinates even if reverse geocoding fails
            return {
                "success": True,
                "coordinates": {
                    "latitude": latitude,
                    "longitude": longitude
                },
                "address": "Address lookup failed"
            }
    
    def is_service_available(self) -> bool:
        """
        Check if the geocoding service is available.
        
        Returns:
            True if service is available, False otherwise
        """
        try:
            # Test with a simple, well-known address
            test_location = self.geocoder.geocode("New York, NY", timeout=5)
            return test_location is not None
        except Exception:
            return False


# Create a singleton instance
geocoding_service = GeocodingService()
