"""
Timezone and Admin Profile Schemas for timezone-aware contest management
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class AdminTimezonePreferences(BaseModel):
    """Schema for admin timezone preferences"""
    timezone: str = Field(..., description="IANA timezone identifier (e.g., 'America/New_York')")
    timezone_auto_detect: bool = Field(default=True, description="Whether to auto-detect timezone from browser")
    
    @validator('timezone')
    def validate_timezone(cls, v):
        """Validate that timezone is a valid IANA timezone identifier"""
        # List of common/supported timezones
        valid_timezones = [
            'UTC',
            'America/New_York',    # Eastern Time
            'America/Chicago',     # Central Time  
            'America/Denver',      # Mountain Time
            'America/Los_Angeles', # Pacific Time
            'America/Phoenix',     # Arizona Time
            'America/Anchorage',   # Alaska Time
            'Pacific/Honolulu',    # Hawaii Time
            'Europe/London',       # GMT/BST
            'Europe/Paris',        # CET/CEST
            'Europe/Berlin',       # CET/CEST
            'Asia/Tokyo',          # JST
            'Asia/Shanghai',       # CST
            'Australia/Sydney',    # AEST/AEDT
            'Canada/Eastern',      # Eastern Time (Canada)
            'Canada/Central',      # Central Time (Canada)
            'Canada/Mountain',     # Mountain Time (Canada)
            'Canada/Pacific',      # Pacific Time (Canada)
        ]
        
        if v not in valid_timezones:
            raise ValueError(f'Unsupported timezone: {v}. Supported timezones: {", ".join(valid_timezones)}')
        
        return v


class AdminProfileResponse(BaseModel):
    """Response schema for admin profile data"""
    admin_user_id: str
    timezone: str
    timezone_auto_detect: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AdminProfileCreate(AdminTimezonePreferences):
    """Schema for creating admin profile"""
    pass


class AdminProfileUpdate(BaseModel):
    """Schema for updating admin profile (all fields optional)"""
    timezone: Optional[str] = None
    timezone_auto_detect: Optional[bool] = None
    
    @validator('timezone')
    def validate_timezone(cls, v):
        """Validate timezone if provided"""
        if v is not None:
            # Reuse the same validation logic
            return AdminTimezonePreferences.validate_timezone(v)
        return v


class TimezoneInfo(BaseModel):
    """Schema for timezone information and conversion utilities"""
    timezone: str = Field(..., description="IANA timezone identifier")
    display_name: str = Field(..., description="Human-readable timezone name")
    current_time: datetime = Field(..., description="Current time in this timezone")
    utc_offset: str = Field(..., description="UTC offset (e.g., '-05:00')")
    is_dst: bool = Field(default=False, description="Whether daylight saving time is currently active")


class TimezoneListResponse(BaseModel):
    """Response schema for supported timezones list"""
    timezones: list[TimezoneInfo]
    default_timezone: str = "UTC"
    auto_detected_timezone: Optional[str] = None
