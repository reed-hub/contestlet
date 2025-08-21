#!/usr/bin/env python3
"""
🔧 Vercel Environment Setup Helper

This script helps configure your Vercel project with the correct 
environment variables for three-environment deployment.
"""

import json
import os
from typing import Dict, Any

def generate_env_vars() -> Dict[str, Dict[str, Any]]:
    """Generate environment variables for each Vercel environment."""
    
    # Base environment variables template
    base_vars = {
        "JWT_ALGORITHM": "HS256",
        "JWT_EXPIRE_MINUTES": "1440",
        "RATE_LIMIT_REQUESTS": "5",
        "RATE_LIMIT_WINDOW": "300",
    }
    
    environments = {
        "production": {
            **base_vars,
            "ENVIRONMENT": "production",
            "DEBUG": "false", 
            "LOG_LEVEL": "WARNING",
            "USE_MOCK_SMS": "false",
            "DATABASE_URL": "${PRODUCTION_DATABASE_URL}",
            "SECRET_KEY": "${PRODUCTION_SECRET_KEY}",
            "TWILIO_ACCOUNT_SID": "${PRODUCTION_TWILIO_ACCOUNT_SID}",
            "TWILIO_AUTH_TOKEN": "${PRODUCTION_TWILIO_AUTH_TOKEN}",
            "TWILIO_PHONE_NUMBER": "${PRODUCTION_TWILIO_PHONE_NUMBER}",
            "TWILIO_VERIFY_SERVICE_SID": "${PRODUCTION_TWILIO_VERIFY_SERVICE_SID}",
            "ADMIN_TOKEN": "${PRODUCTION_ADMIN_TOKEN}",
            "ADMIN_PHONES": "${PRODUCTION_ADMIN_PHONES}",
            "CORS_ORIGINS": "https://app.contestlet.com,https://contestlet.com",
            "REDIS_URL": "${PRODUCTION_REDIS_URL}",
            "SENTRY_DSN": "${PRODUCTION_SENTRY_DSN}",
        },
        
        "preview": {
            **base_vars,
            "ENVIRONMENT": "staging",
            "DEBUG": "false",
            "LOG_LEVEL": "INFO", 
            "USE_MOCK_SMS": "false",
            "DATABASE_URL": "${STAGING_DATABASE_URL}",
            "SECRET_KEY": "${STAGING_SECRET_KEY}",
            "TWILIO_ACCOUNT_SID": "${STAGING_TWILIO_ACCOUNT_SID}",
            "TWILIO_AUTH_TOKEN": "${STAGING_TWILIO_AUTH_TOKEN}",
            "TWILIO_PHONE_NUMBER": "${STAGING_TWILIO_PHONE_NUMBER}",
            "TWILIO_VERIFY_SERVICE_SID": "${STAGING_TWILIO_VERIFY_SERVICE_SID}",
            "ADMIN_TOKEN": "${STAGING_ADMIN_TOKEN}",
            "ADMIN_PHONES": "${STAGING_ADMIN_PHONES}",
            "CORS_ORIGINS": "https://staging.contestlet.com,https://contestlet-frontend-git-staging.vercel.app",
            "REDIS_URL": "${STAGING_REDIS_URL}",
            "SENTRY_DSN": "${STAGING_SENTRY_DSN}",
        }
    }
    
    return environments

def generate_vercel_cli_commands() -> str:
    """Generate Vercel CLI commands to set environment variables."""
    
    envs = generate_env_vars()
    commands = []
    
    commands.append("#!/bin/bash")
    commands.append("# 🚀 Vercel Environment Variables Setup")
    commands.append("# Run this script to configure your Vercel project environments")
    commands.append("")
    commands.append("echo '🔧 Setting up Vercel environment variables...'")
    commands.append("")
    
    # Production environment
    commands.append("echo '🏆 Setting Production environment variables...'")
    for key, value in envs["production"].items():
        commands.append(f'vercel env add {key} production --value="{value}"')
    commands.append("")
    
    # Preview/Staging environment  
    commands.append("echo '🧪 Setting Preview (Staging) environment variables...'")
    for key, value in envs["preview"].items():
        commands.append(f'vercel env add {key} preview --value="{value}"')
    commands.append("")
    
    commands.append("echo '✅ Environment variables configured!'")
    commands.append("echo '📋 Next steps:'")
    commands.append("echo '  1. Replace ${...} placeholders with actual values'")
    commands.append("echo '  2. Run: vercel --prod to deploy production'")
    commands.append("echo '  3. Run: vercel to deploy preview'")
    
    return "\n".join(commands)

def generate_env_file_templates():
    """Generate .env file templates for each environment."""
    
    envs = generate_env_vars()
    
    # Production .env template
    prod_env = []
    prod_env.append("# 🏆 PRODUCTION ENVIRONMENT")
    prod_env.append("# Set these in Vercel Dashboard > Environment Variables > Production")
    prod_env.append("")
    for key, value in envs["production"].items():
        prod_env.append(f"{key}={value}")
    
    # Preview .env template
    preview_env = []
    preview_env.append("# 🧪 PREVIEW/STAGING ENVIRONMENT")
    preview_env.append("# Set these in Vercel Dashboard > Environment Variables > Preview")
    preview_env.append("")
    for key, value in envs["preview"].items():
        preview_env.append(f"{key}={value}")
    
    return {
        "production": "\n".join(prod_env),
        "preview": "\n".join(preview_env)
    }

def main():
    """Generate configuration files for Vercel setup."""
    
    print("🚀 Generating Vercel environment configuration...")
    
    # Generate CLI commands
    cli_commands = generate_vercel_cli_commands()
    with open("vercel_env_setup.sh", "w") as f:
        f.write(cli_commands)
    os.chmod("vercel_env_setup.sh", 0o755)
    print("✅ Created: vercel_env_setup.sh")
    
    # Generate environment templates
    env_templates = generate_env_file_templates()
    
    with open("vercel_production.env.template", "w") as f:
        f.write(env_templates["production"])
    print("✅ Created: vercel_production.env.template")
    
    with open("vercel_preview.env.template", "w") as f:
        f.write(env_templates["preview"])
    print("✅ Created: vercel_preview.env.template")
    
    # Generate Vercel project configuration
    vercel_config = {
        "version": 2,
        "builds": [
            {
                "src": "app/main.py",
                "use": "@vercel/python"
            }
        ],
        "routes": [
            {
                "src": "/(.*)",
                "dest": "app/main.py"
            }
        ]
    }
    
    with open("vercel.json", "w") as f:
        json.dump(vercel_config, f, indent=2)
    print("✅ Updated: vercel.json")
    
    print("")
    print("🎯 Next Steps:")
    print("1. 📝 Edit the generated templates with your actual values")
    print("2. 🔧 Run: ./vercel_env_setup.sh (after installing Vercel CLI)")
    print("3. 🚀 Deploy: vercel --prod for production")
    print("4. 🧪 Deploy: vercel for preview/staging")
    print("")
    print("📚 See VERCEL_DEPLOYMENT_GUIDE.md for detailed instructions")

if __name__ == "__main__":
    main()
