"""
Service dependency injection.
Provides clean dependency injection for all service layers.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.services.contest_service import ContestService
from app.core.services.auth_service import AuthService
from app.core.services.user_service import UserService
from app.core.services.admin_service import AdminService
from app.core.services.entry_service import EntryService
from app.core.services.location_service import LocationService
from app.core.services.notification_service import NotificationService
from app.services.media_service import MediaService
from app.infrastructure.repositories.contest_repository import SQLAlchemyContestRepository
from app.infrastructure.repositories.user_repository import SQLAlchemyUserRepository
from app.infrastructure.repositories.entry_repository import SQLAlchemyEntryRepository


def get_contest_service(db: Session = Depends(get_db)) -> ContestService:
    """
    Dependency injection for contest service.
    Assembles all required dependencies for contest operations.
    """
    contest_repo = SQLAlchemyContestRepository(db)
    entry_repo = SQLAlchemyEntryRepository(db)
    user_repo = SQLAlchemyUserRepository(db)
    
    return ContestService(
        contest_repo=contest_repo,
        entry_repo=entry_repo,
        user_repo=user_repo,
        db=db
    )


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """
    Dependency injection for authentication service.
    """
    user_repo = SQLAlchemyUserRepository(db)
    
    return AuthService(
        user_repo=user_repo,
        db=db
    )


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """
    Dependency injection for user service.
    """
    user_repo = SQLAlchemyUserRepository(db)
    
    return UserService(
        user_repo=user_repo,
        db=db
    )


def get_admin_service(db: Session = Depends(get_db)) -> AdminService:
    """
    Dependency injection for admin service.
    """
    contest_repo = SQLAlchemyContestRepository(db)
    user_repo = SQLAlchemyUserRepository(db)
    entry_repo = SQLAlchemyEntryRepository(db)
    
    return AdminService(
        contest_repo=contest_repo,
        user_repo=user_repo,
        entry_repo=entry_repo,
        db=db
    )


def get_entry_service(db: Session = Depends(get_db)) -> EntryService:
    """
    Dependency injection for entry service.
    """
    entry_repo = SQLAlchemyEntryRepository(db)
    contest_repo = SQLAlchemyContestRepository(db)
    user_repo = SQLAlchemyUserRepository(db)
    
    return EntryService(
        entry_repo=entry_repo,
        contest_repo=contest_repo,
        user_repo=user_repo,
        db=db
    )


def get_location_service(db: Session = Depends(get_db)) -> LocationService:
    """
    Dependency injection for location service.
    """
    return LocationService(db=db)


def get_notification_service(db: Session = Depends(get_db)) -> NotificationService:
    """
    Dependency injection for notification service.
    """
    user_repo = SQLAlchemyUserRepository(db)
    contest_repo = SQLAlchemyContestRepository(db)
    entry_repo = SQLAlchemyEntryRepository(db)
    
    return NotificationService(
        notification_repo=None,  # TODO: Create notification repository
        user_repo=user_repo,
        contest_repo=contest_repo,
        entry_repo=entry_repo,
        db=db
    )


def get_media_service() -> MediaService:
    """
    Dependency injection for media service.
    """
    return MediaService()
