"""
🚀 Vercel Environment Configuration

Handles environment-specific settings for Vercel deployments.
Maps Vercel's environment structure to our three-environment strategy.
"""

import os
from typing import Dict, Any


def get_vercel_environment() -> str:
    """
    Determine the current Vercel environment.
    
    Vercel provides these environment variables:
    - VERCEL_ENV: "production", "preview", or "development"
    - VERCEL_GIT_COMMIT_REF: The branch name
    """
    vercel_env = os.getenv("VERCEL_ENV", "development")
    git_branch = os.getenv("VERCEL_GIT_COMMIT_REF", "develop")
    
    # Map Vercel environments to our strategy
    if vercel_env == "production":
        return "production"
    elif vercel_env == "preview":
        # Use branch name to determine preview type
        if git_branch == "staging":
            return "staging"
        else:
            return "preview"  # Feature branch previews
    else:
        return "development"


def get_environment_config() -> Dict[str, Any]:
    """
    Get environment-specific configuration for Vercel deployment.
    """
    env = get_vercel_environment()
    
    # Base configuration
    config = {
        "environment": env,
        "debug": False,
        "log_level": "INFO",
    }
    
    if env == "development":
        config.update({
            "debug": True,
            "log_level": "DEBUG",
            "use_mock_sms": True,
            "database_url": "sqlite:///./contestlet_dev.db",
            "cors_origins": [
                "http://localhost:3000",
                "http://localhost:8000",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:8000"
            ]
        })
    
    elif env == "staging":
        config.update({
            "debug": False,
            "log_level": "INFO",
            "use_mock_sms": True,   # Use mock mode for staging safety
            "staging_sms_whitelist": True,  # Only allow whitelisted numbers
            "staging_allowed_phones": [
                "+15551234567",  # Test numbers only
                "+18187958204"   # Your admin number
            ],
            "cors_origins": [
                "https://staging-app.contestlet.com",  # Staging custom domain
                "https://contestlet-frontend-staging.vercel.app",
                "https://contestlet-frontend-fd6p132ip-matthew-reeds-projects-89c602d6.vercel.app",  # Current staging URL
                "https://staging.contestlet.com",
                "http://localhost:3000",  # Local development
                "http://localhost:3002"   # Local development alt port
            ]
        })
    
    elif env == "production":
        config.update({
            "debug": False,
            "log_level": "WARNING",
            "use_mock_sms": False,
            "cors_origins": [
                "https://app.contestlet.com",  # Production custom domain
                "https://contestlet.com",      # Root domain redirect
                "https://contestlet-frontend.vercel.app",  # Vercel production
                "https://contestlet-frontend-production.vercel.app"  # Vercel production variant
            ]
        })
    
    elif env == "preview":
        config.update({
            "debug": False,
            "log_level": "INFO",
            "use_mock_sms": True,  # Mock for feature previews
            "cors_origins": ["*"]  # Allow all for feature previews
        })
    
    return config


def log_environment_info():
    """Log current environment information for debugging."""
    env_info = {
        "VERCEL_ENV": os.getenv("VERCEL_ENV"),
        "VERCEL_GIT_COMMIT_REF": os.getenv("VERCEL_GIT_COMMIT_REF"),
        "VERCEL_GIT_COMMIT_SHA": os.getenv("VERCEL_GIT_COMMIT_SHA"),
        "VERCEL_URL": os.getenv("VERCEL_URL"),
        "Determined Environment": get_vercel_environment()
    }
    
    print("🌍 Vercel Environment Info:")
    for key, value in env_info.items():
        print(f"   {key}: {value}")
    
    return env_info
