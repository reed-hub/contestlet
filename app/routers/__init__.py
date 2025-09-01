from .auth import router as auth_router
from .contests import router as contests_router
from .entries import router as entries_router
from .admin import router as admin_router
from .admin_contests import router as admin_contests_router
from .admin_approval import router as admin_approval_router
from .location import router as location_router
from .sponsor_workflow import router as sponsor_workflow_router
from .universal_contests import router as universal_contests_router
from .users import router as users_router
from .media import router as media_router

__all__ = [
    "auth_router", 
    "contests_router", 
    "entries_router", 
    "admin_router",
    "admin_contests_router",
    "admin_approval_router",
    "location_router",
    "sponsor_workflow_router",
    "universal_contests_router",
    "users_router",
    "media_router"
]
