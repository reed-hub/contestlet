"""
Role System Schemas

Pydantic models for multi-tier role system including:
- User role management
- Sponsor profiles
- Role-based authentication
- Audit trail responses
"""

import re
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
    """Enhanced user schema with role information and personal profile"""
    id: int
    phone: str
    role: UserRole
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    role_assigned_at: datetime
    created_by_user_id: Optional[int] = None
    role_assigned_by: Optional[int] = None
    
    # Personal Profile Fields
    full_name: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None
    
    # Timezone Preferences
    timezone: Optional[str] = None
    timezone_auto_detect: bool = True
    
    class Config:
        from_attributes = True


class UserWithRoleAndCompany(BaseModel):
    """Enhanced user schema with role information and optional company profile for admin management"""
    id: int
    phone: str
    role: UserRole
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    role_assigned_at: datetime
    created_by_user_id: Optional[int] = None
    role_assigned_by: Optional[int] = None
    
    # Personal Profile Fields
    full_name: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None
    
    # Timezone Preferences
    timezone: Optional[str] = None
    timezone_auto_detect: bool = True
    
    # Company Profile Fields (for sponsors)
    sponsor_profile_id: Optional[int] = None  # Added for contest creation
    company_name: Optional[str] = None
    website_url: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    industry: Optional[str] = None
    company_description: Optional[str] = None
    
    class Config:
        from_attributes = True
    
    @classmethod
    def from_user(cls, user):
        """Create UserWithRoleAndCompany from User model"""
        data = {
            "id": user.id,
            "phone": user.phone,
            "role": user.role,
            "is_verified": user.is_verified,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "role_assigned_at": user.role_assigned_at,
            "created_by_user_id": user.created_by_user_id,
            "role_assigned_by": user.role_assigned_by,
            "full_name": user.full_name,
            "email": user.email,
            "bio": user.bio,
            "timezone": getattr(user, 'timezone', None),
            "timezone_auto_detect": getattr(user, 'timezone_auto_detect', True),
        }
        
        # Add company fields if user has sponsor profile
        if user.sponsor_profile:
            data.update({
                "sponsor_profile_id": user.sponsor_profile.id,  # Added for contest creation
                "company_name": user.sponsor_profile.company_name,
                "website_url": user.sponsor_profile.website_url,
                "contact_name": user.sponsor_profile.contact_name,
                "contact_email": user.sponsor_profile.contact_email,
                "contact_phone": user.sponsor_profile.contact_phone,
                "industry": user.sponsor_profile.industry,
                "company_description": user.sponsor_profile.description,
            })
        
        return cls(**data)


class AdminUserCreate(BaseModel):
    """Schema for admin creating new users"""
    phone: str = Field(..., description="Phone number in E.164 format")
    role: UserRole = Field(..., description="User role")
    full_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Full name")
    email: Optional[str] = Field(None, max_length=255, description="Email address")
    bio: Optional[str] = Field(None, max_length=1000, description="Personal bio")
    
    # Company fields (for sponsors)
    company_name: Optional[str] = Field(None, max_length=255, description="Company name")
    website_url: Optional[str] = Field(None, max_length=500, description="Company website")
    contact_name: Optional[str] = Field(None, max_length=255, description="Contact person name")
    contact_email: Optional[str] = Field(None, max_length=255, description="Contact email")
    contact_phone: Optional[str] = Field(None, max_length=50, description="Contact phone")
    industry: Optional[str] = Field(None, max_length=100, description="Industry sector")
    company_description: Optional[str] = Field(None, description="Company description")
    
    @validator('phone')
    def validate_phone(cls, v):
        if not v.startswith('+'):
            raise ValueError('Phone number must be in E.164 format (start with +)')
        if len(v) < 10 or len(v) > 15:
            raise ValueError('Phone number must be between 10 and 15 characters')
        return v
    
    @validator('email', 'contact_email')
    def validate_emails(cls, v):
        if v and not re.match(r"[^@]+@[^@]+\.[^@]+", v):
            raise ValueError('Invalid email format')
        return v
    
    @validator('website_url')
    def validate_urls(cls, v):
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('URL must start with http:// or https://')
        return v
    
    @validator('company_name')
    def validate_company_name(cls, v):
        if v is not None and v.strip() == "":
            return None
        if v and len(v.strip()) < 2:
            raise ValueError('Company name must be at least 2 characters')
        return v.strip() if v else v
    
    @validator('full_name', 'contact_name')
    def validate_names(cls, v):
        if v and len(v.strip()) < 1:
            raise ValueError('Name cannot be empty')
        return v.strip() if v else v


# =====================================================
# SPONSOR PROFILE SCHEMAS
# =====================================================

class SponsorProfileCreate(BaseModel):
    """Schema for creating sponsor profiles"""
    company_name: str = Field(..., min_length=2, max_length=255, description="Company name")
    website_url: Optional[str] = Field(None, max_length=500, description="Company website URL")
    logo_url: Optional[str] = Field(None, max_length=500, description="Company logo URL")
    contact_name: Optional[str] = Field(None, max_length=255, description="Contact person name")
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
    
    @validator('contact_email')
    def validate_contact_email(cls, v):
        if v and not re.match(r"[^@]+@[^@]+\.[^@]+", v):
            raise ValueError('Invalid email format')
        return v
    
    @validator('contact_name')
    def validate_contact_name(cls, v):
        if v and len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters')
        return v


class SponsorProfileUpdate(BaseModel):
    """Schema for updating sponsor profiles"""
    company_name: Optional[str] = Field(None, min_length=2, max_length=255)
    website_url: Optional[str] = Field(None, max_length=500)
    logo_url: Optional[str] = Field(None, max_length=500)
    contact_name: Optional[str] = Field(None, max_length=255)
    contact_email: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=50)
    industry: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None)

    @validator('website_url', 'logo_url')
    def validate_urls(cls, v):
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('URL must start with http:// or https://')
        return v
    
    @validator('contact_email')
    def validate_contact_email(cls, v):
        if v and not re.match(r"[^@]+@[^@]+\.[^@]+", v):
            raise ValueError('Invalid email format')
        return v
    
    @validator('contact_name')
    def validate_contact_name(cls, v):
        if v and len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters')
        return v


class UnifiedProfileUpdate(BaseModel):
    """Unified schema for updating user profiles (personal + company + timezone fields)"""
    # Personal Profile Fields (available to all users)
    full_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Full name")
    email: Optional[str] = Field(None, max_length=255, description="Email address")
    bio: Optional[str] = Field(None, max_length=1000, description="Personal bio/description")
    
    # Timezone Preferences (available to all users)
    timezone: Optional[str] = Field(None, max_length=50, description="IANA timezone identifier (e.g., 'America/New_York'). NULL uses system default (UTC)")
    timezone_auto_detect: Optional[bool] = Field(None, description="Whether to auto-detect timezone from browser")
    
    # Company Profile Fields (only for sponsors)
    company_name: Optional[str] = Field(None, max_length=255, description="Company name")
    website_url: Optional[str] = Field(None, max_length=500, description="Company website")
    logo_url: Optional[str] = Field(None, max_length=500, description="Company logo URL")
    contact_name: Optional[str] = Field(None, max_length=255, description="Contact person name")
    contact_email: Optional[str] = Field(None, max_length=255, description="Contact email")
    contact_phone: Optional[str] = Field(None, max_length=50, description="Contact phone")
    industry: Optional[str] = Field(None, max_length=100, description="Industry sector")
    description: Optional[str] = Field(None, description="Company description")

    @validator('email', 'contact_email')
    def validate_emails(cls, v):
        if v and not re.match(r"[^@]+@[^@]+\.[^@]+", v):
            raise ValueError('Invalid email format')
        return v
    
    @validator('website_url', 'logo_url')
    def validate_urls(cls, v):
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('URL must start with http:// or https://')
        return v
    
    @validator('timezone')
    def validate_timezone(cls, v):
        """Validate timezone using the same logic as UserTimezonePreferences"""
        if v is None:
            return v  # Allow None for system default
            
        # List of supported timezones (consistent with admin system)
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
    
    @validator('company_name')
    def validate_company_name(cls, v):
        if v is not None and v.strip() == "":
            # Convert empty strings to None for company fields
            return None
        if v and len(v.strip()) < 2:
            raise ValueError('Company name must be at least 2 characters')
        return v.strip() if v else v
    
    @validator('full_name', 'contact_name')
    def validate_names(cls, v):
        if v and len(v.strip()) < 1:
            raise ValueError('Name cannot be empty')
        return v.strip() if v else v


class SponsorProfileResponse(BaseModel):
    """Schema for sponsor profile responses"""
    id: int
    user_id: int
    company_name: str
    website_url: Optional[str]
    logo_url: Optional[str]
    contact_name: Optional[str]
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


class UnifiedSponsorProfileResponse(BaseModel):
    """Unified schema combining user and company profile information for frontend"""
    # User information
    user_id: int
    phone: str
    role: UserRole
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    role_assigned_at: datetime
    
    # Personal Profile Fields
    full_name: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None
    
    # Timezone Preferences
    timezone: Optional[str] = None
    timezone_auto_detect: bool = True
    
    # Company profile information
    company_profile: Optional[SponsorProfileResponse] = None
    
    class Config:
        from_attributes = True


# =====================================================
# ROLE UPGRADE SCHEMAS
# =====================================================

class RoleUpgradeRequest(BaseModel):
    """Schema for requesting role upgrades (user -> sponsor)"""
    target_role: Literal["sponsor"] = Field(..., description="Target role (currently only sponsor supported)")
    company_name: str = Field(..., min_length=2, max_length=255, description="Company name")
    contact_name: Optional[str] = Field(None, max_length=255, description="Contact person name")
    contact_email: Optional[str] = Field(None, max_length=255, description="Contact email")
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
