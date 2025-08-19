import math
from typing import Tuple


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees) using the Haversine formula.
    
    Returns distance in miles.
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in miles
    r = 3956
    
    return c * r


def is_within_radius(
    center_lat: float, 
    center_lon: float, 
    point_lat: float, 
    point_lon: float, 
    radius_miles: float
) -> bool:
    """
    Check if a point is within a given radius of a center point.
    
    Args:
        center_lat: Latitude of center point
        center_lon: Longitude of center point
        point_lat: Latitude of point to check
        point_lon: Longitude of point to check
        radius_miles: Radius in miles
    
    Returns:
        True if point is within radius, False otherwise
    """
    distance = haversine_distance(center_lat, center_lon, point_lat, point_lon)
    return distance <= radius_miles


def validate_coordinates(lat: float, lon: float) -> bool:
    """
    Validate latitude and longitude coordinates.
    
    Args:
        lat: Latitude (-90 to 90)
        lon: Longitude (-180 to 180)
    
    Returns:
        True if coordinates are valid, False otherwise
    """
    return -90 <= lat <= 90 and -180 <= lon <= 180
