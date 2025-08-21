# 🏗️ Contestlet Project Structure

## 📁 Directory Overview

```
contestlet/
├── 📚 docs/                           # Documentation
│   ├── api-integration/               # Frontend integration guides
│   │   ├── API_QUICK_REFERENCE.md     # API endpoint documentation
│   │   ├── FRONTEND_INTEGRATION_GUIDE.md  # Comprehensive frontend guide
│   │   ├── contestlet-sdk.js          # JavaScript SDK
│   │   ├── demo.html                  # Interactive demo
│   │   └── README.md                  # Documentation index
│   └── TIMEZONE_GUIDE.md              # Comprehensive timezone documentation
│
├── 🐍 app/                            # Main application code
│   ├── core/                          # Core functionality
│   │   ├── admin_auth.py              # Admin authentication
│   │   ├── config.py                  # Application configuration
│   │   ├── datetime_utils.py          # UTC timezone utilities
│   │   ├── rate_limiter.py            # Rate limiting implementation
│   │   ├── sms_notification_service.py # SMS notification service
│   │   ├── timezone_utils.py          # Timezone management utilities
│   │   └── twilio_verify_service.py   # Twilio OTP verification
│   │
│   ├── database/                      # Database configuration
│   │   └── database.py                # SQLAlchemy setup
│   │
│   ├── models/                        # SQLAlchemy models
│   │   ├── __init__.py               # Model exports
│   │   ├── admin_profile.py          # Admin timezone preferences
│   │   ├── contest.py                # Contest model with timezone metadata
│   │   ├── entry.py                  # Contest entry model
│   │   ├── notification.py           # SMS notification logs
│   │   ├── official_rules.py         # Contest legal requirements
│   │   └── user.py                   # User model
│   │
│   ├── routers/                       # API route handlers
│   │   ├── admin.py                  # Admin-only endpoints
│   │   ├── admin_profile.py          # Admin profile management
│   │   ├── auth.py                   # Authentication endpoints
│   │   ├── contests.py               # Public contest endpoints
│   │   └── entries.py                # Entry management endpoints
│   │
│   ├── schemas/                       # Pydantic schemas
│   │   ├── admin.py                  # Admin operation schemas
│   │   ├── auth.py                   # Authentication schemas
│   │   ├── contest.py                # Contest schemas
│   │   ├── entry.py                  # Entry schemas
│   │   └── timezone.py               # Timezone schemas
│   │
│   └── main.py                        # FastAPI application entry point
│
├── 🧪 tests/                          # Test suite
│   ├── unit/                          # Unit tests
│   ├── integration/                   # Integration tests
│   └── smoke/                         # Smoke tests
│
├── ⚙️ environments/                    # Environment configurations
│   ├── development.env.template       # Development environment
│   ├── staging.env.template          # Staging environment
│   └── production.env.template       # Production environment
│
├── 🚀 scripts/                        # Deployment & utility scripts
│   ├── deploy-staging.sh             # Staging deployment script
│   ├── deploy-production.sh          # Production deployment script
│   ├── smoke_tests.py                # Automated smoke tests
│   └── rollback.sh                   # Emergency rollback script
│
├── 🔄 .github/                        # GitHub Actions workflows
│   └── workflows/
│       └── deploy.yml                # CI/CD pipeline
│
├── 📋 Configuration Files
│   ├── .env                          # Local environment (gitignored)
│   ├── .gitignore                    # Git ignore patterns
│   ├── requirements.txt              # Python dependencies
│   ├── alembic.ini                   # Database migration config
│   └── pyproject.toml                # Python project configuration
│
├── 📖 Documentation Files
│   ├── README.md                     # Project overview
│   ├── DEPLOYMENT_STRATEGY.md        # Deployment workflow guide
│   ├── AI_DEVELOPMENT_RULES.md       # Rules for AI assistants
│   ├── PROJECT_STRUCTURE.md          # This file
│   └── TIMEZONE_GUIDE.md             # Timezone implementation guide
│
└── 🗄️ Database Files
    ├── contestlet.db                 # SQLite development database
    ├── alembic/                      # Database migrations
    └── migrate_timestamps_to_utc.py  # UTC migration script
```

## 🌿 Git Branch Structure

```
main (🏆 production)
├── staging (🧪 testing)
└── develop (🔧 development)
    ├── feature/contest-deletion
    ├── feature/timezone-support
    └── hotfix/critical-fixes
```

## 🏃‍♂️ Quick Start Commands

### **Development Setup**
```bash
# Clone repository
git clone https://github.com/your-org/contestlet.git
cd contestlet

# Switch to develop branch
git checkout develop

# Set up environment
cp environments/development.env.template .env

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start development server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### **Feature Development**
```bash
# Start new feature
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "Add feature: description"
git push origin feature/your-feature-name

# Create PR to develop branch
```

### **Testing**
```bash
# Run all tests
python -m pytest tests/

# Run smoke tests
python scripts/smoke_tests.py --env=development

# Check code quality
black app/
flake8 app/
```

### **Deployment**
```bash
# Deploy to staging
git checkout staging
git merge develop
git push origin staging
# → Triggers automatic staging deployment

# Deploy to production (after staging validation)
git checkout main
git merge staging
git push origin main
# → Triggers production deployment with approval
```

## 🔧 Environment Configuration

### **Development**
- **Database**: SQLite (local file)
- **SMS**: Mock mode (no real messages)
- **Logging**: DEBUG level, console output
- **CORS**: Allows localhost origins

### **Staging**
- **Database**: PostgreSQL (staging server)
- **SMS**: Real Twilio with test numbers
- **Logging**: INFO level, file output
- **CORS**: Staging frontend only

### **Production**
- **Database**: PostgreSQL (production server)
- **SMS**: Full Twilio service
- **Logging**: WARNING level, structured output
- **CORS**: Production frontend only
- **Monitoring**: Full observability stack

## 📊 Key Features

### **🏆 Contest Management**
- Create, read, update, delete contests
- Timezone-aware scheduling
- Geolocation support
- Official rules compliance
- Winner selection and notification

### **🔐 Authentication**
- Twilio Verify OTP authentication
- JWT token management
- Role-based access (user/admin)
- Rate limiting protection

### **📱 SMS Notifications**
- Winner notifications
- Contest reminders
- Announcements
- Comprehensive audit logging
- Test mode support

### **🌍 Timezone Support**
- Admin timezone preferences
- UTC storage with local display
- 18+ supported timezones
- Daylight saving time handling
- Contest creation metadata

### **🗑️ Data Management**
- Comprehensive contest deletion
- Atomic database operations
- Complete dependency cleanup
- Audit trail logging

## 🚀 Deployment Pipeline

### **Continuous Integration**
1. **Code Push** → Automated testing
2. **PR Review** → Code quality checks
3. **Merge to Develop** → Integration tests
4. **Promotion to Staging** → QA validation
5. **Promotion to Production** → Live deployment

### **Automated Testing**
- **Unit Tests**: Individual component testing
- **Integration Tests**: API endpoint testing
- **Smoke Tests**: Basic functionality verification
- **Security Scans**: Vulnerability detection

### **Deployment Safety**
- **Database Backups**: Before every production deployment
- **Blue-Green Deployment**: Zero-downtime updates
- **Health Checks**: Automatic validation post-deployment
- **Rollback Plans**: Quick recovery procedures

## 📈 Monitoring & Observability

### **Health Monitoring**
- API endpoint health checks
- Database connectivity monitoring
- SMS service status tracking
- Performance metrics collection

### **Error Tracking**
- Sentry integration for error reporting
- Structured logging for debugging
- Alert notifications for critical issues
- Performance bottleneck identification

### **Business Metrics**
- Contest creation rates
- User engagement tracking
- SMS delivery success rates
- Admin operation audit trails

## 🛡️ Security Features

### **Authentication Security**
- OTP-based phone verification
- JWT token expiration
- Rate limiting on authentication endpoints
- Admin role verification

### **API Security**
- CORS origin validation
- Request rate limiting
- Input validation and sanitization
- SQL injection prevention

### **Data Protection**
- Phone number masking in logs
- Secure credential management
- Environment-specific configurations
- Database backup encryption

This structure provides a scalable, maintainable, and secure foundation for the Contestlet platform! 🏗️✨
