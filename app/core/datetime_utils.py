"""
Datetime utilities for consistent UTC handling across the application.

This module ensures all datetimes are properly handled as UTC throughout
the application, regardless of SQLite's timezone limitations.
"""

from datetime import datetime
import pytz
from typing import Optional


def utc_now() -> datetime:
    """
    Get current UTC time as timezone-aware datetime.
    
    Returns:
        datetime: Current UTC time with timezone info
    """
    return datetime.now(pytz.UTC)


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Ensure a datetime is timezone-aware and in UTC.
    
    Args:
        dt: Input datetime (can be naive or timezone-aware)
        
    Returns:
        datetime: UTC timezone-aware datetime, or None if input is None
    """
    if dt is None:
        return None
    
    if dt.tzinfo is None:
        # Naive datetime - assume it's already UTC and add timezone info
        return pytz.UTC.localize(dt)
    
    # Already timezone-aware - convert to UTC
    return dt.astimezone(pytz.UTC)


def to_utc_string(dt: Optional[datetime]) -> Optional[str]:
    """
    Convert datetime to UTC ISO string with timezone suffix.
    
    Args:
        dt: Input datetime
        
    Returns:
        str: ISO format string with 'Z' suffix, or None if input is None
    """
    if dt is None:
        return None
    
    utc_dt = ensure_utc(dt)
    return utc_dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')


def from_utc_string(iso_string: Optional[str]) -> Optional[datetime]:
    """
    Parse UTC ISO string to timezone-aware datetime.
    
    Args:
        iso_string: ISO format string (with or without timezone suffix)
        
    Returns:
        datetime: UTC timezone-aware datetime, or None if input is None
    """
    if not iso_string:
        return None
    
    # Handle various ISO formats
    iso_string = iso_string.strip()
    
    # Remove 'Z' suffix if present
    if iso_string.endswith('Z'):
        iso_string = iso_string[:-1]
    
    # Remove timezone offset if present
    if '+' in iso_string:
        iso_string = iso_string.split('+')[0]
    elif iso_string.count('-') > 2:  # Has timezone offset like -05:00
        parts = iso_string.split('-')
        iso_string = '-'.join(parts[:-1])
    
    try:
        # Parse as naive datetime and assume UTC
        dt = datetime.fromisoformat(iso_string)
        return pytz.UTC.localize(dt)
    except ValueError:
        # Try without microseconds
        try:
            dt = datetime.strptime(iso_string, '%Y-%m-%dT%H:%M:%S')
            return pytz.UTC.localize(dt)
        except ValueError:
            return None


def format_for_display(dt: Optional[datetime], timezone_name: str = 'UTC') -> Optional[str]:
    """
    Format datetime for display in specified timezone.
    
    Args:
        dt: UTC datetime to format
        timezone_name: Target timezone name (e.g., 'America/New_York')
        
    Returns:
        str: Formatted datetime string, or None if input is None
    """
    if dt is None:
        return None
    
    utc_dt = ensure_utc(dt)
    
    if timezone_name == 'UTC':
        target_tz = pytz.UTC
    else:
        try:
            target_tz = pytz.timezone(timezone_name)
        except pytz.UnknownTimeZoneError:
            target_tz = pytz.UTC
    
    local_dt = utc_dt.astimezone(target_tz)
    return local_dt.strftime('%Y-%m-%d %H:%M:%S %Z')


def parse_admin_input(datetime_local: str, admin_timezone: str) -> datetime:
    """
    Parse admin datetime input (from datetime-local) to UTC.
    
    Args:
        datetime_local: Datetime string from HTML datetime-local input
        admin_timezone: Admin's timezone (e.g., 'America/New_York')
        
    Returns:
        datetime: UTC timezone-aware datetime
    """
    # Parse the local datetime
    try:
        naive_dt = datetime.fromisoformat(datetime_local)
    except ValueError:
        # Try without seconds
        naive_dt = datetime.strptime(datetime_local, '%Y-%m-%dT%H:%M')
    
    # Localize to admin's timezone
    try:
        admin_tz = pytz.timezone(admin_timezone)
    except pytz.UnknownTimeZoneError:
        admin_tz = pytz.UTC
    
    local_dt = admin_tz.localize(naive_dt)
    
    # Convert to UTC
    return local_dt.astimezone(pytz.UTC)


def migrate_naive_datetime(naive_dt: datetime, assume_timezone: str = 'UTC') -> datetime:
    """
    Migrate existing naive datetime to timezone-aware UTC.
    
    This function is used to fix existing database records that were
    stored without timezone information.
    
    Args:
        naive_dt: Naive datetime from database
        assume_timezone: Timezone to assume for the naive datetime
        
    Returns:
        datetime: UTC timezone-aware datetime
    """
    if naive_dt.tzinfo is not None:
        # Already timezone-aware
        return naive_dt.astimezone(pytz.UTC)
    
    # Assume the naive datetime is in the specified timezone
    try:
        source_tz = pytz.timezone(assume_timezone)
    except pytz.UnknownTimeZoneError:
        source_tz = pytz.UTC
    
    localized_dt = source_tz.localize(naive_dt)
    return localized_dt.astimezone(pytz.UTC)
