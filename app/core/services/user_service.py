"""
Clean user service with centralized user operations.
"""

from typing import List, Optional
from sqlalchemy.orm import Session, joinedload

from app.models.user import User
from app.shared.exceptions.base import ResourceNotFoundException, ValidationException, BusinessException, ErrorCode
from app.shared.constants.auth import AuthConstants
from app.shared.types.pagination import PaginationParams, UserFilterParams, PaginatedResult, create_paginated_result
from app.schemas.role_system import UnifiedProfileUpdate
from app.core.datetime_utils import utc_now


class UserService:
    """
    Clean user service with centralized user operations.
    """
    
    def __init__(self, user_repo, db: Session):
        self.user_repo = user_repo
        self.db = db
    
    async def get_user_by_id(self, user_id: int, include_related: bool = False) -> Optional[User]:
        """
        Get user by ID with optional related data.
        
        Args:
            user_id: User ID
            include_related: Whether to load related entities
            
        Returns:
            User if found, None otherwise
        """
        return await self.user_repo.get_by_id(user_id, include_related)
    
    async def get_user_profile(self, user_id: int) -> User:
        """
        Get user profile with validation and related data.
        
        Args:
            user_id: User ID
            
        Returns:
            User profile with sponsor profile if applicable
            
        Raises:
            ResourceNotFoundException: If user not found
        """
        # Load user with sponsor_profile relationship
        user = self.db.query(User).options(
            joinedload(User.sponsor_profile)
        ).filter(User.id == user_id).first()
        
        if not user:
            raise ResourceNotFoundException("User", user_id)
        
        return user
    
    async def update_user_role(self, user_id: int, new_role: str, admin_user_id: int) -> User:
        """
        Update user role with validation.
        
        Args:
            user_id: User ID to update
            new_role: New role to assign
            admin_user_id: Admin performing the update
            
        Returns:
            Updated user
            
        Raises:
            ResourceNotFoundException: If user not found
            ValidationException: If role is invalid
        """
        # Validate role
        if new_role not in AuthConstants.VALID_ROLES:
            raise ValidationException(
                message="Invalid role specified",
                field_errors={"role": f"Must be one of: {AuthConstants.VALID_ROLES}"}
            )
        
        # Get user
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundException("User", user_id)
        
        # Update role
        user.role = new_role
        user.role_assigned_by = admin_user_id
        user.role_assigned_at = utc_now()
        
        return await self.user_repo.save(user)
    
    async def get_all_users(
        self,
        role_filter: Optional[str] = None,
        verified_only: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> List[User]:
        """
        Get all users with filtering.
        
        Args:
            role_filter: Filter by role
            verified_only: Only return verified users
            limit: Maximum users to return
            offset: Users to skip
            
        Returns:
            List of users
        """
        return await self.user_repo.get_all_users(
            role_filter=role_filter,
            verified_only=verified_only,
            limit=limit,
            offset=offset
        )
    
    async def search_users(
        self,
        search_term: Optional[str] = None,
        role_filter: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[User]:
        """
        Search users with filters.
        
        Args:
            search_term: Search term
            role_filter: Filter by role
            limit: Maximum results
            offset: Results to skip
            
        Returns:
            List of matching users
        """
        return await self.user_repo.search_users(
            search_term=search_term,
            role_filter=role_filter,
            limit=limit,
            offset=offset
        )
    
    async def update_user_profile(
        self,
        user_id: int,
        profile_update: UnifiedProfileUpdate,
        user_role: str
    ) -> User:
        """
        Update user profile with role-based validation.
        
        Args:
            user_id: User ID to update
            profile_update: Profile update data
            user_role: Role of the user (for validation)
            
        Returns:
            Updated user
            
        Raises:
            ResourceNotFoundException: If user not found
            BusinessException: If update violates business rules
        """
        # Get user with related data
        user = await self.get_user_profile(user_id)
        
        update_data = profile_update.dict(exclude_unset=True)
        
        # Separate personal profile fields from company profile fields
        personal_fields = {'full_name', 'email', 'bio'}
        company_fields = {'company_name', 'website_url', 'logo_url', 'contact_name', 
                         'contact_email', 'contact_phone', 'industry', 'description'}
        
        # Update personal profile fields (available to all users)
        personal_updates = {k: v for k, v in update_data.items() if k in personal_fields}
        if personal_updates:
            for field, value in personal_updates.items():
                if hasattr(user, field):
                    setattr(user, field, value)
            user.updated_at = utc_now()
        
        # Handle company profile updates (only for sponsors)
        company_updates = {k: v for k, v in update_data.items() if k in company_fields}
        if company_updates and user_role == AuthConstants.SPONSOR_ROLE:
            if not user.sponsor_profile:
                raise BusinessException(
                    error_code=ErrorCode.RESOURCE_NOT_FOUND,
                    message="Sponsor profile not found. Contact admin to set up sponsor profile.",
                    details={"user_id": user_id, "role": user_role}
                )
            
            # Update sponsor profile fields
            for field, value in company_updates.items():
                if hasattr(user.sponsor_profile, field):
                    setattr(user.sponsor_profile, field, value)
            
            user.sponsor_profile.updated_at = utc_now()
        
        elif company_updates and user_role != AuthConstants.SPONSOR_ROLE:
            # Ignore company fields for non-sponsor users (no error, just skip)
            pass
        
        # Save changes
        return await self.user_repo.save(user)
    
    async def get_all_users_paginated(
        self,
        pagination: PaginationParams,
        filters: UserFilterParams
    ):
        """
        Get all users with pagination and filtering.
        
        Args:
            pagination: Pagination parameters
            filters: Filter parameters
            
        Returns:
            Paginated result of users
        """
        # Get total count
        total = await self.user_repo.count_users(filters.role)
        
        # Get paginated users
        users = await self.user_repo.get_all_users(
            role_filter=filters.role,
            verified_only=filters.verified_only,
            limit=pagination.limit,
            offset=pagination.offset
        )
        
        return create_paginated_result(users, total, pagination)
    
    async def get_all_sponsors(self) -> List[User]:
        """
        Get all verified sponsor users for admin use.
        
        Returns:
            List of sponsor users with profiles
        """
        return self.db.query(User).options(
            joinedload(User.sponsor_profile)
        ).filter(
            User.role == AuthConstants.SPONSOR_ROLE,
            User.is_verified == True
        ).all()
