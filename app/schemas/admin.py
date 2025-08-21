from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List
from .contest import ContestBase
from .official_rules import OfficialRulesCreate, OfficialRulesUpdate, OfficialRulesResponse


class AdminContestCreate(ContestBase):
    """Schema for admin contest creation with required official rules"""
    official_rules: OfficialRulesCreate = Field(..., description="Official contest rules (required)")
    
    # Contest configuration (Phase 1 form support)
    contest_type: Optional[str] = Field("general", description="Contest type (general, sweepstakes, instant_win)")
    entry_method: Optional[str] = Field("sms", description="Entry method (sms, email, web_form)")
    winner_selection_method: Optional[str] = Field("random", description="Winner selection method (random, scheduled, instant)")
    
    # Entry limitations and validation
    minimum_age: Optional[int] = Field(18, ge=13, le=100, description="Minimum age requirement")
    max_entries_per_person: Optional[int] = Field(None, ge=1, description="Maximum entries per person (null = unlimited)")
    total_entry_limit: Optional[int] = Field(None, ge=1, description="Total entry limit (null = unlimited)")
    
    # Additional contest details
    consolation_offer: Optional[str] = Field(None, description="Consolation prize/offer for non-winners")
    geographic_restrictions: Optional[str] = Field(None, description="Geographic limitations or restrictions")
    contest_tags: Optional[List[str]] = Field(None, description="Tags for contest organization and filtering")
    promotion_channels: Optional[List[str]] = Field(None, description="Promotion channels used for marketing")
    
    @validator('contest_type')
    def validate_contest_type(cls, v):
        valid_types = ['general', 'sweepstakes', 'instant_win']
        if v not in valid_types:
            raise ValueError(f'Contest type must be one of: {valid_types}')
        return v
    
    @validator('entry_method')
    def validate_entry_method(cls, v):
        valid_methods = ['sms', 'email', 'web_form']
        if v not in valid_methods:
            raise ValueError(f'Entry method must be one of: {valid_methods}')
        return v
    
    @validator('winner_selection_method')
    def validate_winner_selection_method(cls, v):
        valid_methods = ['random', 'scheduled', 'instant']
        if v not in valid_methods:
            raise ValueError(f'Winner selection method must be one of: {valid_methods}')
        return v
    
    @validator('minimum_age')
    def validate_minimum_age(cls, v):
        if v < 13:  # COPPA compliance
            raise ValueError('Minimum age cannot be less than 13 for legal compliance')
        return v


class AdminContestUpdate(BaseModel):
    """Schema for admin contest updates"""
    name: Optional[str] = Field(None, description="Contest name")
    description: Optional[str] = Field(None, description="Contest description")
    location: Optional[str] = Field(None, description="Contest location")
    latitude: Optional[float] = Field(None, description="Latitude for geolocation")
    longitude: Optional[float] = Field(None, description="Longitude for geolocation")
    start_time: Optional[datetime] = Field(None, description="Contest start time")
    end_time: Optional[datetime] = Field(None, description="Contest end time")
    prize_description: Optional[str] = Field(None, description="Prize description")
# Note: Active status is now computed automatically based on start/end times and winner selection
    official_rules: Optional[OfficialRulesUpdate] = Field(None, description="Official rules updates")

    @validator('latitude')
    def validate_latitude(cls, v):
        if v is not None and not (-90 <= v <= 90):
            raise ValueError('Latitude must be between -90 and 90')
        return v

    @validator('longitude')
    def validate_longitude(cls, v):
        if v is not None and not (-180 <= v <= 180):
            raise ValueError('Longitude must be between -180 and 180')
        return v


class AdminContestResponse(BaseModel):
    """Enhanced contest response for admin operations"""
    id: int
    name: str
    description: Optional[str]
    location: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    start_time: datetime
    end_time: datetime
    prize_description: Optional[str]
    active: bool
    created_at: datetime
    entry_count: int = Field(..., description="Number of entries for this contest")
    official_rules: Optional[OfficialRulesResponse] = Field(None, description="Official contest rules")
    status: Optional[str] = Field(None, description="Contest status: active, inactive, ended, upcoming")
    
    # Winner information
    winner_entry_id: Optional[int] = Field(None, description="ID of winning entry")
    winner_phone: Optional[str] = Field(None, description="Winner's phone number (masked)")
    winner_selected_at: Optional[datetime] = Field(None, description="When winner was selected")
    
    # Timezone metadata
    created_timezone: Optional[str] = Field(None, description="Timezone used when contest was created")
    admin_user_id: Optional[str] = Field(None, description="Admin who created the contest")
    
    def __init__(self, **data):
        # Compute status before creating the object based purely on time
        if 'status' not in data:
            from app.core.datetime_utils import utc_now
            now = utc_now()
            start_time = data.get('start_time')
            end_time = data.get('end_time')
            winner_selected_at = data.get('winner_selected_at')
            
            # Make datetime objects timezone-aware for comparison if they aren't already
            if start_time and start_time.tzinfo is None:
                from datetime import timezone
                start_time = start_time.replace(tzinfo=timezone.utc)
            if end_time and end_time.tzinfo is None:
                from datetime import timezone
                end_time = end_time.replace(tzinfo=timezone.utc)
            
            # Simplified time-based status calculation
            if winner_selected_at:
                data['status'] = "complete"
            elif end_time and end_time <= now:
                data['status'] = "ended"
            elif start_time and start_time > now:
                data['status'] = "upcoming"
            else:
                data['status'] = "active"
        
        super().__init__(**data)
    
    class Config:
        from_attributes = True


class WinnerSelectionResponse(BaseModel):
    """Response for winner selection"""
    success: bool
    message: str
    winner_entry_id: Optional[int] = None
    winner_user_phone: Optional[str] = None
    total_entries: int


class AdminEntryResponse(BaseModel):
    """Admin response for contest entries with user details"""
    id: int
    contest_id: int
    user_id: int
    phone_number: str = Field(..., description="User's phone number")
    created_at: datetime
    selected: bool = Field(default=False, description="Whether this entry was selected as winner")
    status: str = Field(default="active", description="Entry status: active, winner, disqualified")
    
    class Config:
        from_attributes = True


class WinnerNotificationRequest(BaseModel):
    """Request to notify a contest winner via SMS"""
    entry_id: int = Field(..., description="ID of the winning entry")
    message: str = Field(..., min_length=1, max_length=1600, description="SMS message to send to winner")
    test_mode: bool = Field(default=False, description="If true, simulate sending without actually sending SMS")
    
    @validator('message')
    def validate_message(cls, v):
        if not v.strip():
            raise ValueError('Message cannot be empty')
        return v.strip()


class WinnerNotificationResponse(BaseModel):
    """Response from winner notification"""
    success: bool = Field(..., description="Whether the notification was sent successfully")
    message: str = Field(..., description="Status message")
    entry_id: int = Field(..., description="ID of the entry that was notified")
    contest_id: int = Field(..., description="ID of the contest")
    winner_phone: str = Field(..., description="Phone number of the winner (masked for privacy)")
    sms_status: str = Field(..., description="SMS delivery status")
    test_mode: bool = Field(..., description="Whether this was sent in test mode")
    notification_id: int = Field(..., description="ID of the notification record")
    twilio_sid: Optional[str] = Field(None, description="Twilio message SID (if real SMS)")
    notification_sent_at: datetime = Field(default_factory=datetime.utcnow, description="When the notification was sent")


class AdminAuthResponse(BaseModel):
    """Response for admin authentication"""
    message: str
    admin: bool = True


class NotificationLogResponse(BaseModel):
    """Response for notification logs"""
    id: int
    contest_id: int
    user_id: int
    entry_id: Optional[int]
    message: str
    notification_type: str
    status: str
    twilio_sid: Optional[str]
    error_message: Optional[str]
    test_mode: bool
    sent_at: datetime
    admin_user_id: Optional[str]
    
    # Related data
    contest_name: Optional[str] = Field(None, description="Name of the related contest")
    user_phone: Optional[str] = Field(None, description="Masked phone number of recipient")
    
    class Config:
        from_attributes = True


class ContestDeletionSummary(BaseModel):
    """Summary of what was deleted during contest deletion"""
    entries_deleted: int = Field(..., description="Number of contest entries deleted")
    notifications_deleted: int = Field(..., description="Number of SMS notifications deleted")
    official_rules_deleted: int = Field(..., description="Number of official rules deleted (0 or 1)")
    dependencies_cleared: int = Field(..., description="Total number of dependent records cleared")


class ContestDeleteResponse(BaseModel):
    """Response for successful contest deletion"""
    status: str = Field("success", description="Operation status")
    message: str = Field(..., description="Human-readable success message")
    deleted_contest_id: int = Field(..., description="ID of the deleted contest")
    cleanup_summary: ContestDeletionSummary = Field(..., description="Summary of cleanup actions performed")
