"""
Universal User Timezone Schemas

Pydantic models for timezone preferences that work across all user roles.
Extends the admin-only timezone system to sponsors and regular users.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class UserTimezonePreferences(BaseModel):
    """Schema for user timezone preferences (all roles)"""
    timezone: Optional[str] = Field(None, description="IANA timezone identifier (e.g., 'America/New_York'). NULL uses system default (UTC)")
    timezone_auto_detect: bool = Field(default=True, description="Whether to auto-detect timezone from browser")
    
    @validator('timezone')
    def validate_timezone(cls, v):
        """Validate that timezone is a valid IANA timezone identifier"""
        if v is None:
            return v  # Allow None for system default
            
        # List of supported timezones (same as admin system for consistency)
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


class UserTimezoneUpdate(BaseModel):
    """Schema for updating user timezone preferences"""
    timezone: Optional[str] = Field(None, description="IANA timezone identifier or NULL for system default")
    timezone_auto_detect: Optional[bool] = Field(None, description="Whether to auto-detect timezone from browser")
    
    @validator('timezone')
    def validate_timezone(cls, v):
        """Use the same validation as UserTimezonePreferences"""
        return UserTimezonePreferences.validate_timezone(v)


class UserTimezoneResponse(BaseModel):
    """Schema for user timezone preference responses"""
    user_id: int
    timezone: Optional[str] = Field(None, description="Current timezone setting or NULL for system default")
    timezone_auto_detect: bool = Field(default=True, description="Auto-detect setting")
    effective_timezone: str = Field(default="UTC", description="Effective timezone (resolved from setting or default)")
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TimezoneInfo(BaseModel):
    """Schema for timezone information (used in timezone lists)"""
    timezone: str = Field(..., description="IANA timezone identifier")
    display_name: str = Field(..., description="Human-readable timezone name")
    current_time: str = Field(..., description="Current time in this timezone")
    utc_offset: str = Field(..., description="UTC offset (e.g., '-05:00')")
    is_dst: bool = Field(..., description="Whether currently observing daylight saving time")


class SupportedTimezonesResponse(BaseModel):
    """Schema for supported timezones list"""
    timezones: list[TimezoneInfo]
    default_timezone: str = Field(default="UTC", description="System default timezone")
    user_detected_timezone: Optional[str] = Field(None, description="Browser-detected timezone if available")


class TimezoneValidationRequest(BaseModel):
    """Schema for timezone validation requests (no validation applied)"""
    timezone: str = Field(..., description="Timezone to validate")


class TimezoneValidationResponse(BaseModel):
    """Schema for timezone validation responses"""
    timezone: str
    is_valid: bool
    display_name: Optional[str] = None
    current_time: Optional[str] = None
    utc_offset: Optional[str] = None
    error_message: Optional[str] = None
