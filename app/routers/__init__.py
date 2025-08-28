from .auth import router as auth_router
from .contests import router as contests_router
from .entries import router as entries_router
from .admin import router as admin_router
from .admin_contests import router as admin_contests_router
from .admin_notifications import router as admin_notifications_router
from .admin_profile import router as admin_profile_router
from .admin_import import router as admin_import_router
from .location import router as location_router
from .sponsor import router as sponsor_router
from .user import router as user_router
from .users import router as users_router
from .media import router as media_router

__all__ = [
    "auth_router", 
    "contests_router", 
    "entries_router", 
    "admin_router",
    "admin_contests_router",
    "admin_notifications_router", 
    "admin_profile_router",
    "admin_import_router",
    "location_router",
    "sponsor_router",
    "user_router",
    "users_router",
    "media_router"
]
