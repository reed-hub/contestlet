"""
Timezone utilities for backend timezone handling and conversion
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional
import pytz
from app.schemas.user_timezone import TimezoneInfo


# Supported timezones with display names
SUPPORTED_TIMEZONES = {
    'UTC': 'Coordinated Universal Time (UTC)',
    'America/New_York': 'Eastern Time (ET)',
    'America/Chicago': 'Central Time (CT)',
    'America/Denver': 'Mountain Time (MT)',
    'America/Los_Angeles': 'Pacific Time (PT)',
    'America/Phoenix': 'Arizona Time (MST)',
    'America/Anchorage': 'Alaska Time (AKT)',
    'Pacific/Honolulu': 'Hawaii Time (HST)',
    'Europe/London': 'Greenwich Mean Time (GMT)',
    'Europe/Paris': 'Central European Time (CET)',
    'Europe/Berlin': 'Central European Time (CET)',
    'Asia/Tokyo': 'Japan Standard Time (JST)',
    'Asia/Shanghai': 'China Standard Time (CST)',
    'Australia/Sydney': 'Australian Eastern Time (AET)',
    'Canada/Eastern': 'Eastern Time (Canada)',
    'Canada/Central': 'Central Time (Canada)',
    'Canada/Mountain': 'Mountain Time (Canada)',
    'Canada/Pacific': 'Pacific Time (Canada)',
}


def get_supported_timezones() -> List[TimezoneInfo]:
    """
    Get list of supported timezones with current time information
    
    Returns:
        List of TimezoneInfo objects with timezone details
    """
    timezones = []
    utc_now = datetime.now(timezone.utc)
    
    for tz_name, display_name in SUPPORTED_TIMEZONES.items():
        try:
            tz = pytz.timezone(tz_name)
            current_time = utc_now.astimezone(tz)
            
            # Calculate UTC offset
            offset = current_time.strftime('%z')
            formatted_offset = f"{offset[:3]}:{offset[3:]}" if offset else "+00:00"
            
            # Check if DST is active
            is_dst = bool(current_time.dst())
            
            timezones.append(TimezoneInfo(
                timezone=tz_name,
                display_name=display_name,
                current_time=current_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
                utc_offset=formatted_offset,
                is_dst=is_dst
            ))
        except Exception as e:
            # Skip invalid timezones
            print(f"Warning: Could not process timezone {tz_name}: {e}")
            continue
    
    return timezones


def validate_timezone(timezone_name: str) -> bool:
    """
    Validate if a timezone name is supported
    
    Args:
        timezone_name: IANA timezone identifier
        
    Returns:
        True if timezone is supported, False otherwise
    """
    return timezone_name in SUPPORTED_TIMEZONES


def convert_to_timezone(utc_datetime: datetime, target_timezone: str) -> datetime:
    """
    Convert UTC datetime to target timezone
    
    Args:
        utc_datetime: UTC datetime object
        target_timezone: IANA timezone identifier
        
    Returns:
        Datetime object in target timezone
    """
    if not validate_timezone(target_timezone):
        raise ValueError(f"Unsupported timezone: {target_timezone}")
    
    # Ensure the datetime is timezone-aware and in UTC
    if utc_datetime.tzinfo is None:
        utc_datetime = utc_datetime.replace(tzinfo=timezone.utc)
    elif utc_datetime.tzinfo != timezone.utc:
        utc_datetime = utc_datetime.astimezone(timezone.utc)
    
    # Convert to target timezone
    target_tz = pytz.timezone(target_timezone)
    return utc_datetime.astimezone(target_tz)


def ensure_utc(dt: datetime) -> datetime:
    """
    Ensure datetime is in UTC timezone
    
    Args:
        dt: Datetime object (naive or timezone-aware)
        
    Returns:
        UTC datetime object
    """
    if dt.tzinfo is None:
        # Assume naive datetime is already UTC
        return dt.replace(tzinfo=timezone.utc)
    else:
        # Convert to UTC if it has timezone info
        return dt.astimezone(timezone.utc)


def get_current_time_in_timezone(timezone_name: str) -> datetime:
    """
    Get current time in specified timezone
    
    Args:
        timezone_name: IANA timezone identifier
        
    Returns:
        Current datetime in specified timezone
    """
    if not validate_timezone(timezone_name):
        raise ValueError(f"Unsupported timezone: {timezone_name}")
    
    utc_now = datetime.now(timezone.utc)
    return convert_to_timezone(utc_now, timezone_name)


def format_datetime_for_timezone(dt: datetime, timezone_name: str, format_string: str = "%Y-%m-%d %H:%M:%S %Z") -> str:
    """
    Format datetime for display in specified timezone
    
    Args:
        dt: UTC datetime object
        timezone_name: IANA timezone identifier
        format_string: strftime format string
        
    Returns:
        Formatted datetime string
    """
    local_dt = convert_to_timezone(dt, timezone_name)
    return local_dt.strftime(format_string)


def get_timezone_display_name(timezone_name: str) -> str:
    """
    Get display name for timezone
    
    Args:
        timezone_name: IANA timezone identifier
        
    Returns:
        Human-readable timezone display name
    """
    return SUPPORTED_TIMEZONES.get(timezone_name, timezone_name)
