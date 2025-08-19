from .auth import router as auth_router
from .contests import router as contests_router
from .entries import router as entries_router
from .admin import router as admin_router

__all__ = ["auth_router", "contests_router", "entries_router", "admin_router"]
