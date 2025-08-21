# 🚀 Contestlet Deployment Strategy

## 📊 Three-Environment Architecture

### **Environment Overview**
```
🔧 Development (Local)     →    🧪 Staging (Server)      →    🏆 Production (Server)
- Feature development            - Integration testing           - Live user traffic
- Local SQLite                  - Production-like setup         - Production database  
- Mock services                 - Real services (limited)       - Full services
- Hot reloading                 - Stable builds                 - Optimized builds
```

## 🌿 Git Branching Strategy

### **Branch Structure**
```
main (production)
├── staging 
└── develop
    ├── feature/contest-deletion
    ├── feature/timezone-support
    └── hotfix/security-patch
```

### **Branch Rules**

#### **🔧 `develop` Branch**
- **Purpose**: Latest development code, integration of new features
- **Deploys to**: Development environment (local)
- **Merge from**: Feature branches, hotfix branches
- **Protection**: Require PR reviews for merges

#### **🧪 `staging` Branch** 
- **Purpose**: Release candidate testing, QA validation
- **Deploys to**: Staging environment (server)
- **Merge from**: `develop` branch only
- **Protection**: Require CI/CD tests to pass

#### **🏆 `main` Branch**
- **Purpose**: Production-ready code, stable releases
- **Deploys to**: Production environment (server)
- **Merge from**: `staging` branch only
- **Protection**: Require staging validation + approval

## 🔄 Development Workflow

### **For Developers & AI Assistants**

#### **1. Feature Development**
```bash
# Start from develop branch
git checkout develop
git pull origin develop

# Create feature branch
git checkout -b feature/new-feature-name

# Develop and commit changes
git add .
git commit -m "Add new feature: description"

# Push feature branch
git push origin feature/new-feature-name

# Create Pull Request to develop
# → Requires code review
# → Triggers automated tests
```

#### **2. Staging Deployment**
```bash
# After feature is merged to develop
git checkout staging
git pull origin staging

# Merge develop into staging
git merge develop
git push origin staging

# → Triggers staging deployment
# → Runs integration tests
# → QA validation begins
```

#### **3. Production Deployment**
```bash
# After staging validation passes
git checkout main
git pull origin main

# Merge staging into main
git merge staging
git push origin main

# → Triggers production deployment
# → Runs smoke tests
# → Monitoring alerts activated
```

## 📦 Environment Configurations

### **Development Environment**
```yaml
# config/development.yml
database:
  type: sqlite
  url: "sqlite:///./contestlet_dev.db"
  
services:
  twilio:
    mock_mode: true
    use_test_numbers: true
  
security:
  debug_mode: true
  cors_origins: ["http://localhost:3000", "http://localhost:8000"]
  
logging:
  level: DEBUG
  console_output: true
```

### **Staging Environment** 
```yaml
# config/staging.yml
database:
  type: postgresql
  url: "${STAGING_DATABASE_URL}"
  
services:
  twilio:
    mock_mode: false
    use_test_numbers: true
    limited_sending: true
  
security:
  debug_mode: false
  cors_origins: ["https://staging-frontend.contestlet.com"]
  
logging:
  level: INFO
  file_output: true
```

### **Production Environment**
```yaml
# config/production.yml
database:
  type: postgresql
  url: "${PRODUCTION_DATABASE_URL}"
  
services:
  twilio:
    mock_mode: false
    use_test_numbers: false
    rate_limits: strict
  
security:
  debug_mode: false
  cors_origins: ["https://app.contestlet.com"]
  
logging:
  level: WARNING
  structured_output: true
  monitoring: true
```

## 🔐 Environment Variables

### **Development (.env.development)**
```env
# Database
DATABASE_URL=sqlite:///./contestlet_dev.db

# Twilio (Mock)
USE_MOCK_SMS=true
TWILIO_ACCOUNT_SID=test_account_sid
TWILIO_AUTH_TOKEN=test_auth_token

# Admin
ADMIN_PHONES=+15551234567,+18187958204

# Security
SECRET_KEY=development-secret-key-change-me
DEBUG=true
```

### **Staging (.env.staging)**
```env
# Database
DATABASE_URL=${STAGING_DATABASE_URL}

# Twilio (Limited)
USE_MOCK_SMS=false
TWILIO_ACCOUNT_SID=${STAGING_TWILIO_SID}
TWILIO_AUTH_TOKEN=${STAGING_TWILIO_TOKEN}
TWILIO_PHONE_NUMBER=${STAGING_TWILIO_PHONE}

# Admin
ADMIN_PHONES=${STAGING_ADMIN_PHONES}

# Security
SECRET_KEY=${STAGING_SECRET_KEY}
DEBUG=false
```

### **Production (.env.production)**
```env
# Database
DATABASE_URL=${PRODUCTION_DATABASE_URL}

# Twilio (Full)
USE_MOCK_SMS=false
TWILIO_ACCOUNT_SID=${PRODUCTION_TWILIO_SID}
TWILIO_AUTH_TOKEN=${PRODUCTION_TWILIO_TOKEN}
TWILIO_PHONE_NUMBER=${PRODUCTION_TWILIO_PHONE}

# Admin
ADMIN_PHONES=${PRODUCTION_ADMIN_PHONES}

# Security
SECRET_KEY=${PRODUCTION_SECRET_KEY}
DEBUG=false
SENTRY_DSN=${PRODUCTION_SENTRY_DSN}
```

## 🚀 Deployment Process

### **Development → Staging**

#### **Automated Triggers**
- Push to `staging` branch triggers deployment
- Runs automated test suite
- Deploys to staging server
- Runs smoke tests

#### **Manual Validation**
- QA team tests new features
- Performance validation
- Security scan
- Database migration test

### **Staging → Production**

#### **Approval Process**
- Staging tests must pass (automated)
- QA sign-off required (manual)
- Product owner approval (manual)
- Security review for sensitive changes

#### **Deployment Steps**
- Database migration (if needed)
- Blue-green deployment
- Health checks
- Monitoring alerts
- Rollback plan ready

## ⚙️ Deployment Scripts

### **Staging Deployment**
```bash
#!/bin/bash
# deploy-staging.sh

echo "🧪 Deploying to Staging Environment..."

# Pull latest staging code
git checkout staging
git pull origin staging

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Run tests
pytest tests/ --env=staging

# Deploy application
systemctl restart contestlet-staging
systemctl restart nginx

# Verify deployment
curl -f https://staging-api.contestlet.com/health || exit 1

echo "✅ Staging deployment completed successfully"
```

### **Production Deployment**
```bash
#!/bin/bash
# deploy-production.sh

echo "🏆 Deploying to Production Environment..."

# Backup database
pg_dump $PRODUCTION_DATABASE_URL > backup-$(date +%Y%m%d-%H%M%S).sql

# Pull latest main code
git checkout main
git pull origin main

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Deploy with zero downtime
./scripts/blue-green-deploy.sh

# Verify deployment
./scripts/health-check.sh

echo "✅ Production deployment completed successfully"
```

## 🔍 Testing Strategy

### **Development Testing**
- Unit tests on every commit
- Integration tests for new features
- Manual testing for UI changes

### **Staging Testing**
- Full integration test suite
- Performance testing
- Security scanning
- User acceptance testing

### **Production Testing**
- Smoke tests post-deployment
- Monitoring and alerting
- Canary releases for major changes

## 📋 AI Assistant Rules

### **✅ AI Development Workflow**

#### **Starting New Work**
1. **Always start from `develop` branch**
2. **Create feature branch** for new work
3. **Make incremental commits** with clear messages
4. **Test locally** before pushing
5. **Create PR to `develop`** when ready

#### **Code Standards**
- Follow existing code patterns
- Add tests for new features
- Update documentation
- Use environment-appropriate configs
- Never commit secrets or credentials

#### **Deployment Rules**
- **Development**: Can deploy directly to test changes
- **Staging**: Only merge from `develop` after testing
- **Production**: Only merge from `staging` after full validation

### **🚫 Restrictions**
- Never commit directly to `main` or `staging`
- Never skip testing phases
- Never deploy untested code to staging/production
- Never hardcode environment-specific values
- Never commit real credentials

## 🎯 Success Metrics

### **Development Velocity**
- Feature delivery time
- Code review turnaround
- Bug detection rate

### **Staging Quality**
- Test coverage percentage
- Bug escape rate to production
- Performance benchmarks

### **Production Stability** 
- Uptime percentage (>99.9%)
- Deployment success rate (>95%)
- Mean time to recovery (<30min)

## 📞 Emergency Procedures

### **Hotfix Process**
```bash
# For critical production bugs
git checkout main
git checkout -b hotfix/critical-bug-fix

# Fix the issue
git commit -m "Hotfix: critical bug description"

# Deploy to staging for verification
git checkout staging
git merge hotfix/critical-bug-fix
# Test in staging

# Deploy to production
git checkout main
git merge hotfix/critical-bug-fix
git push origin main

# Merge back to develop
git checkout develop
git merge main
```

### **Rollback Process**
```bash
# If production deployment fails
git checkout main
git reset --hard HEAD~1  # Go back one commit
git push --force-with-lease origin main

# Trigger emergency deployment
./scripts/emergency-deploy.sh
```

This strategy ensures safe, reliable deployments with clear processes for development teams and AI assistants!
