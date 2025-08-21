# 🚀 Vercel Deployment Guide for Contestlet

## 🌍 **Environment Mapping Strategy**

### **Three-Environment Architecture on Vercel**

```
🔧 Local Development    →    🧪 Vercel Preview (Staging)    →    🏆 Vercel Production
      (develop)                    (staging branch)                   (main branch)
```

## 📊 **Vercel Environment Configuration**

### **🏆 Production Environment**
- **Vercel Environment**: `production`
- **Git Branch**: `main`
- **Domain**: `contestlet-frontend.vercel.app` (auto-assigned)
- **Custom Domain**: `app.contestlet.com` (when configured)
- **Deployment Trigger**: Push to `main` branch

### **🧪 Preview Environment (Staging)**
- **Vercel Environment**: `preview`
- **Git Branch**: `staging`
- **Domain**: `contestlet-frontend-git-staging-{team}.vercel.app`
- **Custom Domain**: `staging.contestlet.com` (when configured)
- **Deployment Trigger**: Push to `staging` branch

### **🔧 Development Environment**
- **Vercel Environment**: `development` (local only)
- **Git Branch**: `develop` + feature branches
- **Domain**: Feature branch previews get unique URLs
- **Local Development**: `http://localhost:8000`

## ⚙️ **Vercel Project Configuration**

### **1. Environment Variables Setup**

#### **🏆 Production Environment Variables**
```bash
# Database
DATABASE_URL=postgresql://prod_user:password@prod-host/contestlet_prod

# JWT & Security
SECRET_KEY=production-secret-key-very-secure
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# Twilio (Production)
TWILIO_ACCOUNT_SID=AC1234567890abcdef...
TWILIO_AUTH_TOKEN=your-production-auth-token
TWILIO_PHONE_NUMBER=+15551234567
TWILIO_VERIFY_SERVICE_SID=VA1234567890abcdef...
USE_MOCK_SMS=false

# Admin Settings
ADMIN_TOKEN=production-admin-token-very-secure
ADMIN_PHONES=+15551234567,+17205550000

# Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING

# CORS
CORS_ORIGINS=https://app.contestlet.com,https://contestlet.com

# Redis/Cache
REDIS_URL=redis://production-redis-host:6379

# Monitoring
SENTRY_DSN=https://your-sentry-dsn-production
```

#### **🧪 Preview Environment Variables**
```bash
# Database
DATABASE_URL=postgresql://staging_user:password@staging-host/contestlet_staging

# JWT & Security  
SECRET_KEY=staging-secret-key-different-from-prod
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# Twilio (Staging - Limited)
TWILIO_ACCOUNT_SID=AC1234567890abcdef...
TWILIO_AUTH_TOKEN=your-staging-auth-token
TWILIO_PHONE_NUMBER=+15551234567
TWILIO_VERIFY_SERVICE_SID=VA1234567890abcdef...
USE_MOCK_SMS=false

# Admin Settings
ADMIN_TOKEN=staging-admin-token-different
ADMIN_PHONES=+15551234567

# Environment
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO

# CORS
CORS_ORIGINS=https://staging.contestlet.com

# Redis/Cache
REDIS_URL=redis://staging-redis-host:6379

# Monitoring
SENTRY_DSN=https://your-sentry-dsn-staging
```

### **2. Vercel Project Settings**

#### **Git Integration**
```json
{
  "productionBranch": "main",
  "framework": "other",
  "buildCommand": "pip install -r requirements.txt",
  "outputDirectory": "",
  "installCommand": "pip install -r requirements.txt",
  "devCommand": "uvicorn app.main:app --host 0.0.0.0 --port 8000"
}
```

#### **Build & Development Settings**
- **Framework Preset**: Other
- **Build Command**: `pip install -r requirements.txt`
- **Output Directory**: (leave empty)
- **Install Command**: `pip install -r requirements.txt`
- **Development Command**: `uvicorn app.main:app --host 0.0.0.0 --port 8000`

## 🔄 **Deployment Workflow**

### **Step 1: Fix Current Production Deployment**
```bash
# First, let's get the correct production setup
git checkout main

# Make sure main has production-ready code
git merge staging  # Only if staging is validated

# Push to fix production
git push origin main
```

### **Step 2: Configure Vercel Environments**

#### **In Vercel Dashboard:**

1. **Go to Project Settings > Environment Variables**

2. **Add Production Variables** (Environment: Production):
   - Set all production environment variables
   - These apply only to the `main` branch

3. **Add Preview Variables** (Environment: Preview):
   - Set all staging environment variables  
   - These apply to the `staging` branch and other preview deployments

4. **Set Branch-Specific Settings**:
   - **Production Branch**: `main`
   - **Preview Branches**: All branches (including `staging`)

### **Step 3: Deploy Staging Environment**
```bash
# Deploy to staging (preview)
git checkout staging
git merge develop  # Merge latest development
git push origin staging

# This creates a preview deployment at:
# https://contestlet-backend-git-staging-{team}.vercel.app
```

### **Step 4: Validate and Promote**
```bash
# After staging validation passes
git checkout main
git merge staging
git push origin main

# This deploys to production:
# https://contestlet-backend.vercel.app
```

## 🛡️ **Environment Security**

### **Environment Variable Precedence**
1. **Environment-specific variables** (Production/Preview)
2. **General project variables**
3. **Default values in code**

### **Sensitive Data Handling**
- ✅ Store all secrets in Vercel Environment Variables
- ✅ Use different secrets for each environment
- ✅ Never commit `.env` files with real credentials
- ✅ Use Vercel's encrypted environment variables

## 📊 **Environment Detection**

### **How the Backend Detects Environment**
```python
# The app uses these Vercel environment variables:
VERCEL_ENV = os.getenv("VERCEL_ENV")  # "production", "preview", "development"
VERCEL_GIT_COMMIT_REF = os.getenv("VERCEL_GIT_COMMIT_REF")  # branch name

# Our mapping:
if VERCEL_ENV == "production":
    environment = "production"
elif VERCEL_ENV == "preview" and VERCEL_GIT_COMMIT_REF == "staging":
    environment = "staging" 
elif VERCEL_ENV == "preview":
    environment = "preview"  # Feature branch previews
else:
    environment = "development"
```

### **Environment-Specific Behavior**
- **Production**: Full Twilio, strict CORS, minimal logging
- **Staging**: Real Twilio (limited), staging CORS, info logging
- **Preview**: Mock Twilio, permissive CORS, debug logging

## 🔍 **Verification Steps**

### **1. Check Environment Detection**
```bash
# Visit your deployed URLs and check the health endpoint:
curl https://your-deployment-url.vercel.app/health

# Should return:
{
  "status": "healthy",
  "environment": "production|staging|preview",
  "vercel_env": "production|preview|development", 
  "git_branch": "main|staging|feature-branch"
}
```

### **2. Verify CORS Configuration**
```bash
# Test CORS from your frontend domain
curl -H "Origin: https://your-frontend-domain.com" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: X-Requested-With" \
     -X OPTIONS \
     https://your-api-url.vercel.app/auth/request-otp
```

### **3. Test Environment-Specific Features**
- **Production**: Real SMS sending
- **Staging**: Limited SMS sending with test numbers
- **Preview**: Mock SMS (no real messages sent)

## 🚨 **Fixing Current Issue**

### **Immediate Steps**
1. **Identify which branch is on production** (likely `staging`)
2. **Set up proper environment variables** for each Vercel environment
3. **Configure branch mapping** in Vercel dashboard
4. **Redeploy with correct configuration**

### **Branch Cleanup**
```bash
# If staging accidentally got deployed to production:

# 1. Make sure main branch has production-ready code
git checkout main
git merge staging  # Only if staging is validated for production

# 2. Push main to trigger proper production deployment
git push origin main

# 3. Ensure staging branch is configured for preview
git checkout staging
git push origin staging  # This should create a preview deployment
```

This setup ensures your environments are properly isolated and mapped to the correct Vercel deployment types! 🌍🚀
