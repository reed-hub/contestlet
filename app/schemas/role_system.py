"""
Role System Schemas

Pydantic models for multi-tier role system including:
- User role management
- Sponsor profiles
- Role-based authentication
- Audit trail responses
"""

from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List, Literal
from enum import Enum


class UserRole(str, Enum):
    """Valid user roles in the system"""
    ADMIN = "admin"
    SPONSOR = "sponsor"
    USER = "user"


class ApprovalAction(str, Enum):
    """Valid contest approval actions"""
    APPROVED = "approved"
    REJECTED = "rejected"
    PENDING = "pending"


# =====================================================
# USER ROLE SCHEMAS
# =====================================================

class UserRoleUpdate(BaseModel):
    """Schema for updating user roles (admin only)"""
    role: UserRole = Field(..., description="New role to assign")
    reason: Optional[str] = Field(None, description="Reason for role change")


class UserWithRole(BaseModel):
    """Enhanced user schema with role information"""
    id: int
    phone: str
    role: UserRole
    is_verified: bool
    created_at: datetime
    role_assigned_at: datetime
    created_by_user_id: Optional[int] = None
    role_assigned_by: Optional[int] = None
    
    class Config:
        from_attributes = True


# =====================================================
# SPONSOR PROFILE SCHEMAS
# =====================================================

class SponsorProfileCreate(BaseModel):
    """Schema for creating sponsor profiles"""
    company_name: str = Field(..., min_length=2, max_length=255, description="Company name")
    website_url: Optional[str] = Field(None, max_length=500, description="Company website URL")
    logo_url: Optional[str] = Field(None, max_length=500, description="Company logo URL")
    contact_email: Optional[str] = Field(None, max_length=255, description="Contact email")
    contact_phone: Optional[str] = Field(None, max_length=50, description="Contact phone")
    industry: Optional[str] = Field(None, max_length=100, description="Industry sector")
    description: Optional[str] = Field(None, description="Company description")
    verification_document_url: Optional[str] = Field(None, max_length=500, description="Verification document URL")

    @validator('website_url', 'logo_url', 'verification_document_url')
    def validate_urls(cls, v):
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class SponsorProfileUpdate(BaseModel):
    """Schema for updating sponsor profiles"""
    company_name: Optional[str] = Field(None, min_length=2, max_length=255)
    website_url: Optional[str] = Field(None, max_length=500)
    logo_url: Optional[str] = Field(None, max_length=500)
    contact_email: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=50)
    industry: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None)

    @validator('website_url', 'logo_url')
    def validate_urls(cls, v):
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class SponsorProfileResponse(BaseModel):
    """Schema for sponsor profile responses"""
    id: int
    user_id: int
    company_name: str
    website_url: Optional[str]
    logo_url: Optional[str]
    contact_email: Optional[str]
    contact_phone: Optional[str]
    industry: Optional[str]
    description: Optional[str]
    is_verified: bool
    verification_document_url: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# =====================================================
# ROLE UPGRADE SCHEMAS
# =====================================================

class RoleUpgradeRequest(BaseModel):
    """Schema for requesting role upgrades (user -> sponsor)"""
    target_role: Literal["sponsor"] = Field(..., description="Target role (currently only sponsor supported)")
    company_name: str = Field(..., min_length=2, max_length=255, description="Company name")
    website_url: Optional[str] = Field(None, max_length=500, description="Company website")
    industry: Optional[str] = Field(None, max_length=100, description="Industry sector")
    description: Optional[str] = Field(None, description="Company description")
    verification_document_url: Optional[str] = Field(None, max_length=500, description="Verification document")

    @validator('website_url', 'verification_document_url')
    def validate_urls(cls, v):
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class RoleUpgradeResponse(BaseModel):
    """Schema for role upgrade responses"""
    message: str
    status: str
    user_id: int
    new_role: UserRole
    sponsor_profile_id: Optional[int] = None


# =====================================================
# CONTEST APPROVAL SCHEMAS
# =====================================================

class ContestApprovalRequest(BaseModel):
    """Schema for contest approval/rejection"""
    action: ApprovalAction = Field(..., description="Approval action")
    reason: Optional[str] = Field(None, description="Reason for approval/rejection")


class ContestApprovalResponse(BaseModel):
    """Schema for contest approval responses"""
    contest_id: int
    action: ApprovalAction
    approved_by_user_id: int
    reason: Optional[str]
    approved_at: datetime


# =====================================================
# AUDIT TRAIL SCHEMAS
# =====================================================

class RoleAuditResponse(BaseModel):
    """Schema for role audit trail responses"""
    id: int
    user_id: int
    old_role: Optional[str]
    new_role: str
    changed_by_user_id: Optional[int]
    reason: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ContestApprovalAuditResponse(BaseModel):
    """Schema for contest approval audit responses"""
    id: int
    contest_id: int
    action: str
    approved_by_user_id: Optional[int]
    reason: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# =====================================================
# ENHANCED AUTH SCHEMAS
# =====================================================

class UserRegistrationRequest(BaseModel):
    """Enhanced user registration with role support"""
    phone: str = Field(..., description="Phone number in E.164 format")
    role: Optional[UserRole] = Field(UserRole.USER, description="Requested role (admin requires approval)")
    company_name: Optional[str] = Field(None, description="Company name (required for sponsor role)")
    verification_code: str = Field(..., description="OTP verification code")

    @validator('company_name')
    def validate_company_name_for_sponsor(cls, v, values):
        if values.get('role') == UserRole.SPONSOR and not v:
            raise ValueError('Company name is required for sponsor role')
        return v


class EnhancedAuthResponse(BaseModel):
    """Enhanced authentication response with role information"""
    access_token: str
    token_type: str
    user_id: int
    phone: str
    role: UserRole
    is_verified: bool
    sponsor_profile_id: Optional[int] = None


# =====================================================
# ANALYTICS SCHEMAS
# =====================================================

class UserAnalytics(BaseModel):
    """User analytics for admin dashboard"""
    total_users: int
    admin_count: int
    sponsor_count: int
    user_count: int
    verified_users: int
    recent_registrations: int


class SponsorAnalytics(BaseModel):
    """Sponsor analytics for admin dashboard"""
    total_sponsors: int
    verified_sponsors: int
    pending_verification: int
    active_contests: int
    total_contests: int


class ContestAnalytics(BaseModel):
    """Contest analytics for admin dashboard"""
    total_contests: int
    approved_contests: int
    pending_approval: int
    active_contests: int
    completed_contests: int
