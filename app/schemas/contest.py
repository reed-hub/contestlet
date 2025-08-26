from pydantic import BaseModel, Field, validator, computed_field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class ContestType(str, Enum):
    """Contest type enumeration"""
    GENERAL = "general"
    SWEEPSTAKES = "sweepstakes"
    INSTANT_WIN = "instant_win"
    DAILY = "daily"
    WEEKLY = "weekly"


class EntryMethod(str, Enum):
    """Entry method enumeration"""
    SMS = "sms"
    EMAIL = "email"
    WEB_FORM = "web_form"
    SOCIAL_MEDIA = "social_media"


class WinnerSelectionMethod(str, Enum):
    """Winner selection method enumeration"""
    RANDOM = "random"
    SCHEDULED = "scheduled"
    INSTANT = "instant"
    JUDGED = "judged"


class ContestStatus(str, Enum):
    """Contest status enumeration"""
    UPCOMING = "upcoming"
    ACTIVE = "active"
    ENDED = "ended"
    COMPLETE = "complete"
    CANCELLED = "cancelled"


class ContestBase(BaseModel):
    """Base contest model with common fields"""
    
    name: str = Field(..., min_length=3, max_length=200, description="Contest name")
    description: Optional[str] = Field(None, max_length=2000, description="Contest description")
    location: Optional[str] = Field(None, max_length=500, description="Contest location (city, state, zip)")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude for geolocation")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude for geolocation")
    start_time: datetime = Field(..., description="Contest start time")
    end_time: datetime = Field(..., description="Contest end time")
    prize_description: Optional[str] = Field(None, max_length=1000, description="Prize description")
    active: bool = Field(True, description="Whether the contest is active")
    
    # Contest configuration
    contest_type: ContestType = Field(ContestType.GENERAL, description="Contest type")
    entry_method: EntryMethod = Field(EntryMethod.SMS, description="Entry method")
    winner_selection_method: WinnerSelectionMethod = Field(WinnerSelectionMethod.RANDOM, description="Winner selection method")
    minimum_age: int = Field(18, ge=13, le=120, description="Minimum age requirement")
    max_entries_per_person: Optional[int] = Field(None, ge=1, le=1000, description="Maximum entries per person")
    total_entry_limit: Optional[int] = Field(None, ge=1, le=1000000, description="Total entry limit")
    consolation_offer: Optional[str] = Field(None, max_length=500, description="Consolation prize/offer")
    geographic_restrictions: Optional[str] = Field(None, max_length=500, description="Geographic restrictions")
    contest_tags: Optional[List[str]] = Field(None, max_items=20, description="Contest tags")
    promotion_channels: Optional[List[str]] = Field(None, max_items=10, description="Promotion channels")
    
    # Visual branding and sponsor information
    image_url: Optional[str] = Field(None, max_length=500, description="CDN URL to contest hero image")
    sponsor_url: Optional[str] = Field(None, max_length=500, description="Sponsor's website URL")
    
    # Smart Location System fields
    location_type: str = Field("united_states", max_length=50, description="Location targeting type")
    selected_states: Optional[List[str]] = Field(None, max_items=50, description="State codes for targeting")
    radius_address: Optional[str] = Field(None, max_length=500, description="Address for radius targeting")
    radius_miles: Optional[int] = Field(None, ge=1, le=500, description="Radius in miles for targeting")
    radius_latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude for radius center")
    radius_longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude for radius center")

    @validator('start_time', 'end_time')
    def validate_dates(cls, v, values):
        """Validate contest dates"""
        if 'start_time' in values and 'end_time' in values:
            if values['start_time'] >= values['end_time']:
                raise ValueError('Start time must be before end time')
        return v
    
    @validator('start_time')
    def validate_start_time(cls, v):
        """Validate start time is in the future (only for creation)"""
        # Only validate for creation, not for responses
        # This validator is overridden in ContestResponse
        if v <= datetime.utcnow():
            raise ValueError('Start time must be in the future')
        return v
    
    @validator('contest_tags')
    def validate_tags(cls, v):
        """Validate contest tags"""
        if v:
            # Remove duplicates and empty strings
            v = list(set(tag.strip() for tag in v if tag.strip()))
            # Limit tag length
            for tag in v:
                if len(tag) > 50:
                    raise ValueError('Tag length cannot exceed 50 characters')
        return v
    
    @validator('promotion_channels')
    def validate_channels(cls, v):
        """Validate promotion channels"""
        if v:
            valid_channels = ['social_media', 'email', 'sms', 'web', 'print', 'tv', 'radio']
            for channel in v:
                if channel not in valid_channels:
                    raise ValueError(f'Invalid promotion channel: {channel}')
        return v


class ContestCreate(ContestBase):
    """Contest creation model"""
    pass


class ContestUpdate(BaseModel):
    """Contest update model with optional fields"""
    
    name: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    location: Optional[str] = Field(None, max_length=500)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    prize_description: Optional[str] = Field(None, max_length=1000)
    active: Optional[bool] = None
    contest_type: Optional[ContestType] = None
    entry_method: Optional[EntryMethod] = None
    winner_selection_method: Optional[WinnerSelectionMethod] = None
    minimum_age: Optional[int] = Field(None, ge=13, le=120)
    max_entries_per_person: Optional[int] = Field(None, ge=1, le=1000)
    total_entry_limit: Optional[int] = Field(None, ge=1, le=1000000)
    consolation_offer: Optional[str] = Field(None, max_length=500)
    geographic_restrictions: Optional[str] = Field(None, max_length=500)
    contest_tags: Optional[List[str]] = Field(None, max_items=20)
    promotion_channels: Optional[List[str]] = Field(None, max_items=10)
    image_url: Optional[str] = Field(None, max_length=500)
    sponsor_url: Optional[str] = Field(None, max_length=500)
    location_type: Optional[str] = Field(None, max_length=50)
    selected_states: Optional[List[str]] = Field(None, max_items=50)
    radius_address: Optional[str] = Field(None, max_length=500)
    radius_miles: Optional[int] = Field(None, ge=1, le=500)
    radius_latitude: Optional[float] = Field(None, ge=-90, le=90)
    radius_longitude: Optional[float] = Field(None, ge=-180, le=180)


class ContestResponse(BaseModel):
    """Contest response model with computed fields"""
    
    # Basic contest info
    id: int
    name: str
    description: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    start_time: datetime
    end_time: datetime
    prize_description: Optional[str] = None
    prize_value: Optional[float] = None  # Made optional since it's not in the model
    
    # Contest configuration
    contest_type: str = "general"
    entry_method: str = "sms"
    winner_selection_method: str = "random"
    active: bool = True
    minimum_age: int = 18
    max_entries_per_person: Optional[int] = None
    total_entry_limit: Optional[int] = None
    
    # Additional details
    consolation_offer: Optional[str] = None
    geographic_restrictions: Optional[str] = None
    contest_tags: Optional[List[str]] = None
    promotion_channels: Optional[List[str]] = None
    image_url: Optional[str] = None
    sponsor_url: Optional[str] = None
    
    # Location system
    location_type: str = "united_states"
    selected_states: Optional[List[str]] = None
    radius_address: Optional[str] = None
    radius_miles: Optional[int] = None
    radius_latitude: Optional[float] = None
    radius_longitude: Optional[float] = None
    
    # Role system
    created_by_user_id: Optional[int] = None
    sponsor_profile_id: Optional[int] = None
    is_approved: bool = True
    approved_by_user_id: Optional[int] = None
    approved_at: Optional[datetime] = None
    
    # Response-specific fields
    created_at: datetime
    updated_at: Optional[datetime] = None
    distance_miles: Optional[float] = Field(None, ge=0, description="Distance from query point in miles")
    status: ContestStatus
    entry_count: int = Field(0, description="Number of entries received")
    is_winner_selected: bool = Field(False, description="Whether a winner has been selected")
    
    @computed_field
    @property
    def is_upcoming(self) -> bool:
        """Check if contest is upcoming"""
        return self.status == ContestStatus.UPCOMING
    
    @computed_field
    @property
    def is_active(self) -> bool:
        """Check if contest is active"""
        return self.status == ContestStatus.ACTIVE
    
    @computed_field
    @property
    def is_ended(self) -> bool:
        """Check if contest has ended"""
        return self.status == ContestStatus.ENDED
    
    @computed_field
    @property
    def is_complete(self) -> bool:
        """Check if contest is complete"""
        return self.status == ContestStatus.COMPLETE
    
    @computed_field
    @property
    def time_until_start(self) -> Optional[int]:
        """Seconds until contest starts (negative if already started)"""
        if self.start_time:
            return int((self.start_time - datetime.utcnow()).total_seconds())
        return None
    
    @computed_field
    @property
    def time_until_end(self) -> Optional[int]:
        """Seconds until contest ends (negative if already ended)"""
        if self.end_time:
            return int((self.end_time - datetime.utcnow()).total_seconds())
        return None
    
    @computed_field
    @property
    def duration_days(self) -> Optional[int]:
        """Contest duration in days"""
        if self.start_time and self.end_time:
            return int((self.end_time - self.start_time).days)
        return None
    
    @computed_field
    @property
    def can_enter(self) -> bool:
        """Check if users can currently enter the contest"""
        return (
            self.is_active and 
            not self.is_winner_selected and
            (self.total_entry_limit is None or self.entry_count < self.total_entry_limit)
        )
    
    @computed_field
    @property
    def entry_limit_reached(self) -> bool:
        """Check if entry limit has been reached"""
        return (
            self.total_entry_limit is not None and 
            self.entry_count >= self.total_entry_limit
        )
    
    @computed_field
    @property
    def progress_percentage(self) -> Optional[float]:
        """Contest progress as percentage (0-100)"""
        if self.start_time and self.end_time:
            total_duration = (self.end_time - self.start_time).total_seconds()
            elapsed = (datetime.utcnow() - self.start_time).total_seconds()
            if total_duration > 0:
                return min(100.0, max(0.0, (elapsed / total_duration) * 100))
        return None
    
    class Config:
        from_attributes = True
        use_enum_values = True


class ContestInDB(ContestResponse):
    """Contest database model"""
    pass


class ContestListResponse(BaseModel):
    """Contest list response with pagination"""
    
    contests: List[ContestResponse]
    total: int
    page: int
    size: int
    total_pages: int
    
    @computed_field
    @property
    def has_next_page(self) -> bool:
        """Check if there's a next page"""
        return self.page < self.total_pages
    
    @computed_field
    @property
    def has_previous_page(self) -> bool:
        """Check if there's a previous page"""
        return self.page > 1
    
    @computed_field
    @property
    def next_page(self) -> Optional[int]:
        """Get next page number"""
        return self.page + 1 if self.has_next_page else None
    
    @computed_field
    @property
    def previous_page(self) -> Optional[int]:
        """Get previous page number"""
        return self.page - 1 if self.has_previous_page else None
    
    class Config:
        from_attributes = True


class ContestSummary(BaseModel):
    """Contest summary for dashboard views"""
    
    id: int
    name: str
    status: ContestStatus
    entry_count: int
    start_time: datetime
    end_time: datetime
    is_winner_selected: bool
    
    @computed_field
    @property
    def is_active(self) -> bool:
        """Check if contest is active"""
        return self.status == ContestStatus.ACTIVE
    
    class Config:
        from_attributes = True
        use_enum_values = True
