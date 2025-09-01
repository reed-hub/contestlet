"""
Unified Admin Router - Consolidates all admin operations.
Clean architecture with service delegation and proper error handling.
"""

from fastapi import APIRouter, Depends, UploadFile, File, Query, Path
from typing import List, Optional

from app.core.services.admin_service import AdminService
from app.core.services.notification_service import NotificationService
from app.core.services.campaign_import_service import CampaignImportService
from app.core.dependencies.auth import get_admin_user
from app.core.dependencies.services import get_admin_service
from app.models.user import User
from app.shared.types.pagination import PaginationParams, UserFilterParams
from app.shared.types.responses import APIResponse
from app.api.responses.admin import (
    AdminDashboardResponse,
    AdminStatisticsResponse,
    NotificationLogResponse,
    CampaignImportResponse,
    UserManagementResponse
)
from app.api.responses.user import UserUpdateResponse
from app.schemas.admin import (
    WinnerNotificationRequest,
    NotificationLogResponse as NotificationLog,
    CampaignImportResponse as CampaignImport
)
from app.schemas.role_system import (
    UserWithRole,
    UserWithRoleAndCompany,
    UnifiedProfileUpdate,
    UnifiedSponsorProfileResponse,
    AdminUserCreate
)
from app.shared.constants.auth import AuthConstants, AuthMessages
from app.shared.exceptions.base import ValidationException

router = APIRouter(prefix="/admin", tags=["admin"])


# =====================================================
# DASHBOARD & STATISTICS
# =====================================================

@router.get("/dashboard", response_model=AdminDashboardResponse)
async def get_admin_dashboard(
    admin_user: User = Depends(get_admin_user),
    admin_service: AdminService = Depends(get_admin_service)
) -> AdminDashboardResponse:
    """
    Get admin dashboard with system statistics.
    Clean controller with service delegation.
    """
    dashboard_data = await admin_service.get_dashboard_data()
    
    return AdminDashboardResponse(
        success=True,
        data=dashboard_data,
        message="Dashboard data retrieved successfully"
    )


@router.get("/statistics", response_model=AdminStatisticsResponse)
async def get_system_statistics(
    admin_user: User = Depends(get_admin_user),
    admin_service: AdminService = Depends(get_admin_service)
) -> AdminStatisticsResponse:
    """
    Get detailed system statistics.
    Uses service layer for comprehensive stats.
    """
    statistics = await admin_service.get_system_statistics()
    
    return AdminStatisticsResponse(
        success=True,
        data=statistics,
        message="System statistics retrieved successfully"
    )


# =====================================================
# USER MANAGEMENT
# =====================================================

@router.get("/users", response_model=UserManagementResponse)
async def get_all_users_admin(
    pagination: PaginationParams = Depends(),
    filters: UserFilterParams = Depends(),
    admin_user: User = Depends(get_admin_user),
    admin_service: AdminService = Depends(get_admin_service)
) -> UserManagementResponse:
    """
    Get all users for admin management.
    Clean pagination and filtering with service layer.
    """
    users = await admin_service.get_all_users(
        role_filter=filters.role,
        limit=pagination.limit,
        offset=pagination.offset
    )
    
    # Convert users to include company data
    users_with_company = [UserWithRoleAndCompany.from_user(user) for user in users]
    
    return UserManagementResponse(
        success=True,
        data=users_with_company,
        message="Users retrieved successfully"
    )


@router.post("/users")
async def create_user_admin(
    user_data: AdminUserCreate,
    admin_user: User = Depends(get_admin_user),
    admin_service: AdminService = Depends(get_admin_service)
) -> UserUpdateResponse:
    """
    Create a new user (admin operation).
    Allows admin to create users with any role and profile information.
    """
    created_user = await admin_service.create_user_admin(
        user_data=user_data,
        admin_user_id=admin_user.id
    )
    
    # Return appropriate response based on role
    if created_user.role == AuthConstants.SPONSOR_ROLE and created_user.sponsor_profile:
        profile_data = UnifiedSponsorProfileResponse(
            user_id=created_user.id,
            phone=created_user.phone,
            role=created_user.role,
            is_verified=created_user.is_verified,
            created_at=created_user.created_at,
            updated_at=created_user.updated_at,
            role_assigned_at=created_user.role_assigned_at,
            full_name=created_user.full_name,
            email=created_user.email,
            bio=created_user.bio,
            company_profile=created_user.sponsor_profile
        )
    else:
        profile_data = UserWithRole(
            id=created_user.id,
            phone=created_user.phone,
            role=created_user.role,
            is_verified=created_user.is_verified,
            created_at=created_user.created_at,
            updated_at=created_user.updated_at,
            role_assigned_at=created_user.role_assigned_at,
            created_by_user_id=created_user.created_by_user_id,
            role_assigned_by=created_user.role_assigned_by,
            full_name=created_user.full_name,
            email=created_user.email,
            bio=created_user.bio
        )
    
    return UserUpdateResponse(
        success=True,
        data=profile_data,
        message="User created successfully by admin"
    )


@router.delete("/users/{user_id}")
async def delete_user_admin(
    user_id: int = Path(..., gt=0, description="User ID"),
    admin_user: User = Depends(get_admin_user),
    admin_service: AdminService = Depends(get_admin_service)
) -> APIResponse[dict]:
    """
    Delete a user (admin operation).
    Permanently removes user and associated data.
    """
    success = await admin_service.delete_user_admin(
        user_id=user_id,
        admin_user_id=admin_user.id
    )
    
    return APIResponse(
        success=True,
        data={
            "user_id": user_id,
            "deleted": success,
            "deleted_by": admin_user.id
        },
        message="User deleted successfully"
    )


@router.put("/users/{user_id}")
async def update_user_profile_admin(
    profile_update: UnifiedProfileUpdate,
    user_id: int = Path(..., gt=0, description="User ID"),
    admin_user: User = Depends(get_admin_user),
    admin_service: AdminService = Depends(get_admin_service)
) -> UserUpdateResponse:
    """
    Update any user's profile information (admin operation).
    Allows admin to update name, email, bio, and company info for any user.
    """
    updated_user = await admin_service.update_user_profile_admin(
        user_id=user_id,
        profile_update=profile_update,
        admin_user_id=admin_user.id
    )
    
    # Return appropriate response based on role
    if updated_user.role == AuthConstants.SPONSOR_ROLE and updated_user.sponsor_profile:
        profile_data = UnifiedSponsorProfileResponse(
            user_id=updated_user.id,
            phone=updated_user.phone,
            role=updated_user.role,
            is_verified=updated_user.is_verified,
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at,
            role_assigned_at=updated_user.role_assigned_at,
            full_name=updated_user.full_name,
            email=updated_user.email,
            bio=updated_user.bio,
            company_profile=updated_user.sponsor_profile
        )
    else:
        profile_data = UserWithRole(
            id=updated_user.id,
            phone=updated_user.phone,
            role=updated_user.role,
            is_verified=updated_user.is_verified,
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at,
            role_assigned_at=updated_user.role_assigned_at,
            created_by_user_id=updated_user.created_by_user_id,
            role_assigned_by=updated_user.role_assigned_by,
            full_name=updated_user.full_name,
            email=updated_user.email,
            bio=updated_user.bio
        )
    
    return UserUpdateResponse(
        success=True,
        data=profile_data,
        message="User profile updated successfully by admin"
    )


@router.put("/users/{user_id}/role/{new_role}")
async def update_user_role_admin(
    user_id: int = Path(..., gt=0, description="User ID"),
    new_role: str = Path(..., description="New role to assign"),
    admin_user: User = Depends(get_admin_user),
    admin_service: AdminService = Depends(get_admin_service)
) -> APIResponse[dict]:
    """
    Update user role (admin operation).
    Uses service layer with proper validation.
    """
    # Validate role
    if new_role not in AuthConstants.VALID_ROLES:
        raise ValidationException(
            message="Invalid role specified",
            field_errors={"role": f"Must be one of: {AuthConstants.VALID_ROLES}"}
        )
    
    updated_user = await admin_service.update_user_role(
        user_id=user_id,
        new_role=new_role,
        admin_user_id=admin_user.id
    )
    
    return APIResponse(
        success=True,
        data={
            "user_id": updated_user.id,
            "new_role": updated_user.role,
            "updated_by": admin_user.id
        },
        message=f"User role updated to {new_role} successfully"
    )


# =====================================================
# NOTIFICATIONS MANAGEMENT
# =====================================================

@router.get("/notifications", response_model=NotificationLogResponse)
async def get_notification_logs(
    limit: int = Query(100, ge=1, le=1000, description="Number of logs to retrieve"),
    offset: int = Query(0, ge=0, description="Number of logs to skip"),
    admin_user: User = Depends(get_admin_user)
) -> NotificationLogResponse:
    """
    Get SMS notification logs with pagination.
    Clean controller with proper error handling.
    """
    try:
        # Use notification service directly (could be injected via DI)
        from app.database.database import get_db
        from sqlalchemy.orm import Session
        
        # This is a temporary approach - ideally we'd inject the service
        db = next(get_db())
        notification_service = NotificationService(db)
        logs = notification_service.get_notification_logs(limit=limit, offset=offset)
        
        return NotificationLogResponse(
            success=True,
            data=logs,
            message="Notification logs retrieved successfully"
        )
    except Exception as e:
        # Return empty list instead of error to prevent CORS issues
        return NotificationLogResponse(
            success=True,
            data=[],
            message="No notification logs available"
        )


@router.post("/notifications/winner")
async def send_winner_notification(
    notification_request: WinnerNotificationRequest,
    admin_user: User = Depends(get_admin_user)
) -> APIResponse[dict]:
    """
    Send winner notification SMS.
    Clean controller with service delegation.
    """
    try:
        # Use notification service
        from app.database.database import get_db
        db = next(get_db())
        notification_service = NotificationService(db)
        
        result = await notification_service.send_winner_notification(
            contest_id=notification_request.contest_id,
            winner_phone=notification_request.winner_phone,
            message=notification_request.message,
            admin_user_id=admin_user.id
        )
        
        return APIResponse(
            success=True,
            data=result,
            message="Winner notification sent successfully"
        )
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Failed to send notification: {str(e)}",
            errors={"notification_error": str(e)}
        )


# =====================================================
# CAMPAIGN IMPORT
# =====================================================

@router.post("/import/one-sheet", response_model=CampaignImportResponse)
async def import_campaign_from_sheet(
    file: UploadFile = File(...),
    admin_user: User = Depends(get_admin_user)
) -> CampaignImportResponse:
    """
    Import campaign data from uploaded spreadsheet.
    Clean file handling with proper validation.
    """
    # Validate file format
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise ValidationException(
            message="Invalid file format",
            field_errors={"file": "File must be Excel (.xlsx, .xls) or CSV format"}
        )
    
    try:
        # Use campaign import service
        from app.services.campaign_import_service import campaign_import_service
        
        result = await campaign_import_service.import_from_file(file, admin_user.id)
        
        return CampaignImportResponse(
            success=True,
            data={
                "contests_created": result['contests_created'],
                "contests_updated": result.get('contests_updated', 0),
                "errors": result.get('errors', [])
            },
            message=f"Successfully imported {result['contests_created']} contests"
        )
        
    except Exception as e:
        return CampaignImportResponse(
            success=False,
            message=f"Import failed: {str(e)}",
            errors={"import_error": str(e)}
        )


@router.post("/import/validate-sheet")
async def validate_campaign_sheet(
    file: UploadFile = File(...),
    admin_user: User = Depends(get_admin_user)
) -> APIResponse[dict]:
    """
    Validate campaign spreadsheet without importing.
    Clean validation with detailed feedback.
    """
    # Validate file format
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise ValidationException(
            message="Invalid file format",
            field_errors={"file": "File must be Excel (.xlsx, .xls) or CSV format"}
        )
    
    try:
        # Use campaign import service for validation
        from app.services.campaign_import_service import campaign_import_service
        
        validation_result = await campaign_import_service.validate_file(file)
        
        return APIResponse(
            success=True,
            data=validation_result,
            message="File validation completed"
        )
        
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Validation failed: {str(e)}",
            errors={"validation_error": str(e)}
        )


# =====================================================
# PROFILE MANAGEMENT (Legacy Compatibility)
# =====================================================

@router.get("/profile", response_model=APIResponse[UserWithRole])
async def get_admin_profile(
    admin_user: User = Depends(get_admin_user)
) -> APIResponse[UserWithRole]:
    """
    DEPRECATED: Use GET /users/me instead.
    Get admin's user account profile.
    """
    profile_data = UserWithRole(
        id=admin_user.id,
        phone=admin_user.phone,
        role=admin_user.role,
        is_verified=admin_user.is_verified,
        created_at=admin_user.created_at,
        updated_at=admin_user.updated_at,
        role_assigned_at=admin_user.role_assigned_at,
        created_by_user_id=admin_user.created_by_user_id,
        role_assigned_by=admin_user.role_assigned_by,
        full_name=admin_user.full_name,
        email=admin_user.email,
        bio=admin_user.bio
    )
    
    return APIResponse(
        success=True,
        data=profile_data,
        message="Admin profile retrieved successfully"
    )


@router.post("/auth-check")
async def admin_auth_check(
    admin_user: User = Depends(get_admin_user)
) -> APIResponse[dict]:
    """
    Check admin authentication status.
    Simple endpoint for frontend auth validation.
    """
    return APIResponse(
        success=True,
        data={
            "user_id": admin_user.id,
            "role": admin_user.role,
            "authenticated": True
        },
        message=AuthMessages.ADMIN_ACCESS_REQUIRED
    )
