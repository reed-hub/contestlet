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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
