import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.routers import auth_router, contests_router, entries_router, admin_router
from app.routers.admin_profile import router as admin_profile_router
from app.core.vercel_config import get_vercel_environment, get_environment_config, log_environment_info

# Log environment info for debugging
env_info = log_environment_info()
env_config = get_environment_config()

# Log database configuration
from app.database.database import get_database_url
database_url = get_database_url()
print(f"🗄️ Database URL: {database_url}")

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app with environment-aware configuration
app = FastAPI(
    title="Contestlet API",
    description=f"Backend API for Contestlet - micro sweepstakes contests platform ({env_config['environment']})",
    version="1.0.0",
    debug=env_config.get("debug", False)
)

# Add environment-aware CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=env_config.get("cors_origins", ["*"]),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add exception handler to ensure CORS headers are included even for 500 errors
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc: Exception):
    """Ensure CORS headers are included even for 500 errors"""
    response = JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
    
    # Get origin from request
    origin = request.headers.get("origin")
    if origin and origin in env_config.get("cors_origins", []):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    
    return response

# Include routers
app.include_router(auth_router)
app.include_router(contests_router)
app.include_router(entries_router)
app.include_router(admin_router)
app.include_router(admin_profile_router)


@app.get("/")
async def root():
    """Root endpoint with environment info"""
    return {
        "message": "Welcome to Contestlet API", 
        "status": "healthy",
        "environment": env_config['environment'],
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": env_config['environment'],
        "vercel_env": os.getenv("VERCEL_ENV", "local"),
        "git_branch": os.getenv("VERCEL_GIT_COMMIT_REF", "develop")
    }


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
