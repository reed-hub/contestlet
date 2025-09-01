"""
Admin-specific response models with type safety.
Provides standardized responses for all admin endpoints.
"""

from typing import List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from app.shared.types.responses import APIResponse, PaginatedResponse
from app.schemas.role_system import UserWithRole, UserWithRoleAndCompany
from app.schemas.admin import NotificationLogResponse as NotificationLog


class AdminDashboardData(BaseModel):
    """Admin dashboard data structure"""
    statistics: Dict[str, int] = Field(..., description="System statistics")
    recent_contests: List[Dict[str, Any]] = Field(..., description="Recent contests")


class AdminDashboardResponse(APIResponse[AdminDashboardData]):
    """Type-safe response for admin dashboard"""
    pass


class AdminStatisticsResponse(APIResponse[Dict[str, Any]]):
    """Type-safe response for system statistics"""
    pass


class UserManagementResponse(APIResponse[List[UserWithRoleAndCompany]]):
    """Type-safe response for user management with company data"""
    pass


class NotificationLogResponse(APIResponse[List[NotificationLog]]):
    """Type-safe response for notification logs"""
    pass


class CampaignImportData(BaseModel):
    """Campaign import result data"""
    contests_created: int = Field(..., description="Number of contests created")
    contests_updated: int = Field(0, description="Number of contests updated")
    errors: List[str] = Field(default_factory=list, description="Import errors")


class CampaignImportResponse(APIResponse[CampaignImportData]):
    """Type-safe response for campaign import"""
    pass


class AdminAuthCheckResponse(APIResponse[Dict[str, Any]]):
    """Type-safe response for admin auth check"""
    pass


class WinnerNotificationResponse(APIResponse[Dict[str, Any]]):
    """Type-safe response for winner notifications"""
    pass


class FileValidationResponse(APIResponse[Dict[str, Any]]):
    """Type-safe response for file validation"""
    pass
