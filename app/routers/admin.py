from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database.database import get_db
from app.models.user import User
from app.schemas.admin import AdminAuthResponse
from app.schemas.role_system import UserWithRole
from app.core.admin_auth import get_admin_user
from app.core.dependencies import get_admin_user as get_admin_user_dependency
from app.services.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard")
async def get_admin_dashboard(
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get admin dashboard data with statistics and recent activity"""
    admin_service = AdminService(db)
    dashboard_data = admin_service.get_admin_dashboard_data()
    return dashboard_data


@router.get("/statistics")
async def get_system_statistics(
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive system statistics"""
    admin_service = AdminService(db)
    stats = admin_service.get_system_statistics()
    return stats


@router.get("/users", response_model=List[UserWithRole])
async def get_all_users(
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db),
    limit: int = 100,
    role: str = None
):
    """Get all users with optional role filtering"""
    admin_service = AdminService(db)
    users = admin_service.get_all_users(limit=limit, role=role)
    return users


@router.get("/users/{user_id}", response_model=UserWithRole)
async def get_user_by_id(
    user_id: int,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get specific user by ID with admin access"""
    admin_service = AdminService(db)
    user = admin_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    role_update: dict,
    admin_user: dict = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Update user role with audit trail"""
    admin_service = AdminService(db)
    new_role = role_update.get("role")
    if not new_role:
        raise HTTPException(status_code=400, detail="Role is required")
    
    user = admin_service.update_user_role(user_id, new_role, admin_user["sub"])
    return {"message": f"User role updated to {new_role}", "user": user}


# Legacy endpoint for backward compatibility
@router.get("/auth", response_model=AdminAuthResponse)
async def admin_auth_check(admin_user: dict = Depends(get_admin_user)):
    """Check admin authentication status"""
    return AdminAuthResponse(message="Admin authentication successful")
