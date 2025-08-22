from pydantic import BaseModel, Field, validator
from typing import Optional, List, Literal
from decimal import Decimal

class GeoCoordinates(BaseModel):
    """Geographic coordinates for location targeting"""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate (-90 to 90)")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate (-180 to 180)")
    
    class Config:
        json_encoders = {
            float: lambda v: round(v, 8)  # Precision for coordinates
        }

class ContestLocation(BaseModel):
    """Comprehensive location targeting system for contests"""
    
    location_type: Literal["united_states", "specific_states", "radius", "custom"] = Field(
        ..., 
        description="Type of location targeting"
    )
    
    # For specific states selection
    selected_states: Optional[List[str]] = Field(
        None, 
        description="List of state codes for state-specific targeting (e.g., ['CA', 'NY', 'TX'])"
    )
    
    # For radius-based targeting
    radius_address: Optional[str] = Field(
        None, 
        max_length=500,
        description="Address for radius-based targeting center"
    )
    radius_miles: Optional[int] = Field(
        None, 
        ge=1, 
        le=5000,
        description="Radius in miles for location targeting (1-5000)"
    )
    radius_coordinates: Optional[GeoCoordinates] = Field(
        None,
        description="Geocoded coordinates for radius center"
    )
    
    # For custom text (fallback)
    custom_text: Optional[str] = Field(
        None,
        max_length=500,
        description="Custom location description for manual targeting"
    )
    
    # Computed/display field
    display_text: str = Field(
        ...,
        max_length=500,
        description="Human-readable location description for display"
    )
    
    @validator('selected_states')
    def validate_state_codes(cls, v):
        """Validate US state codes"""
        if not v:
            return v
            
        VALID_STATE_CODES = {
            "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
            "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
            "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
            "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
            "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
            "DC"  # Include District of Columbia
        }
        
        # Normalize to uppercase and validate
        normalized_states = []
        for state in v:
            state_upper = state.upper().strip()
            if state_upper not in VALID_STATE_CODES:
                raise ValueError(f'Invalid state code: {state}. Must be valid US state/territory code.')
            normalized_states.append(state_upper)
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(normalized_states))
    
    @validator('display_text', always=True)
    def generate_display_text(cls, v, values):
        """Auto-generate display text if not provided"""
        if v and v.strip():
            return v.strip()
        
        location_type = values.get('location_type')
        
        if location_type == "united_states":
            return "Open to all United States residents"
        
        elif location_type == "specific_states":
            states = values.get('selected_states', [])
            if states:
                if len(states) == 1:
                    return f"Open to {states[0]} residents only"
                elif len(states) <= 3:
                    return f"Open to {', '.join(states)} residents only"
                else:
                    return f"Open to residents of {len(states)} selected states"
            return "State-specific targeting (states not specified)"
        
        elif location_type == "radius":
            radius_miles = values.get('radius_miles')
            radius_address = values.get('radius_address')
            if radius_miles and radius_address:
                return f"Within {radius_miles} miles of {radius_address}"
            elif radius_miles:
                return f"Within {radius_miles} miles of contest location"
            return "Radius-based targeting (details not specified)"
        
        elif location_type == "custom":
            custom_text = values.get('custom_text')
            if custom_text:
                return custom_text.strip()
            return "Custom location restrictions apply"
        
        return "Location restrictions apply"
    
    @validator('radius_miles')
    def validate_radius_requirements(cls, v, values):
        """Ensure radius requirements are met when radius type is selected"""
        location_type = values.get('location_type')
        if location_type == "radius" and not v:
            raise ValueError('radius_miles is required when location_type is "radius"')
        return v
    
    @validator('selected_states')
    def validate_states_requirements(cls, v, values):
        """Ensure states are provided when specific_states type is selected"""
        location_type = values.get('location_type')
        if location_type == "specific_states" and (not v or len(v) == 0):
            raise ValueError('selected_states is required when location_type is "specific_states"')
        return v
    
    @validator('custom_text')
    def validate_custom_requirements(cls, v, values):
        """Ensure custom text is provided when custom type is selected"""
        location_type = values.get('location_type')
        if location_type == "custom" and (not v or not v.strip()):
            raise ValueError('custom_text is required when location_type is "custom"')
        return v

class LocationValidationRequest(BaseModel):
    """Request for location validation"""
    location_data: ContestLocation = Field(..., description="Location data to validate")

class LocationValidationResponse(BaseModel):
    """Response for location validation"""
    valid: bool = Field(..., description="Whether the location data is valid")
    errors: List[str] = Field(default_factory=list, description="List of validation errors")
    warnings: List[str] = Field(default_factory=list, description="List of validation warnings")
    processed_location: Optional[ContestLocation] = Field(None, description="Processed and validated location data")

class GeocodeRequest(BaseModel):
    """Request for address geocoding"""
    address: str = Field(..., min_length=1, max_length=500, description="Address to geocode")

class GeocodeResponse(BaseModel):
    """Response for address geocoding"""
    success: bool = Field(..., description="Whether geocoding was successful")
    coordinates: Optional[GeoCoordinates] = Field(None, description="Geocoded coordinates")
    formatted_address: Optional[str] = Field(None, description="Formatted address from geocoding service")
    error_message: Optional[str] = Field(None, description="Error message if geocoding failed")

class UserLocation(BaseModel):
    """User location for eligibility checking"""
    state: Optional[str] = Field(None, description="User's state code")
    coordinates: Optional[GeoCoordinates] = Field(None, description="User's coordinates")
    address: Optional[str] = Field(None, description="User's address")

class EligibilityCheckRequest(BaseModel):
    """Request for contest eligibility check"""
    contest_id: int = Field(..., description="Contest ID to check eligibility for")
    user_location: Optional[UserLocation] = Field(None, description="User's location data")

class EligibilityCheckResponse(BaseModel):
    """Response for contest eligibility check"""
    eligible: bool = Field(..., description="Whether user is eligible for the contest")
    reason: str = Field(..., description="Explanation of eligibility status")
    location_requirements: str = Field(..., description="Contest location requirements")

# Constants for location utilities
VALID_STATE_CODES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", 
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", 
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho", 
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", 
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland", 
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi", 
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", 
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York", 
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", 
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina", 
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah", 
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia", 
    "WI": "Wisconsin", "WY": "Wyoming", "DC": "District of Columbia"
}

def get_state_name(state_code: str) -> Optional[str]:
    """Get full state name from state code"""
    return VALID_STATE_CODES.get(state_code.upper())

def validate_state_codes(states: List[str]) -> List[str]:
    """Validate and return only valid state codes"""
    return [state.upper() for state in states if state.upper() in VALID_STATE_CODES]
