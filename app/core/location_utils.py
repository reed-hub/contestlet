"""
Location utilities for contest geographic targeting
"""

import math
from typing import Tuple, Optional, List
from app.schemas.location import ContestLocation, UserLocation, VALID_STATE_CODES

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth in miles.
    Uses the Haversine formula for accurate distance calculation.
    
    Args:
        lat1, lon1: Latitude and longitude of first point
        lat2, lon2: Latitude and longitude of second point
    
    Returns:
        Distance in miles
    """
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of Earth in miles
    earth_radius_miles = 3959
    
    return earth_radius_miles * c

def is_location_in_radius(
    target_lat: float, 
    target_lng: float, 
    center_lat: float, 
    center_lng: float, 
    radius_miles: int
) -> bool:
    """
    Check if target location is within specified radius of center point.
    
    Args:
        target_lat: Target latitude
        target_lng: Target longitude
        center_lat: Center point latitude
        center_lng: Center point longitude
        radius_miles: Radius in miles
    
    Returns:
        True if target is within radius, False otherwise
    """
    distance = haversine_distance(target_lat, target_lng, center_lat, center_lng)
    return distance <= radius_miles

def validate_contest_location(location: ContestLocation) -> Tuple[bool, List[str], List[str]]:
    """
    Validate contest location data and return validation results.
    
    Args:
        location: ContestLocation object to validate
    
    Returns:
        Tuple of (is_valid, errors, warnings)
    """
    errors = []
    warnings = []
    
    # Validate based on location type
    if location.location_type == "specific_states":
        if not location.selected_states or len(location.selected_states) == 0:
            errors.append("selected_states is required for specific_states location type")
        else:
            # Check for invalid state codes
            invalid_states = [
                state for state in location.selected_states 
                if state.upper() not in VALID_STATE_CODES
            ]
            if invalid_states:
                errors.append(f"Invalid state codes: {', '.join(invalid_states)}")
    
    elif location.location_type == "radius":
        if not location.radius_miles:
            errors.append("radius_miles is required for radius location type")
        elif location.radius_miles < 1 or location.radius_miles > 5000:
            errors.append("radius_miles must be between 1 and 5000")
        
        if not location.radius_address and not location.radius_coordinates:
            errors.append("Either radius_address or radius_coordinates is required for radius location type")
        
        if location.radius_coordinates:
            lat, lng = location.radius_coordinates.latitude, location.radius_coordinates.longitude
            if not (-90 <= lat <= 90):
                errors.append("radius_coordinates latitude must be between -90 and 90")
            if not (-180 <= lng <= 180):
                errors.append("radius_coordinates longitude must be between -180 and 180")
    
    elif location.location_type == "custom":
        if not location.custom_text or not location.custom_text.strip():
            errors.append("custom_text is required for custom location type")
    
    # Warnings for potential issues
    if location.location_type == "radius" and location.radius_miles and location.radius_miles > 1000:
        warnings.append(f"Large radius ({location.radius_miles} miles) may include very broad geographic area")
    
    if location.location_type == "specific_states" and location.selected_states and len(location.selected_states) > 25:
        warnings.append(f"Large number of states selected ({len(location.selected_states)}) - consider using 'united_states' type")
    
    is_valid = len(errors) == 0
    return is_valid, errors, warnings

async def check_contest_eligibility(
    contest_location: ContestLocation, 
    user_location: Optional[UserLocation]
) -> Tuple[bool, str]:
    """
    Check if user is eligible for contest based on location restrictions.
    
    Args:
        contest_location: Contest location requirements
        user_location: User's location data (optional)
    
    Returns:
        Tuple of (is_eligible, reason_message)
    """
    
    if contest_location.location_type == "united_states":
        return True, "Open to all United States residents"
    
    elif contest_location.location_type == "specific_states":
        if not user_location or not user_location.state:
            return False, "Location verification required for state-specific contest"
        
        user_state = user_location.state.upper()
        if user_state in [state.upper() for state in contest_location.selected_states]:
            state_name = VALID_STATE_CODES.get(user_state, user_state)
            return True, f"Eligible as {state_name} resident"
        else:
            allowed_states = ', '.join(contest_location.selected_states)
            return False, f"Contest restricted to residents of: {allowed_states}"
    
    elif contest_location.location_type == "radius":
        if not user_location or not user_location.coordinates:
            return False, "Location verification required for radius-based contest"
        
        if not contest_location.radius_coordinates or not contest_location.radius_miles:
            return False, "Contest location configuration incomplete"
        
        user_lat = user_location.coordinates.latitude
        user_lng = user_location.coordinates.longitude
        center_lat = contest_location.radius_coordinates.latitude
        center_lng = contest_location.radius_coordinates.longitude
        radius = contest_location.radius_miles
        
        if is_location_in_radius(user_lat, user_lng, center_lat, center_lng, radius):
            return True, f"Eligible - within {radius} miles of contest location"
        else:
            return False, f"Outside contest area (must be within {radius} miles of contest location)"
    
    elif contest_location.location_type == "custom":
        # For custom location types, we can't automatically verify eligibility
        # This would typically require manual review or additional verification steps
        return True, contest_location.display_text
    
    else:
        return False, "Unknown location restriction type"

def format_location_display(location: ContestLocation) -> str:
    """
    Generate a human-readable display string for contest location.
    
    Args:
        location: ContestLocation object
    
    Returns:
        Formatted display string
    """
    if location.display_text and location.display_text.strip():
        return location.display_text.strip()
    
    if location.location_type == "united_states":
        return "Open to all United States residents"
    
    elif location.location_type == "specific_states":
        if not location.selected_states:
            return "State-specific restrictions apply"
        
        states = location.selected_states
        if len(states) == 1:
            state_name = VALID_STATE_CODES.get(states[0], states[0])
            return f"Open to {state_name} residents only"
        elif len(states) <= 5:
            state_names = [VALID_STATE_CODES.get(state, state) for state in states]
            return f"Open to residents of: {', '.join(state_names)}"
        else:
            return f"Open to residents of {len(states)} selected states"
    
    elif location.location_type == "radius":
        if location.radius_miles and location.radius_address:
            return f"Within {location.radius_miles} miles of {location.radius_address}"
        elif location.radius_miles:
            return f"Within {location.radius_miles} miles of contest location"
        else:
            return "Radius-based location restrictions apply"
    
    elif location.location_type == "custom":
        if location.custom_text:
            return location.custom_text.strip()
        else:
            return "Custom location restrictions apply"
    
    return "Location restrictions apply"

def convert_legacy_location_to_smart(
    legacy_location: Optional[str],
    legacy_lat: Optional[float],
    legacy_lng: Optional[float]
) -> ContestLocation:
    """
    Convert legacy location data to smart location system.
    
    Args:
        legacy_location: Legacy location string
        legacy_lat: Legacy latitude
        legacy_lng: Legacy longitude
    
    Returns:
        ContestLocation object
    """
    # Default to united_states if no legacy data
    if not legacy_location:
        return ContestLocation(
            location_type="united_states",
            display_text="Open to all United States residents"
        )
    
    # Try to detect if it's a state-specific location
    location_upper = legacy_location.upper()
    detected_states = []
    
    for state_code, state_name in VALID_STATE_CODES.items():
        if state_code in location_upper or state_name.upper() in location_upper:
            detected_states.append(state_code)
    
    # If we detected specific states, use specific_states type
    if detected_states:
        # Remove duplicates and limit to reasonable number
        unique_states = list(dict.fromkeys(detected_states))[:10]
        return ContestLocation(
            location_type="specific_states",
            selected_states=unique_states,
            display_text=legacy_location
        )
    
    # If we have coordinates, could be radius-based
    if legacy_lat is not None and legacy_lng is not None:
        return ContestLocation(
            location_type="radius",
            radius_miles=50,  # Default 50-mile radius
            radius_coordinates={
                "latitude": legacy_lat,
                "longitude": legacy_lng
            },
            display_text=legacy_location
        )
    
    # Fall back to custom type
    return ContestLocation(
        location_type="custom",
        custom_text=legacy_location,
        display_text=legacy_location
    )
