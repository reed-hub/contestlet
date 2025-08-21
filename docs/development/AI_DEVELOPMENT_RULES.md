# 🤖 AI Development Rules & Guidelines

## 🎯 Core Principles for AI Assistants

### **🌿 Always Start on `develop` Branch**
```bash
# ✅ CORRECT: Start every coding session here
git checkout develop
git pull origin develop

# ❌ WRONG: Never start directly on main or staging
git checkout main  # DON'T DO THIS
```

### **📊 Three-Environment Workflow**
```
🔧 develop    →    🧪 staging    →    🏆 main
(Your work)       (QA testing)      (Production)
```

## 🚀 Standard Development Process

### **1. Feature Development**
```bash
# Always start from develop
git checkout develop
git pull origin develop

# Create feature branch
git checkout -b feature/your-feature-name

# Work on feature...
git add .
git commit -m "Add feature: clear description"

# Push when ready
git push origin feature/your-feature-name

# Create PR to develop (never directly to main/staging)
```

### **2. Testing & Validation**
```bash
# Test locally first
python -m pytest tests/

# Run smoke tests
python scripts/smoke_tests.py --env=development

# Only push if tests pass
```

### **3. Environment Promotion**
```bash
# After feature merged to develop
git checkout staging
git merge develop
git push origin staging
# → Triggers staging deployment

# After staging validation
git checkout main  
git merge staging
git push origin main
# → Triggers production deployment
```

## 📋 Code Standards

### **✅ Required Practices**
- **Write tests** for new features
- **Update documentation** when adding endpoints
- **Use environment templates** for configuration
- **Follow existing code patterns**
- **Add clear commit messages**

### **🚫 Forbidden Actions**
- Never commit directly to `main` or `staging`
- Never skip testing phases
- Never hardcode credentials or secrets
- Never break existing functionality
- Never deploy untested code

## 🔧 Environment Usage

### **Development Environment**
```bash
# Use for active development
cp environments/development.env.template .env
# Edit .env with development values

# Start server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
python -m pytest tests/
```

### **Staging Environment**
```bash
# Only for integration testing
# Deployed automatically when staging branch is updated
# Used for QA validation before production
```

### **Production Environment**
```bash
# Only for live user traffic
# Deployed automatically when main branch is updated
# Requires staging validation first
```

## 🛡️ Security Guidelines

### **Credentials Management**
```bash
# ✅ Use environment templates
cp environments/staging.env.template .env

# ✅ Reference environment variables
TWILIO_ACCOUNT_SID=${STAGING_TWILIO_SID}

# ❌ Never hardcode secrets
TWILIO_ACCOUNT_SID=AC1234567890...  # DON'T DO THIS
```

### **Database Handling**
```bash
# ✅ Development: SQLite is fine
DATABASE_URL=sqlite:///./contestlet_dev.db

# ✅ Production: Use PostgreSQL
DATABASE_URL=${PRODUCTION_DATABASE_URL}

# ✅ Always backup before migrations
pg_dump $DATABASE_URL > backup.sql
```

## 📦 Deployment Checklist

### **Before Every Merge**
- [ ] All tests pass locally
- [ ] Code follows project patterns  
- [ ] Documentation updated
- [ ] No hardcoded values
- [ ] Environment variables properly set
- [ ] Database migrations tested

### **Staging Deployment**
- [ ] Merged from `develop` branch only
- [ ] Integration tests pass
- [ ] QA validation completed
- [ ] Performance testing done
- [ ] Security scan passed

### **Production Deployment**
- [ ] Merged from `staging` branch only
- [ ] Staging validation complete
- [ ] Database backup created
- [ ] Rollback plan ready
- [ ] Monitoring alerts active

## 🚨 Emergency Procedures

### **Hotfix Process**
```bash
# For critical production bugs
git checkout main
git checkout -b hotfix/critical-issue

# Fix the issue
git commit -m "Hotfix: critical issue description"

# Test in staging first
git checkout staging
git merge hotfix/critical-issue
# Validate fix works

# Deploy to production
git checkout main
git merge hotfix/critical-issue
git push origin main

# Merge back to develop
git checkout develop
git merge main
```

### **Rollback Process**
```bash
# If deployment fails
git checkout main
git reset --hard HEAD~1
git push --force-with-lease origin main

# Or use deployment script
./scripts/rollback.sh
```

## 🔍 Testing Requirements

### **Unit Tests**
```bash
# Test individual functions
python -m pytest tests/unit/

# Must pass before any merge
```

### **Integration Tests**
```bash
# Test API endpoints
python -m pytest tests/integration/

# Required for staging deployment
```

### **Smoke Tests**
```bash
# Test basic functionality
python scripts/smoke_tests.py --env=development

# Run after every deployment
```

## 📊 Monitoring & Logging

### **Development Logging**
```python
# Use appropriate log levels
import logging
logger = logging.getLogger(__name__)

logger.debug("Development details")
logger.info("General information")
logger.warning("Important warnings")
logger.error("Error conditions")
```

### **Production Monitoring**
- Health checks every 30 seconds
- Error rate alerts
- Performance monitoring
- Database connection tracking

## 🤝 Collaboration Rules

### **Pull Request Process**
1. **Create descriptive PR title**
2. **Add detailed description**
3. **Link to relevant issues**
4. **Request appropriate reviewers**
5. **Respond to feedback promptly**

### **Code Review Guidelines**
- Focus on code quality
- Check for security issues
- Verify tests are included
- Ensure documentation updates
- Validate environment compatibility

## 📈 Success Metrics

### **Development Quality**
- All tests pass
- Code coverage > 80%
- No security vulnerabilities
- Documentation up to date

### **Deployment Success**
- Zero-downtime deployments
- Rollback time < 5 minutes
- Staging validation rate > 95%
- Production uptime > 99.9%

## 🎓 Learning Resources

### **Git Workflow**
- [Git Flow Best Practices](https://nvie.com/posts/a-successful-git-branching-model/)
- [Conventional Commits](https://www.conventionalcommits.org/)

### **Testing**
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [Pytest Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)

### **Deployment**
- [Blue-Green Deployment](https://martinfowler.com/bliki/BlueGreenDeployment.html)
- [Database Migration Best Practices](https://www.postgresql.org/docs/current/ddl-alter.html)

---

**Remember: Quality and safety first! When in doubt, ask for review before deploying.** 🛡️✨
