"""
Clean admin service with centralized admin operations.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.contest import Contest
from app.models.entry import Entry
from app.shared.exceptions.base import ResourceNotFoundException, AuthorizationException
from app.shared.constants.auth import AuthConstants


class AdminService:
    """
    Clean admin service with centralized admin operations.
    """
    
    def __init__(self, contest_repo, user_repo, entry_repo, db: Session):
        self.contest_repo = contest_repo
        self.user_repo = user_repo
        self.entry_repo = entry_repo
        self.db = db
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get admin dashboard statistics.
        
        Returns:
            Dashboard data with statistics
        """
        # Get counts
        total_contests = await self.contest_repo.count_contests()
        active_contests = await self.contest_repo.count_contests("active")
        total_users = await self.user_repo.count_users()
        admin_users = await self.user_repo.count_users("admin")
        sponsor_users = await self.user_repo.count_users("sponsor")
        
        # Get recent contests
        recent_contests = await self.contest_repo.get_all_contests(limit=5)
        
        return {
            "statistics": {
                "total_contests": total_contests,
                "active_contests": active_contests,
                "total_users": total_users,
                "admin_users": admin_users,
                "sponsor_users": sponsor_users
            },
            "recent_contests": [
                {
                    "id": contest.id,
                    "name": contest.name,
                    "status": contest.status,
                    "created_at": contest.created_at,
                    "entry_count": len(contest.entries) if contest.entries else 0
                }
                for contest in recent_contests
            ]
        }
    
    async def get_system_statistics(self) -> Dict[str, Any]:
        """
        Get detailed system statistics.
        
        Returns:
            Detailed system statistics
        """
        # Contest statistics by status
        contest_stats = {}
        for status in ["draft", "awaiting_approval", "active", "ended", "complete", "cancelled"]:
            contest_stats[status] = await self.contest_repo.count_contests(status)
        
        # User statistics by role
        user_stats = {}
        for role in AuthConstants.VALID_ROLES:
            user_stats[role] = await self.user_repo.count_users(role)
        
        return {
            "contest_statistics": contest_stats,
            "user_statistics": user_stats,
            "total_contests": sum(contest_stats.values()),
            "total_users": sum(user_stats.values())
        }
    
    async def get_all_contests(self, limit: int = 100, offset: int = 0) -> List[Contest]:
        """
        Get all contests for admin view.
        
        Args:
            limit: Maximum contests to return
            offset: Contests to skip
            
        Returns:
            List of contests with admin details
        """
        return await self.contest_repo.get_all_contests(limit, offset)
    
    async def get_all_users(
        self,
        role_filter: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[User]:
        """
        Get all users for admin management.
        
        Args:
            role_filter: Filter by role
            limit: Maximum users to return
            offset: Users to skip
            
        Returns:
            List of users
        """
        return await self.user_repo.get_all_users(
            role_filter=role_filter,
            verified_only=False,
            limit=limit,
            offset=offset
        )
    
    async def update_user_role(self, user_id: int, new_role: str, admin_user_id: int) -> User:
        """
        Update user role (admin operation).
        
        Args:
            user_id: User ID to update
            new_role: New role to assign
            admin_user_id: Admin performing the update
            
        Returns:
            Updated user
            
        Raises:
            ResourceNotFoundException: If user not found
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundException("User", user_id)
        
        # Update role
        old_role = user.role
        user.role = new_role
        user.role_assigned_by = admin_user_id
        from app.core.datetime_utils import utc_now
        user.role_assigned_at = utc_now()
        
        updated_user = await self.user_repo.save(user)
        
        # Log role change (could be expanded to audit table)
        print(f"Admin {admin_user_id} changed user {user_id} role from {old_role} to {new_role}")
        
        return updated_user
    
    async def update_user_profile_admin(self, user_id: int, profile_update, admin_user_id: int) -> User:
        """
        Update any user's profile information (admin operation).
        
        Args:
            user_id: User ID to update
            profile_update: Profile update data
            admin_user_id: Admin performing the update
            
        Returns:
            Updated user with profile data
            
        Raises:
            ResourceNotFoundException: If user not found
        """
        from sqlalchemy.orm import joinedload
        from app.core.datetime_utils import utc_now
        from app.models.sponsor_profile import SponsorProfile
        
        # Load user with sponsor_profile relationship
        user = self.db.query(User).options(
            joinedload(User.sponsor_profile)
        ).filter(User.id == user_id).first()
        
        if not user:
            raise ResourceNotFoundException("User", user_id)
        
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
        if company_updates and user.role == "sponsor":
            if not user.sponsor_profile:
                # Create sponsor profile if it doesn't exist
                sponsor_profile = SponsorProfile(
                    user_id=user.id,
                    created_at=utc_now(),
                    updated_at=utc_now()
                )
                self.db.add(sponsor_profile)
                self.db.flush()  # Get the ID
                user.sponsor_profile = sponsor_profile
            
            # Update sponsor profile fields
            for field, value in company_updates.items():
                if hasattr(user.sponsor_profile, field):
                    setattr(user.sponsor_profile, field, value)
            user.sponsor_profile.updated_at = utc_now()
        
        # Commit changes
        self.db.commit()
        self.db.refresh(user)
        
        # Log profile change
        print(f"Admin {admin_user_id} updated profile for user {user_id}")
        
        return user
    
    async def create_user_admin(self, user_data, admin_user_id: int) -> User:
        """
        Create a new user (admin operation).
        
        Args:
            user_data: User creation data
            admin_user_id: Admin performing the creation
            
        Returns:
            Created user with profile data
            
        Raises:
            ValidationException: If phone number already exists
        """
        from sqlalchemy.orm import joinedload
        from app.core.datetime_utils import utc_now
        from app.models.sponsor_profile import SponsorProfile
        
        # Check if phone number already exists
        existing_user = self.db.query(User).filter(User.phone == user_data.phone).first()
        if existing_user:
            from app.shared.exceptions.base import ValidationException
            raise ValidationException(
                message="Phone number already exists",
                field_errors={"phone": "A user with this phone number already exists"}
            )
        
        # Create user
        user = User(
            phone=user_data.phone,
            role=user_data.role,
            is_verified=True,  # Admin-created users are auto-verified
            created_at=utc_now(),
            updated_at=utc_now(),
            role_assigned_at=utc_now(),
            created_by_user_id=admin_user_id,
            role_assigned_by=admin_user_id,
            full_name=user_data.full_name,
            email=user_data.email,
            bio=user_data.bio
        )
        
        self.db.add(user)
        self.db.flush()  # Get the user ID
        
        # Create sponsor profile if user is a sponsor and has company data
        if user.role == "sponsor" and user_data.company_name:
            sponsor_profile = SponsorProfile(
                user_id=user.id,
                company_name=user_data.company_name,
                website_url=user_data.website_url,
                contact_name=user_data.contact_name,
                contact_email=user_data.contact_email,
                contact_phone=user_data.contact_phone,
                industry=user_data.industry,
                description=user_data.company_description,
                is_verified=True,  # Admin-created sponsors are auto-verified
                created_at=utc_now(),
                updated_at=utc_now()
            )
            self.db.add(sponsor_profile)
            self.db.flush()
            user.sponsor_profile = sponsor_profile
        
        # Commit changes
        self.db.commit()
        self.db.refresh(user)
        
        # Load with relationships for response
        user_with_profile = self.db.query(User).options(
            joinedload(User.sponsor_profile)
        ).filter(User.id == user.id).first()
        
        # Log user creation
        print(f"Admin {admin_user_id} created user {user.id} with role {user.role}")
        
        return user_with_profile
    
    async def delete_user_admin(self, user_id: int, admin_user_id: int) -> bool:
        """
        Delete a user (admin operation).
        
        Args:
            user_id: User ID to delete
            admin_user_id: Admin performing the deletion
            
        Returns:
            True if deleted successfully
            
        Raises:
            ResourceNotFoundException: If user not found
            BusinessException: If user cannot be deleted (has dependencies)
        """
        from sqlalchemy.orm import joinedload
        
        # Load user with relationships to check dependencies
        user = self.db.query(User).options(
            joinedload(User.entries),
            joinedload(User.sponsor_profile)
        ).filter(User.id == user_id).first()
        
        if not user:
            raise ResourceNotFoundException("User", user_id)
        
        # Check if user has contest entries (prevent deletion if they do)
        if user.entries and len(user.entries) > 0:
            from app.shared.exceptions.base import BusinessException, ErrorCode
            raise BusinessException(
                error_code=ErrorCode.OPERATION_NOT_ALLOWED,
                message=f"Cannot delete user with {len(user.entries)} contest entries",
                details={"user_id": user_id, "entry_count": len(user.entries)}
            )
        
        # Delete sponsor profile first if it exists
        if user.sponsor_profile:
            self.db.delete(user.sponsor_profile)
        
        # Delete the user
        self.db.delete(user)
        self.db.commit()
        
        # Log user deletion
        print(f"Admin {admin_user_id} deleted user {user_id} ({user.role})")
        
        return True
    
    async def get_contest_entries(self, contest_id: int) -> List[Entry]:
        """
        Get all entries for a contest (admin view) with user information.
        
        Args:
            contest_id: Contest ID
            
        Returns:
            List of contest entries with user relationships loaded
            
        Raises:
            ResourceNotFoundException: If contest not found
        """
        # Verify contest exists
        contest = await self.contest_repo.get_by_id(contest_id)
        if not contest:
            raise ResourceNotFoundException("Contest", contest_id)
        
        # Get entries with user relationship loaded
        from sqlalchemy.orm import joinedload
        entries = self.db.query(Entry).options(
            joinedload(Entry.user)
        ).filter(Entry.contest_id == contest_id).all()
        
        return entries
    
    async def delete_contest_admin(self, contest_id: int, admin_user_id: int) -> bool:
        """
        Delete contest with admin privileges (bypasses some restrictions).
        
        Args:
            contest_id: Contest ID to delete
            admin_user_id: Admin performing deletion
            
        Returns:
            True if deleted successfully
            
        Raises:
            ResourceNotFoundException: If contest not found
        """
        contest = await self.contest_repo.get_by_id(contest_id)
        if not contest:
            raise ResourceNotFoundException("Contest", contest_id)
        
        # Admin can delete most contests (with some restrictions for active ones)
        if contest.status == "active":
            # Even admins should be careful with active contests
            entry_count = await self.entry_repo.count_entries_for_contest(contest_id)
            if entry_count > 0:
                from app.shared.exceptions.base import BusinessException, ErrorCode
                raise BusinessException(
                    error_code=ErrorCode.CONTEST_PROTECTED,
                    message=f"Cannot delete active contest with {entry_count} entries",
                    details={"contest_id": contest_id, "entry_count": entry_count}
                )
        
        # Perform deletion
        return await self.contest_repo.delete(contest_id)
