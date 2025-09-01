"""
Contest-related constants centralized from across the codebase.
Eliminates magic numbers and hardcoded values.
"""

class ContestConstants:
    """Contest field limits and validation constants"""
    
    # Contest status constants
    STATUS_DRAFT = "draft"
    STATUS_AWAITING_APPROVAL = "awaiting_approval"
    STATUS_REJECTED = "rejected"
    STATUS_PUBLISHED = "published"
    STATUS_UPCOMING = "upcoming"
    STATUS_ACTIVE = "active"
    STATUS_ENDED = "ended"
    STATUS_COMPLETE = "complete"
    STATUS_CANCELLED = "cancelled"
    
    # Valid statuses list
    VALID_STATUSES = [
        STATUS_DRAFT,
        STATUS_AWAITING_APPROVAL,
        STATUS_REJECTED,
        STATUS_PUBLISHED,
        STATUS_UPCOMING,
        STATUS_ACTIVE,
        STATUS_ENDED,
        STATUS_COMPLETE,
        STATUS_CANCELLED
    ]
    
    # Name validation
    MAX_NAME_LENGTH = 200
    MIN_NAME_LENGTH = 3
    
    # Description validation
    MAX_DESCRIPTION_LENGTH = 2000
    MIN_DESCRIPTION_LENGTH = 10
    
    # Prize description validation
    MAX_PRIZE_DESCRIPTION_LENGTH = 1000
    MIN_PRIZE_DESCRIPTION_LENGTH = 5
    
    # Location validation
    MAX_LOCATION_LENGTH = 500
    MAX_RADIUS_ADDRESS_LENGTH = 500
    
    # Contest configuration defaults
    DEFAULT_MINIMUM_AGE = 18
    MIN_AGE = 13
    MAX_AGE = 120
    
    # Entry limits
    MIN_ENTRIES_PER_PERSON = 1
    MAX_ENTRIES_PER_PERSON = 1000
    DEFAULT_ENTRIES_PER_PERSON = 1
    MIN_TOTAL_ENTRY_LIMIT = 1
    MAX_TOTAL_ENTRY_LIMIT = 1000000
    
    # Geographic constraints
    MAX_RADIUS_MILES = 500
    MIN_RADIUS_MILES = 1
    DEFAULT_SEARCH_RADIUS_MILES = 25
    MIN_SEARCH_RADIUS = 1
    MAX_SEARCH_RADIUS = 500
    MAX_SELECTED_STATES = 50
    
    # Latitude/longitude validation
    MIN_LATITUDE = -90.0
    MAX_LATITUDE = 90.0
    MIN_LONGITUDE = -180.0
    MAX_LONGITUDE = 180.0
    
    # Default values
    DEFAULT_CONTEST_TYPE = "general"
    DEFAULT_ENTRY_METHOD = "sms"
    DEFAULT_WINNER_SELECTION_METHOD = "random"
    DEFAULT_LOCATION_TYPE = "united_states"
    
    # Status values
    VALID_STATUSES = [
        "draft",
        "awaiting_approval", 
        "rejected",
        "upcoming",
        "active",
        "ended",
        "complete",
        "cancelled"
    ]
    
    # Published statuses (visible to public)
    PUBLISHED_STATUSES = ["upcoming", "active", "ended", "complete"]
    
    # Statuses that allow entries
    ENTRY_ALLOWED_STATUSES = ["active"]
    
    # Statuses that can be deleted
    DELETABLE_STATUSES = ["draft", "awaiting_approval", "rejected", "upcoming", "ended"]
    
    # Statuses that cannot be deleted
    PROTECTED_STATUSES = ["active", "complete"]


class ContestMessages:
    """Standardized contest-related messages"""
    
    # Creation messages
    CREATED_SUCCESSFULLY = "Contest created successfully"
    DRAFT_CREATED = "Contest draft created successfully"
    
    # Update messages
    UPDATED_SUCCESSFULLY = "Contest updated successfully"
    STATUS_UPDATED = "Contest status updated successfully"
    
    # Deletion messages
    DELETED_SUCCESSFULLY = "Contest deleted successfully"
    CANNOT_DELETE_ACTIVE = "Contest is currently active and accepting entries"
    CANNOT_DELETE_HAS_ENTRIES = "Contest has entries and cannot be deleted"
    CANNOT_DELETE_COMPLETE = "Contest is complete and archived"
    
    # Entry messages
    ENTRY_SUCCESSFUL = "Successfully entered contest"
    ENTRY_DUPLICATE = "You have already entered this contest. Duplicate entries are not allowed."
    ENTRY_LIMIT_REACHED = "Contest has reached maximum entry limit"
    ENTRY_LIMIT_PER_PERSON = "Maximum entries per person reached"
    
    # Status messages
    CONTEST_NOT_STARTED = "Contest has not started yet"
    CONTEST_ENDED = "Contest has ended"
    CONTEST_CANCELLED = "Contest has been cancelled"
    CONTEST_DRAFT = "Contest is still in draft mode"
    CONTEST_AWAITING_APPROVAL = "Contest is awaiting admin approval"
    CONTEST_REJECTED = "Contest has been rejected"
    CONTEST_COMPLETE = "Contest is complete - winner already selected"
    
    # Permission messages
    INSUFFICIENT_PERMISSIONS = "You do not have permission to perform this action"
    ADMIN_ACCESS_REQUIRED = "Admin access required"
    SPONSOR_ACCESS_REQUIRED = "Sponsor access required"
    OWNER_ACCESS_REQUIRED = "Only the contest owner can perform this action"
    
    # Validation messages
    INVALID_DATE_RANGE = "Contest end time must be after start time"
    INVALID_COORDINATES = "Invalid latitude or longitude coordinates"
    INVALID_RADIUS = "Invalid radius value"
    INVALID_STATE_SELECTION = "Invalid state selection"
    
    # Not found messages
    CONTEST_NOT_FOUND = "Contest not found"
    CONTEST_NOT_ACCESSIBLE = "Contest not found or not accessible"


class ContestDefaults:
    """Default values for contest creation"""
    
    # Pagination defaults
    DEFAULT_PAGE_SIZE = 10
    MAX_PAGE_SIZE = 100
    DEFAULT_PAGE = 1
    
    # Search defaults
    DEFAULT_SEARCH_RADIUS_MILES = 25.0
    MIN_SEARCH_RADIUS = 0.1
    MAX_SEARCH_RADIUS = 100.0
    
    # List limits
    DEFAULT_CONTEST_LIMIT = 100
    MAX_CONTEST_LIMIT = 1000
    
    # Time defaults
    DEFAULT_CONTEST_DURATION_HOURS = 24
    MIN_CONTEST_DURATION_MINUTES = 30
    
    # Media defaults
    DEFAULT_CLOUDINARY_FOLDER = "contestlet"
    MAX_IMAGE_SIZE_MB = 10
    ALLOWED_IMAGE_FORMATS = ["jpg", "jpeg", "png", "webp"]
