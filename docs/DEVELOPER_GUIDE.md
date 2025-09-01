# 👨‍💻 Contestlet Developer Guide

**Comprehensive guide for developers working on the Contestlet platform.**

---

## 🚀 **Quick Start for New Developers**

### **1. First Time Setup**
```bash
# Clone repository
git clone <repository-url>
cd contestlet

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp environments/development.env.template .env

# Run locally
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### **2. Verify Setup**
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Test OTP**: Use phone `+18187958204` with any 6-digit code

### **3. Essential Reading**
- **[Cursor Agent Onboarding](../CURSOR_AGENT_ONBOARDING.md)** - Complete platform overview
- **[Enhanced Status System](./backend/ENHANCED_CONTEST_STATUS_SYSTEM.md)** - Core workflow system
- **[API Quick Reference](./api-integration/API_QUICK_REFERENCE.md)** - All endpoints

---

## 🏗️ **Architecture Overview**

### **🎯 Core Concepts**

#### **Enhanced Contest Status System**
The platform uses an 8-state workflow that separates publication from lifecycle:

```
SPONSOR WORKFLOW:
Draft → Edit → Submit → Admin Review → Published

CONTEST LIFECYCLE:
Published → Upcoming → Active → Ended → Complete
```

#### **Role-Based Access Control**
- **Admin**: Full access, approval management, system oversight
- **Sponsor**: Own contest management, draft workflow, submission process  
- **User**: Contest participation, entry management, profile access
- **Public**: Contest discovery, entry submission (no auth required)

#### **Multi-Environment Architecture**
- **Development**: Local SQLite, mock SMS, basic auth
- **Staging**: Supabase staging, real SMS (whitelist), full RLS
- **Production**: Supabase production, full SMS, enterprise RLS

### **📁 Project Structure**

```
contestlet/
├── app/                          # 🚀 Main application
│   ├── core/                    # 🔧 Core utilities
│   │   ├── config.py           # Environment configuration
│   │   ├── contest_status.py   # Status calculation logic
│   │   ├── auth.py             # JWT authentication
│   │   ├── admin_auth.py       # Admin role validation
│   │   └── twilio_verify_service.py # OTP verification
│   ├── models/                 # 📊 Database models
│   │   ├── contest.py          # Enhanced contest model
│   │   ├── contest_status_audit.py # Status change audit
│   │   ├── user.py             # User with role system
│   │   └── entry.py            # Contest participation
│   ├── routers/                # 🛣️ API endpoints
│   │   ├── contests.py         # Public contest API
│   │   ├── sponsor_workflow.py # Draft & submission workflow
│   │   ├── admin_approval.py   # Approval queue management
│   │   ├── auth.py             # Authentication endpoints
│   │   └── admin_contests.py   # Admin contest management
│   ├── schemas/                # 📝 Validation schemas
│   │   ├── contest.py          # Contest validation
│   │   ├── contest_status.py   # Status management schemas
│   │   └── auth.py             # Authentication schemas
│   ├── services/               # 🔄 Business logic
│   │   └── contest_service.py  # Contest management service
│   └── main.py                 # 🚀 FastAPI application
├── docs/                       # 📚 Documentation
├── environments/               # 🌍 Environment configs
├── migrations/                 # 🗄️ Database migrations
└── tests/                      # 🧪 Test suite
```

---

## 🔧 **Development Workflow**

### **🌿 Branch Strategy**
```
feature/your-feature → develop → staging → main (production)
```

### **📝 Development Process**

#### **1. Feature Development**
```bash
# Create feature branch
git checkout -b feature/enhanced-notifications

# Make changes
# ... development work ...

# Test locally
python -m pytest tests/

# Commit and push
git add .
git commit -m "feat: add enhanced notification system"
git push origin feature/enhanced-notifications
```

#### **2. Testing & Validation**
```bash
# Run all tests
python -m pytest tests/ -v

# Test specific module
python -m pytest tests/test_contest_status.py -v

# Test API endpoints
python tests/test_enhanced_api.py

# Check linting
flake8 app/
```

#### **3. Deployment Process**
```bash
# Deploy to staging
git checkout staging
git merge feature/enhanced-notifications
git push origin staging

# Verify staging deployment
# Test at: https://contestlet-git-staging.vercel.app

# Deploy to production
git checkout main
git merge staging
git push origin main
```

### **🔄 Database Migrations**

#### **Creating Migrations**
```sql
-- Create new migration file
-- docs/migrations/add_new_feature.sql

-- Add migration logic
ALTER TABLE contests ADD COLUMN new_field VARCHAR(50);

-- Update indexes
CREATE INDEX IF NOT EXISTS idx_contests_new_field ON contests(new_field);
```

#### **Applying Migrations**
```bash
# Local development (SQLite)
sqlite3 contestlet.db < docs/migrations/add_new_feature.sql

# Staging/Production (Supabase)
# Apply via Supabase dashboard or SQL editor
```

---

## 🎯 **Enhanced Status System Development**

### **🔄 Status Flow Implementation**

#### **Status Calculation**
```python
# app/core/contest_status.py
def calculate_contest_status(
    current_status: str,
    start_time: datetime,
    end_time: datetime,
    winner_selected_at: Optional[datetime] = None,
    now: Optional[datetime] = None
) -> str:
    # Publication workflow statuses don't change based on time
    if current_status in ['draft', 'awaiting_approval', 'rejected']:
        return current_status
    
    # For published contests, calculate lifecycle status
    if winner_selected_at:
        return 'complete'
    elif end_time <= now:
        return 'ended'
    elif start_time > now:
        return 'upcoming'
    else:
        return 'active'
```

#### **Status Transitions**
```python
# app/services/contest_service.py
def transition_contest_status(
    self, 
    contest_id: int, 
    new_status: str, 
    user_id: int, 
    user_role: str,
    reason: Optional[str] = None
) -> Contest:
    # Validate transition is allowed
    self._validate_status_transition(contest, new_status, user_role, user_id)
    
    # Update contest status
    contest.status = new_status
    
    # Create audit trail
    self._create_status_audit(contest_id, old_status, new_status, user_id, reason)
    
    return contest
```

### **🛠️ Adding New Status States**

#### **1. Update Enum**
```python
# app/core/contest_status.py
class ContestStatus(str, Enum):
    # Existing statuses...
    NEW_STATUS = "new_status"  # Add new status
```

#### **2. Update Calculation Logic**
```python
# app/core/contest_status.py
def calculate_contest_status(...):
    # Add new status logic
    if some_condition:
        return ContestStatus.NEW_STATUS
```

#### **3. Update Permissions**
```python
# app/core/contest_status.py
def can_edit_contest(status: str, user_role: str, is_creator: bool = False) -> bool:
    # Add new status permissions
    if status == ContestStatus.NEW_STATUS:
        return user_role == "admin"
```

#### **4. Update Transitions**
```python
# app/core/contest_status.py
def get_next_possible_statuses(current_status: str, user_role: str) -> list:
    transitions = {
        ContestStatus.NEW_STATUS: {
            "admin": [ContestStatus.ACTIVE, ContestStatus.CANCELLED]
        }
    }
```

---

## 🔌 **API Development**

### **📡 Creating New Endpoints**

#### **1. Define Schema**
```python
# app/schemas/new_feature.py
class NewFeatureRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    
class NewFeatureResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    
    class Config:
        from_attributes = True
```

#### **2. Create Router**
```python
# app/routers/new_feature.py
from fastapi import APIRouter, Depends
from app.schemas.new_feature import NewFeatureRequest, NewFeatureResponse

router = APIRouter(prefix="/new-feature", tags=["new-feature"])

@router.post("/", response_model=NewFeatureResponse)
async def create_new_feature(
    request: NewFeatureRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Implementation logic
    pass
```

#### **3. Register Router**
```python
# app/main.py
from app.routers import new_feature

app.include_router(new_feature.router)
```

### **🔒 Authentication & Authorization**

#### **Role-Based Endpoints**
```python
# Public endpoint (no auth)
@router.get("/public")
async def public_endpoint():
    pass

# User endpoint (JWT required)
@router.get("/user")
async def user_endpoint(current_user: User = Depends(get_current_user)):
    pass

# Admin endpoint (admin role required)
@router.get("/admin")
async def admin_endpoint(admin_user: dict = Depends(get_admin_user)):
    pass

# Sponsor endpoint (sponsor role required)
@router.get("/sponsor")
async def sponsor_endpoint(sponsor_user: User = Depends(get_sponsor_user)):
    pass
```

#### **Permission Validation**
```python
def validate_contest_access(contest: Contest, user: User, action: str) -> bool:
    """Validate user can perform action on contest"""
    from app.core.contest_status import can_edit_contest
    
    # Check ownership for sponsors
    if user.role == "sponsor":
        if contest.created_by_user_id != user.id:
            return False
        return can_edit_contest(contest.status, "sponsor", True)
    
    # Admins can do anything
    if user.role == "admin":
        return True
    
    return False
```

---

## 🗄️ **Database Development**

### **📊 Model Development**

#### **Creating New Models**
```python
# app/models/new_model.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from . import Base
from app.core.datetime_utils import utc_now

class NewModel(Base):
    __tablename__ = "new_models"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    
    # Foreign key relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="new_models")
```

#### **Updating Existing Models**
```python
# Add new field to existing model
class Contest(Base):
    # ... existing fields ...
    new_field = Column(String(50), nullable=True, index=True)
```

### **🔗 Relationship Management**

#### **One-to-Many Relationships**
```python
# Parent model
class Contest(Base):
    entries = relationship("Entry", back_populates="contest")

# Child model  
class Entry(Base):
    contest_id = Column(Integer, ForeignKey("contests.id"))
    contest = relationship("Contest", back_populates="entries")
```

#### **Many-to-Many Relationships**
```python
# Association table
contest_tags = Table(
    'contest_tags',
    Base.metadata,
    Column('contest_id', Integer, ForeignKey('contests.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)

# Models with many-to-many
class Contest(Base):
    tags = relationship("Tag", secondary=contest_tags, back_populates="contests")

class Tag(Base):
    contests = relationship("Contest", secondary=contest_tags, back_populates="tags")
```

---

## 🧪 **Testing Development**

### **📝 Test Structure**

#### **Unit Tests**
```python
# tests/unit/test_contest_status.py
import pytest
from app.core.contest_status import calculate_contest_status

def test_calculate_status_draft():
    """Test draft status calculation"""
    status = calculate_contest_status(
        current_status="draft",
        start_time=datetime.now() + timedelta(days=1),
        end_time=datetime.now() + timedelta(days=2)
    )
    assert status == "draft"

def test_status_transition_validation():
    """Test status transition validation"""
    from app.core.contest_status import get_next_possible_statuses
    
    allowed = get_next_possible_statuses("draft", "sponsor")
    assert "awaiting_approval" in allowed
    assert "active" not in allowed
```

#### **API Tests**
```python
# tests/api/test_sponsor_workflow.py
import pytest
from fastapi.testclient import TestClient

def test_create_draft_contest(client: TestClient, sponsor_token: str):
    """Test creating draft contest"""
    response = client.post(
        "/sponsor/workflow/contests/draft",
        headers={"Authorization": f"Bearer {sponsor_token}"},
        json={
            "name": "Test Draft",
            "description": "Test description",
            # ... other fields
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "draft"
    assert data["name"] == "Test Draft"
```

#### **Integration Tests**
```python
# tests/integration/test_approval_workflow.py
def test_complete_approval_workflow(client: TestClient, sponsor_token: str, admin_token: str):
    """Test complete sponsor → admin approval workflow"""
    
    # 1. Sponsor creates draft
    draft_response = client.post("/sponsor/workflow/contests/draft", ...)
    contest_id = draft_response.json()["id"]
    
    # 2. Sponsor submits for approval
    submit_response = client.post(f"/sponsor/workflow/contests/{contest_id}/submit", ...)
    assert submit_response.json()["new_status"] == "awaiting_approval"
    
    # 3. Admin approves
    approve_response = client.post(
        f"/admin/approval/contests/{contest_id}/approve",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"approved": True, "reason": "Looks good"}
    )
    assert approve_response.json()["new_status"] in ["upcoming", "active"]
```

### **🔧 Test Utilities**

#### **Test Fixtures**
```python
# tests/conftest.py
@pytest.fixture
def sponsor_user(db: Session):
    """Create test sponsor user"""
    user = User(
        phone="+18187958205",
        role="sponsor",
        is_verified=True
    )
    db.add(user)
    db.commit()
    return user

@pytest.fixture
def draft_contest(db: Session, sponsor_user: User):
    """Create test draft contest"""
    contest = Contest(
        name="Test Draft Contest",
        status="draft",
        created_by_user_id=sponsor_user.id,
        # ... other fields
    )
    db.add(contest)
    db.commit()
    return contest
```

#### **Mock Services**
```python
# tests/mocks.py
class MockTwilioService:
    """Mock Twilio service for testing"""
    
    def send_verification(self, phone: str) -> bool:
        return True
    
    def check_verification(self, phone: str, code: str) -> bool:
        return code == "123456"  # Accept any test code
```

---

## 🔒 **Security Development**

### **🛡️ Row Level Security (RLS)**

#### **Understanding RLS Policies**
```sql
-- Example RLS policy for contests
CREATE POLICY "Users can view published contests" ON contests
    FOR SELECT USING (
        status IN ('upcoming', 'active', 'ended', 'complete')
    );

CREATE POLICY "Sponsors can manage own contests" ON contests
    FOR ALL USING (
        auth.jwt() ->> 'role' = 'admin' OR
        (auth.jwt() ->> 'role' = 'sponsor' AND created_by_user_id = (auth.jwt() ->> 'sub')::int)
    );
```

#### **Testing RLS Policies**
```python
# tests/security/test_rls_policies.py
def test_sponsor_can_only_see_own_contests(sponsor_client, other_sponsor_contest):
    """Test sponsors can only see their own contests"""
    response = sponsor_client.get("/sponsor/contests")
    contest_ids = [c["id"] for c in response.json()]
    
    # Should not see other sponsor's contest
    assert other_sponsor_contest.id not in contest_ids
```

### **🔐 Authentication Security**

#### **JWT Token Validation**
```python
# app/core/auth.py
def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Validate token type
        if payload.get("type") != token_type:
            return None
            
        # Validate expiration
        if datetime.fromtimestamp(payload.get("exp", 0)) < datetime.utcnow():
            return None
            
        return payload
    except JWTError:
        return None
```

#### **Rate Limiting**
```python
# app/core/rate_limiter.py
class RateLimiter:
    """Rate limiting for OTP requests"""
    
    def __init__(self):
        self.requests = {}  # phone -> [timestamps]
    
    def is_allowed(self, phone: str, max_requests: int = 3, window_minutes: int = 60) -> bool:
        """Check if request is allowed within rate limit"""
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=window_minutes)
        
        # Clean old requests
        if phone in self.requests:
            self.requests[phone] = [
                ts for ts in self.requests[phone] 
                if ts > window_start
            ]
        else:
            self.requests[phone] = []
        
        # Check limit
        if len(self.requests[phone]) >= max_requests:
            return False
        
        # Add current request
        self.requests[phone].append(now)
        return True
```

---

## 📊 **Performance & Monitoring**

### **🚀 Performance Optimization**

#### **Database Query Optimization**
```python
# Efficient queries with proper joins
def get_contests_with_entries(db: Session) -> List[Contest]:
    """Get contests with entry counts efficiently"""
    return db.query(Contest).options(
        joinedload(Contest.entries),  # Eager load to avoid N+1
        joinedload(Contest.official_rules)
    ).filter(
        Contest.status == "active"
    ).all()

# Use subqueries for counts
def get_contest_stats(db: Session) -> dict:
    """Get contest statistics efficiently"""
    return {
        "total": db.query(Contest).count(),
        "active": db.query(Contest).filter(Contest.status == "active").count(),
        "draft": db.query(Contest).filter(Contest.status == "draft").count()
    }
```

#### **Caching Strategy**
```python
# app/core/cache.py
from functools import lru_cache
from typing import Optional

@lru_cache(maxsize=128)
def get_contest_by_id_cached(contest_id: int) -> Optional[Contest]:
    """Cached contest lookup for frequently accessed contests"""
    # Implementation with cache invalidation logic
    pass
```

### **📈 Monitoring & Logging**

#### **Structured Logging**
```python
# app/core/logging.py
import logging
import json

class StructuredLogger:
    """Structured JSON logging for better monitoring"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def log_api_request(self, method: str, path: str, user_id: Optional[int], duration_ms: float):
        """Log API request with structured data"""
        self.logger.info(json.dumps({
            "event": "api_request",
            "method": method,
            "path": path,
            "user_id": user_id,
            "duration_ms": duration_ms,
            "timestamp": datetime.utcnow().isoformat()
        }))
    
    def log_status_change(self, contest_id: int, old_status: str, new_status: str, user_id: int):
        """Log contest status changes"""
        self.logger.info(json.dumps({
            "event": "status_change",
            "contest_id": contest_id,
            "old_status": old_status,
            "new_status": new_status,
            "changed_by": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }))
```

#### **Health Checks**
```python
# app/routers/health.py
@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Comprehensive health check"""
    checks = {
        "database": False,
        "sms_service": False,
        "status": "unhealthy"
    }
    
    try:
        # Test database connection
        db.execute("SELECT 1")
        checks["database"] = True
        
        # Test SMS service
        sms_service = get_sms_service()
        checks["sms_service"] = sms_service.health_check()
        
        # Overall status
        if all([checks["database"], checks["sms_service"]]):
            checks["status"] = "healthy"
            
    except Exception as e:
        checks["error"] = str(e)
    
    return checks
```

---

## 🔧 **Configuration Management**

### **🌍 Environment Configuration**

#### **Environment Variables**
```python
# app/core/config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Database
    database_url: str = "sqlite:///./contestlet.db"
    
    # Authentication
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Twilio
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_verify_service_sid: Optional[str] = None
    
    # Environment
    environment: str = "development"
    debug: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

#### **Environment-Specific Configs**
```bash
# environments/development.env
DATABASE_URL=sqlite:///./contestlet.db
ENVIRONMENT=development
DEBUG=true
TWILIO_ACCOUNT_SID=mock
TWILIO_AUTH_TOKEN=mock

# environments/staging.env  
DATABASE_URL=postgresql://user:pass@staging-db/contestlet
ENVIRONMENT=staging
DEBUG=false
TWILIO_ACCOUNT_SID=real_sid
TWILIO_AUTH_TOKEN=real_token

# environments/production.env
DATABASE_URL=postgresql://user:pass@prod-db/contestlet
ENVIRONMENT=production
DEBUG=false
TWILIO_ACCOUNT_SID=prod_sid
TWILIO_AUTH_TOKEN=prod_token
```

---

## 📚 **Documentation Standards**

### **📝 Code Documentation**

#### **Docstring Standards**
```python
def transition_contest_status(
    self, 
    contest_id: int, 
    new_status: str, 
    user_id: int, 
    user_role: str,
    reason: Optional[str] = None
) -> Contest:
    """
    Transition contest to a new status with validation and audit.
    
    Args:
        contest_id: ID of contest to update
        new_status: Target status to transition to
        user_id: ID of user making the change
        user_role: Role of user (admin, sponsor, user)
        reason: Optional reason for status change
        
    Returns:
        Updated contest object
        
    Raises:
        ResourceNotFoundError: If contest doesn't exist
        ValidationError: If transition is not allowed
        BusinessLogicError: If business rules prevent transition
        
    Example:
        >>> service.transition_contest_status(
        ...     contest_id=123,
        ...     new_status="active", 
        ...     user_id=1,
        ...     user_role="admin",
        ...     reason="Manual activation"
        ... )
    """
```

#### **API Documentation**
```python
@router.post("/contests/draft", response_model=AdminContestResponse)
async def create_draft_contest(
    contest_data: AdminContestCreate,
    sponsor_user: User = Depends(get_sponsor_user),
    db: Session = Depends(get_db)
):
    """
    Create a new contest in draft status for iterative development.
    
    **Permissions**: Sponsor role required
    
    **Workflow**: 
    1. Creates contest with status="draft"
    2. Only visible to creator
    3. Can be edited freely before submission
    
    **Next Steps**:
    - Use `PUT /contests/{id}/draft` to update
    - Use `POST /contests/{id}/submit` to submit for approval
    """
```

### **📖 README Standards**

#### **Feature Documentation Template**
```markdown
# Feature Name

## Overview
Brief description of what this feature does and why it exists.

## Usage
### Basic Usage
```python
# Code example
```

### Advanced Usage
```python
# Advanced code example
```

## API Reference
- `POST /endpoint` - Description
- `GET /endpoint` - Description

## Configuration
Required environment variables and settings.

## Testing
How to test this feature.

## Troubleshooting
Common issues and solutions.
```

---

## 🚨 **Troubleshooting Guide**

### **🔧 Common Development Issues**

#### **Database Connection Issues**
```python
# Check database connection
def test_db_connection():
    try:
        db = next(get_db())
        db.execute("SELECT 1")
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
```

#### **Authentication Issues**
```python
# Debug JWT tokens
def debug_token(token: str):
    try:
        # Decode without verification to see payload
        payload = jwt.decode(token, options={"verify_signature": False})
        print(f"Token payload: {payload}")
        
        # Check expiration
        exp = datetime.fromtimestamp(payload.get("exp", 0))
        now = datetime.utcnow()
        print(f"Expires: {exp}, Now: {now}, Valid: {exp > now}")
        
    except Exception as e:
        print(f"Token decode error: {e}")
```

#### **Status System Issues**
```python
# Debug status calculations
def debug_contest_status(contest: Contest):
    from app.core.contest_status import calculate_contest_status
    
    now = datetime.utcnow()
    calculated = calculate_contest_status(
        contest.status, contest.start_time, contest.end_time,
        contest.winner_selected_at, now
    )
    
    print(f"Contest {contest.id}:")
    print(f"  Current status: {contest.status}")
    print(f"  Calculated status: {calculated}")
    print(f"  Start: {contest.start_time}")
    print(f"  End: {contest.end_time}")
    print(f"  Winner selected: {contest.winner_selected_at}")
    print(f"  Now: {now}")
```

### **🐛 Debugging Tools**

#### **Development Utilities**
```python
# app/core/debug.py
def print_request_info(request):
    """Debug helper for request information"""
    print(f"Method: {request.method}")
    print(f"URL: {request.url}")
    print(f"Headers: {dict(request.headers)}")
    print(f"Query params: {dict(request.query_params)}")

def print_user_context(user: User):
    """Debug helper for user context"""
    print(f"User ID: {user.id}")
    print(f"Phone: {user.phone}")
    print(f"Role: {user.role}")
    print(f"Verified: {user.is_verified}")
```

---

## 🎯 **Best Practices**

### **💻 Code Quality**

#### **Python Standards**
- Follow PEP 8 style guidelines
- Use type hints for all function parameters and returns
- Write comprehensive docstrings for all public functions
- Keep functions focused and single-purpose
- Use meaningful variable and function names

#### **FastAPI Standards**
- Use dependency injection for database sessions and authentication
- Implement proper error handling with custom exceptions
- Use Pydantic models for request/response validation
- Include comprehensive API documentation with examples
- Implement proper HTTP status codes

#### **Database Standards**
- Use proper foreign key relationships
- Implement database indexes for query optimization
- Use timezone-aware datetime objects
- Implement proper data validation at the model level
- Use database migrations for schema changes

### **🔒 Security Best Practices**

#### **Authentication & Authorization**
- Always validate JWT tokens on protected endpoints
- Implement proper role-based access control
- Use secure password hashing (though we use phone-based auth)
- Implement rate limiting for sensitive operations
- Log all authentication attempts and failures

#### **Data Protection**
- Implement Row Level Security (RLS) policies
- Validate all user inputs with Pydantic schemas
- Use parameterized queries to prevent SQL injection
- Implement proper CORS policies
- Sanitize all user-generated content

### **📊 Performance Best Practices**

#### **Database Performance**
- Use eager loading for related data to avoid N+1 queries
- Implement proper database indexing
- Use connection pooling for database connections
- Implement caching for frequently accessed data
- Monitor query performance and optimize slow queries

#### **API Performance**
- Implement pagination for list endpoints
- Use appropriate HTTP caching headers
- Implement request/response compression
- Monitor API response times
- Use async/await for I/O operations

---

## 🎉 **Success Checklist**

### **✅ Development Checklist**

#### **Before Starting Development**
- [ ] Read and understand the Enhanced Status System
- [ ] Set up local development environment
- [ ] Verify all tests pass locally
- [ ] Understand the role-based permission system
- [ ] Review existing API documentation

#### **During Development**
- [ ] Write tests for new functionality
- [ ] Follow established code patterns and conventions
- [ ] Implement proper error handling
- [ ] Add comprehensive logging
- [ ] Update documentation for changes

#### **Before Deployment**
- [ ] All tests pass (unit, integration, API)
- [ ] Code review completed
- [ ] Documentation updated
- [ ] Security review completed
- [ ] Performance testing completed

### **🚀 Deployment Checklist**

#### **Staging Deployment**
- [ ] Deploy to staging environment
- [ ] Verify all endpoints work correctly
- [ ] Test authentication and authorization
- [ ] Verify database migrations applied correctly
- [ ] Test SMS integration (if applicable)

#### **Production Deployment**
- [ ] Staging testing completed successfully
- [ ] Database backup completed
- [ ] Production deployment executed
- [ ] Health checks pass
- [ ] Monitor for errors and performance issues

---

**🎯 This developer guide provides comprehensive coverage for working on the Contestlet platform. Follow these guidelines to maintain code quality, security, and performance standards.** ✨
