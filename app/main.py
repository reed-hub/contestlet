from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import get_settings
from app.database.database import db_manager
from app.core.vercel_config import get_environment_config
import importlib
import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("🚀 Starting Contestlet API...")
    
    # Create database tables
    db_manager.create_tables()
    print("🗄️ Database tables created")
    
    # Log environment info
    env_info = get_environment_config()
    print(f"🌍 Environment: {env_info.get('environment', 'development')}")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Contestlet API...")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    settings = get_settings()
    
    app = FastAPI(
        title="Contestlet API",
        description="Backend API for Contestlet - micro sweepstakes contests platform",
        version="1.0.0",
        debug=settings.debug,
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allow_origins,
        allow_credentials=settings.allow_credentials,
        allow_methods=settings.allow_methods,
        allow_headers=settings.allow_headers,
        max_age=600,  # Cache preflight for 10 minutes
    )
    
    # Log CORS configuration for debugging
    print(f"🌐 CORS Origins: {settings.allow_origins}")
    print(f"🔒 CORS Credentials: {settings.allow_credentials}")
    print(f"📋 CORS Methods: {settings.allow_methods}")
    print(f"📄 CORS Headers: {settings.allow_headers}")
    
    return app


def auto_discover_routers() -> list:
    """Automatically discover and import router modules"""
    router_modules = []
    routers_dir = os.path.join(os.path.dirname(__file__), "routers")
    
    # Files to exclude from auto-discovery
    excluded_files = {
        "sponsor_workflow_clean.py",  # Missing dependencies
        "contests_original_backup.py",  # Backup file
        "entries_original_backup.py",  # Backup file
        "location_original_backup.py",  # Backup file
        "media_original_backup.py",  # Backup file
        "users_original_backup.py",  # Backup file
        "auth_original_backup.py",  # Backup file
        "admin_original_backup.py",  # Backup file
    }
    
    for filename in os.listdir(routers_dir):
        if filename.endswith(".py") and not filename.startswith("__") and filename not in excluded_files:
            module_name = filename[:-3]
            try:
                module = importlib.import_module(f"app.routers.{module_name}")
                if hasattr(module, "router"):
                    router_modules.append(module.router)
                    print(f"🔌 Loaded router: {module_name}")
            except ImportError as e:
                print(f"⚠️ Failed to load router {module_name}: {e}")
    
    return router_modules


def setup_exception_handlers(app: FastAPI):
    """Setup custom exception handlers"""
    
    @app.exception_handler(500)
    async def internal_server_error_handler(request, exc):
        """Handle internal server errors with CORS headers"""
        origin = request.headers.get("origin", "*")
        settings = get_settings()
        
        # Use specific origin if it's in allowed origins, otherwise use *
        allowed_origin = origin if origin in settings.allow_origins else "*"
        
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "error": str(exc)},
            headers={
                "Access-Control-Allow-Origin": allowed_origin,
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": ", ".join(settings.allow_methods),
                "Access-Control-Allow-Headers": ", ".join(settings.allow_headers),
            }
        )
    
    @app.exception_handler(422)
    async def validation_error_handler(request, exc):
        """Handle validation errors with CORS headers"""
        origin = request.headers.get("origin", "*")
        settings = get_settings()
        allowed_origin = origin if origin in settings.allow_origins else "*"
        
        return JSONResponse(
            status_code=422,
            content={"detail": "Validation error", "errors": str(exc)},
            headers={
                "Access-Control-Allow-Origin": allowed_origin,
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": ", ".join(settings.allow_methods),
                "Access-Control-Allow-Headers": ", ".join(settings.allow_headers),
            }
        )


def setup_routes(app: FastAPI):
    """Setup application routes"""
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with environment info"""
        settings = get_settings()
        return {
            "message": "Welcome to Contestlet API",
            "status": "healthy",
            "environment": settings.environment,
            "version": "1.0.0"
        }
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "environment": get_settings().environment,
            "vercel_env": os.getenv("VERCEL_ENV", "local"),
            "git_branch": os.getenv("VERCEL_GIT_COMMIT_REF", "develop")
        }
    
    # PWA manifest
    @app.get("/manifest.json")
    async def get_manifest():
        """PWA manifest file for frontend compatibility"""
        return {
            "name": "Contestlet",
            "short_name": "Contestlet",
            "description": "Micro sweepstakes contests platform",
            "start_url": "/",
            "display": "standalone",
            "background_color": "#ffffff",
            "theme_color": "#000000",
            "icons": [
                {
                    "src": "/favicon.ico",
                    "sizes": "64x64 32x32 24x24 16x16",
                    "type": "image/x-icon"
                }
            ]
        }


# Create application instance
app = create_app()

# Setup exception handlers
setup_exception_handlers(app)

# Setup routes
setup_routes(app)

# Auto-discover and include routers
routers = auto_discover_routers()
for router in routers:
    app.include_router(router)

# Development server entry point
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True
    )
