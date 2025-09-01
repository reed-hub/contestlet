"""
Location-related constants for geographic targeting and validation.
Centralizes all location-specific configuration and validation rules.
"""

class LocationConstants:
    """Location validation and configuration constants"""
    
    # Address validation
    MIN_ADDRESS_LENGTH = 5
    MAX_ADDRESS_LENGTH = 500
    
    # Coordinate validation
    MIN_LATITUDE = -90.0
    MAX_LATITUDE = 90.0
    MIN_LONGITUDE = -180.0
    MAX_LONGITUDE = 180.0
    
    # Radius validation
    MIN_RADIUS_MILES = 1
    MAX_RADIUS_MILES = 500
    DEFAULT_RADIUS_MILES = 25
    
    # Location types
    LOCATION_TYPE_UNITED_STATES = "united_states"
    LOCATION_TYPE_SPECIFIC_STATES = "specific_states"
    LOCATION_TYPE_RADIUS = "radius"
    LOCATION_TYPE_CUSTOM = "custom"
    
    VALID_LOCATION_TYPES = [
        LOCATION_TYPE_UNITED_STATES,
        LOCATION_TYPE_SPECIFIC_STATES,
        LOCATION_TYPE_RADIUS,
        LOCATION_TYPE_CUSTOM
    ]
    
    # State validation
    MAX_SELECTED_STATES = 50
    MIN_SELECTED_STATES = 1
    
    # Valid US state codes and names
    VALID_STATE_CODES = {
        "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
        "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "FL": "Florida", "GA": "Georgia",
        "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
        "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
        "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi", "MO": "Missouri",
        "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey",
        "NM": "New Mexico", "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
        "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
        "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont",
        "VA": "Virginia", "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
        "DC": "District of Columbia"
    }
    
    # Geocoding settings
    GEOCODING_TIMEOUT_SECONDS = 10
    MAX_GEOCODING_RETRIES = 3
    GEOCODING_USER_AGENT = "Contestlet/1.0"
    
    # Distance calculation
    EARTH_RADIUS_MILES = 3959
    EARTH_RADIUS_KM = 6371
    
    # Display text limits
    MAX_DISPLAY_TEXT_LENGTH = 200
    MIN_DISPLAY_TEXT_LENGTH = 5


class LocationMessages:
    """Standardized location-related messages"""
    
    # Validation messages
    VALIDATION_SUCCESS = "Location data validated successfully"
    VALIDATION_FAILED = "Location validation failed"
    INVALID_LOCATION_TYPE = "Invalid location type specified"
    INVALID_COORDINATES = "Invalid latitude or longitude coordinates"
    INVALID_RADIUS = "Invalid radius value"
    INVALID_STATES = "Invalid state selection"
    INVALID_ADDRESS = "Invalid address format"
    
    # Geocoding messages
    GEOCODING_SUCCESS = "Address geocoded successfully"
    GEOCODING_FAILED = "Failed to geocode address"
    ADDRESS_NOT_FOUND = "Address not found"
    GEOCODING_TIMEOUT = "Geocoding request timed out"
    GEOCODING_ERROR = "Geocoding service error"
    
    # Eligibility messages
    ELIGIBILITY_CHECKED = "Contest eligibility checked successfully"
    ELIGIBLE = "You are eligible for this contest"
    NOT_ELIGIBLE_LOCATION = "You are not eligible based on your location"
    NOT_ELIGIBLE_STATE = "Contest is not available in your state"
    NOT_ELIGIBLE_RADIUS = "You are outside the contest area"
    ELIGIBILITY_CHECK_FAILED = "Unable to check eligibility"
    
    # Distance messages
    DISTANCE_CALCULATED = "Distance calculated successfully"
    DISTANCE_CALCULATION_FAILED = "Failed to calculate distance"
    
    # Contest location messages
    CONTEST_LOCATION_RETRIEVED = "Contest location configuration retrieved"
    CONTEST_LOCATION_NOT_FOUND = "Contest location configuration not found"
    
    # State messages
    STATES_RETRIEVED = "Valid states retrieved successfully"
    
    # Display text generation
    LOCATION_US_ALL = "Contest open to all United States residents"
    LOCATION_STATES_SINGLE = "Contest open to {state} residents only"
    LOCATION_STATES_MULTIPLE = "Contest open to residents of {states}"
    LOCATION_RADIUS = "Contest open to residents within {miles} miles of {address}"
    LOCATION_CUSTOM = "Custom location restrictions apply"
    LOCATION_NOT_CONFIGURED = "Location targeting not configured"


class LocationErrors:
    """Location-specific error codes"""
    
    INVALID_LOCATION_TYPE = "INVALID_LOCATION_TYPE"
    INVALID_COORDINATES = "INVALID_COORDINATES"
    INVALID_RADIUS = "INVALID_RADIUS"
    INVALID_STATES = "INVALID_STATES"
    INVALID_ADDRESS = "INVALID_ADDRESS"
    
    GEOCODING_FAILED = "GEOCODING_FAILED"
    ADDRESS_NOT_FOUND = "ADDRESS_NOT_FOUND"
    GEOCODING_TIMEOUT = "GEOCODING_TIMEOUT"
    
    ELIGIBILITY_CHECK_FAILED = "ELIGIBILITY_CHECK_FAILED"
    CONTEST_NOT_FOUND = "CONTEST_NOT_FOUND"
    
    DISTANCE_CALCULATION_FAILED = "DISTANCE_CALCULATION_FAILED"


class LocationDefaults:
    """Default values for location operations"""
    
    DEFAULT_LOCATION_TYPE = LocationConstants.LOCATION_TYPE_UNITED_STATES
    DEFAULT_RADIUS_MILES = 25
    DEFAULT_GEOCODING_TIMEOUT = 10
    DEFAULT_MAX_RESULTS = 1
    
    # Default display texts
    DEFAULT_US_DISPLAY = "Open to all US residents"
    DEFAULT_RADIUS_DISPLAY = "Local contest area"
    DEFAULT_STATES_DISPLAY = "State-specific contest"
    DEFAULT_CUSTOM_DISPLAY = "Custom location restrictions"
