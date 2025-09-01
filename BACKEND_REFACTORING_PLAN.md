# 🎯 Backend Refactoring Plan - Clean Architecture

## 📊 **Current State Analysis**

### 🚨 **Critical Issues Identified**
1. **16 Router Files** with massive duplication and mixed concerns
2. **593-line router files** with business logic embedded
3. **Inconsistent Error Handling** - different patterns across files
4. **Hardcoded Magic Numbers** - scattered throughout codebase
5. **Legacy Route Duplication** - `/user/`, `/sponsor/`, `/users/` overlap
6. **Complex Authentication** - multiple token verification patterns
7. **No Type Safety** - missing response validation
8. **Mixed Concerns** - business logic in routers, data access in controllers

---

## 🏗️ **Clean Architecture Target**

### **New Structure**
```
app/
├── api/                    # 🛣️ Thin API layer (controllers only)
│   ├── v1/                 # Versioned API endpoints
│   │   ├── auth/           # Authentication endpoints
│   │   ├── contests/       # Contest endpoints
│   │   ├── admin/          # Admin endpoints
│   │   └── users/          # User endpoints
│   ├── middleware/         # Request/response middleware
│   ├── dependencies/       # FastAPI dependencies
│   └── responses/          # Standardized response models
├── core/                   # 🔧 Core business logic
│   ├── services/           # Business services (domain logic)
│   ├── repositories/       # Data access layer
│   ├── entities/           # Domain entities
│   ├── use_cases/          # Application use cases
│   └── interfaces/         # Contracts/protocols
├── infrastructure/         # 🏭 External concerns
│   ├── database/           # Database configuration
│   ├── external/           # Third-party integrations
│   ├── config/             # Configuration management
│   └── logging/            # Logging setup
└── shared/                 # 🔄 Shared utilities
    ├── constants/          # All constants centralized
    ├── exceptions/         # Custom exceptions
    ├── types/              # Type definitions
    └── utils/              # Pure utility functions
```

---

## 🚀 **Phase 1: Foundation (Constants & Configuration)**

### **1.1 Centralize All Constants**
Create `app/shared/constants/` with:

```python
# app/shared/constants/contest.py
class ContestConstants:
    MAX_NAME_LENGTH = 200
    MIN_NAME_LENGTH = 3
    MAX_DESCRIPTION_LENGTH = 2000
    MIN_DESCRIPTION_LENGTH = 10
    MAX_PRIZE_DESCRIPTION_LENGTH = 1000
    MIN_PRIZE_DESCRIPTION_LENGTH = 5
    DEFAULT_MINIMUM_AGE = 18
    MAX_RADIUS_MILES = 500
    MIN_RADIUS_MILES = 1
    DEFAULT_PAGE_SIZE = 10
    MAX_PAGE_SIZE = 100
    
# app/shared/constants/auth.py
class AuthConstants:
    JWT_ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 1440
    REFRESH_TOKEN_EXPIRE_MINUTES = 10080
    RATE_LIMIT_REQUESTS = 5
    RATE_LIMIT_WINDOW_SECONDS = 300
    OTP_RETRY_AFTER_SECONDS = 300
    
# app/shared/constants/http.py
class HTTPConstants:
    DEFAULT_CORS_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001"
    ]
    ALLOWED_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"]
    ALLOWED_HEADERS = [
        "Accept", "Accept-Language", "Content-Language",
        "Content-Type", "Authorization", "X-Requested-With",
        "Origin", "Access-Control-Request-Method", "Access-Control-Request-Headers"
    ]
```

### **1.2 Standardized Response Models**
```python
# app/api/responses/base.py
from typing import Generic, TypeVar, Optional, Any, Dict
from pydantic import BaseModel

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    """Standardized API response wrapper"""
    success: bool
    data: Optional[T] = None
    message: Optional[str] = None
    errors: Optional[Dict[str, Any]] = None
    meta: Optional[Dict[str, Any]] = None

class PaginatedResponse(BaseModel, Generic[T]):
    """Standardized paginated response"""
    items: List[T]
    total: int
    page: int
    size: int
    total_pages: int
    has_next: bool
    has_prev: bool

# app/api/responses/contest.py
class ContestListResponse(APIResponse[PaginatedResponse[ContestResponse]]):
    """Type-safe contest list response"""
    pass

class ContestDetailResponse(APIResponse[ContestResponse]):
    """Type-safe contest detail response"""
    pass
```

### **1.3 Centralized Error Handling**
```python
# app/shared/exceptions/base.py
from enum import Enum
from typing import Optional, Dict, Any

class ErrorCode(str, Enum):
    # Authentication errors
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    
    # Resource errors
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"
    
    # Business logic errors
    CONTEST_NOT_ACTIVE = "CONTEST_NOT_ACTIVE"
    ENTRY_LIMIT_EXCEEDED = "ENTRY_LIMIT_EXCEEDED"
    CONTEST_PROTECTED = "CONTEST_PROTECTED"
    
    # Validation errors
    INVALID_INPUT = "INVALID_INPUT"
    VALIDATION_FAILED = "VALIDATION_FAILED"

class BusinessException(Exception):
    """Base business logic exception"""
    def __init__(
        self, 
        error_code: ErrorCode, 
        message: str, 
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 400
    ):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        super().__init__(message)

# app/api/middleware/error_handler.py
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from app.shared.exceptions.base import BusinessException
from app.api.responses.base import APIResponse

async def business_exception_handler(request: Request, exc: BusinessException):
    """Global business exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content=APIResponse(
            success=False,
            message=exc.message,
            errors={
                "code": exc.error_code,
                "details": exc.details
            }
        ).dict()
    )
```

---

## 🚀 **Phase 2: Service Layer Refactoring**

### **2.1 Clean Service Interfaces**
```python
# app/core/interfaces/contest_service.py
from abc import ABC, abstractmethod
from typing import List, Optional
from app.core.entities.contest import Contest
from app.shared.types.pagination import PaginationParams

class IContestService(ABC):
    """Contest service interface"""
    
    @abstractmethod
    async def create_contest(self, contest_data: ContestCreateData, creator_id: int) -> Contest:
        """Create a new contest"""
        pass
    
    @abstractmethod
    async def get_active_contests(self, pagination: PaginationParams) -> PaginatedResult[Contest]:
        """Get active contests with pagination"""
        pass
    
    @abstractmethod
    async def delete_contest(self, contest_id: int, user_id: int, user_role: str) -> bool:
        """Delete contest with business rules validation"""
        pass

# app/core/services/contest_service.py
class ContestService(IContestService):
    """Clean contest service implementation"""
    
    def __init__(self, contest_repo: IContestRepository, auth_service: IAuthService):
        self._contest_repo = contest_repo
        self._auth_service = auth_service
    
    async def create_contest(self, contest_data: ContestCreateData, creator_id: int) -> Contest:
        """Create contest with business validation"""
        # Validate creator permissions
        await self._auth_service.validate_contest_creation_permission(creator_id)
        
        # Apply business rules
        contest = Contest.create(contest_data, creator_id)
        
        # Persist
        return await self._contest_repo.save(contest)
    
    async def delete_contest(self, contest_id: int, user_id: int, user_role: str) -> bool:
        """Delete with comprehensive business rules"""
        contest = await self._contest_repo.get_by_id(contest_id)
        if not contest:
            raise BusinessException(ErrorCode.RESOURCE_NOT_FOUND, "Contest not found")
        
        # Check permissions
        if not contest.can_be_deleted_by(user_id, user_role):
            raise BusinessException(
                ErrorCode.INSUFFICIENT_PERMISSIONS, 
                "Cannot delete this contest"
            )
        
        # Check business rules
        if not contest.is_deletable():
            raise BusinessException(
                ErrorCode.CONTEST_PROTECTED,
                f"Contest cannot be deleted: {contest.deletion_restriction_reason()}"
            )
        
        return await self._contest_repo.delete(contest_id)
```

### **2.2 Repository Pattern**
```python
# app/core/interfaces/contest_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional
from app.core.entities.contest import Contest

class IContestRepository(ABC):
    """Contest repository interface"""
    
    @abstractmethod
    async def get_by_id(self, contest_id: int) -> Optional[Contest]:
        pass
    
    @abstractmethod
    async def save(self, contest: Contest) -> Contest:
        pass
    
    @abstractmethod
    async def delete(self, contest_id: int) -> bool:
        pass
    
    @abstractmethod
    async def get_active_contests(self, limit: int, offset: int) -> List[Contest]:
        pass

# app/infrastructure/repositories/contest_repository.py
class SQLAlchemyContestRepository(IContestRepository):
    """SQLAlchemy implementation of contest repository"""
    
    def __init__(self, db: Session):
        self._db = db
    
    async def get_by_id(self, contest_id: int) -> Optional[Contest]:
        """Get contest by ID with proper error handling"""
        db_contest = self._db.query(ContestModel).filter(ContestModel.id == contest_id).first()
        return Contest.from_db_model(db_contest) if db_contest else None
    
    async def save(self, contest: Contest) -> Contest:
        """Save contest with transaction management"""
        db_contest = contest.to_db_model()
        self._db.add(db_contest)
        self._db.commit()
        self._db.refresh(db_contest)
        return Contest.from_db_model(db_contest)
```

---

## 🚀 **Phase 3: API Layer Simplification**

### **3.1 Thin Controllers**
```python
# app/api/v1/contests/controller.py
from fastapi import APIRouter, Depends, Query
from app.core.interfaces.contest_service import IContestService
from app.api.dependencies.auth import get_current_user
from app.api.dependencies.services import get_contest_service
from app.api.responses.contest import ContestListResponse, ContestDetailResponse
from app.shared.types.pagination import PaginationParams

router = APIRouter(prefix="/contests", tags=["contests"])

@router.get("/active", response_model=ContestListResponse)
async def get_active_contests(
    pagination: PaginationParams = Depends(),
    contest_service: IContestService = Depends(get_contest_service)
):
    """Get active contests - clean controller with single responsibility"""
    contests = await contest_service.get_active_contests(pagination)
    return ContestListResponse(
        success=True,
        data=contests,
        message="Active contests retrieved successfully"
    )

@router.delete("/{contest_id}")
async def delete_contest(
    contest_id: int,
    current_user: User = Depends(get_current_user),
    contest_service: IContestService = Depends(get_contest_service)
):
    """Delete contest - business logic delegated to service"""
    success = await contest_service.delete_contest(
        contest_id, 
        current_user.id, 
        current_user.role
    )
    
    return APIResponse(
        success=success,
        message="Contest deleted successfully"
    )
```

### **3.2 Dependency Injection**
```python
# app/api/dependencies/services.py
from fastapi import Depends
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.core.services.contest_service import ContestService
from app.infrastructure.repositories.contest_repository import SQLAlchemyContestRepository

def get_contest_service(db: Session = Depends(get_db)) -> ContestService:
    """Dependency injection for contest service"""
    contest_repo = SQLAlchemyContestRepository(db)
    auth_service = get_auth_service()
    return ContestService(contest_repo, auth_service)

# app/api/dependencies/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.services.auth_service import AuthService

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """Simplified authentication dependency"""
    user = await auth_service.get_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return user
```

---

## 🚀 **Phase 4: Domain Entities**

### **4.1 Rich Domain Models**
```python
# app/core/entities/contest.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from app.shared.exceptions.base import BusinessException, ErrorCode

@dataclass
class Contest:
    """Rich domain entity with business logic"""
    id: Optional[int]
    name: str
    description: str
    start_time: datetime
    end_time: datetime
    status: str
    created_by_user_id: int
    entry_count: int = 0
    winner_selected_at: Optional[datetime] = None
    
    @classmethod
    def create(cls, contest_data: ContestCreateData, creator_id: int) -> 'Contest':
        """Factory method with validation"""
        cls._validate_contest_data(contest_data)
        
        return cls(
            id=None,
            name=contest_data.name.strip(),
            description=contest_data.description.strip(),
            start_time=contest_data.start_time,
            end_time=contest_data.end_time,
            status="draft",
            created_by_user_id=creator_id
        )
    
    def can_be_deleted_by(self, user_id: int, user_role: str) -> bool:
        """Business rule: who can delete this contest"""
        if user_role == "admin":
            return True
        if user_role == "sponsor" and self.created_by_user_id == user_id:
            return True
        return False
    
    def is_deletable(self) -> bool:
        """Business rule: when can contest be deleted"""
        if self.status == "active":
            return False
        if self.entry_count > 0:
            return False
        if self.status == "complete":
            return False
        return True
    
    def deletion_restriction_reason(self) -> str:
        """Get human-readable deletion restriction reason"""
        if self.status == "active":
            return "Contest is currently active"
        if self.entry_count > 0:
            return f"Contest has {self.entry_count} entries"
        if self.status == "complete":
            return "Contest is complete"
        return "Contest cannot be deleted"
    
    @staticmethod
    def _validate_contest_data(data: ContestCreateData):
        """Validate contest creation data"""
        if len(data.name.strip()) < ContestConstants.MIN_NAME_LENGTH:
            raise BusinessException(
                ErrorCode.VALIDATION_FAILED,
                f"Contest name must be at least {ContestConstants.MIN_NAME_LENGTH} characters"
            )
        
        if data.start_time >= data.end_time:
            raise BusinessException(
                ErrorCode.VALIDATION_FAILED,
                "Contest end time must be after start time"
            )
```

---

## 🚀 **Phase 5: Router Consolidation**

### **5.1 Eliminate Duplicate Routes**
**Current:** 16 router files with overlapping concerns
**Target:** 6 clean, focused routers

```python
# Remove these duplicate/legacy routers:
- user.py (deprecated - use users.py)
- sponsor.py (deprecated - use users.py) 
- admin_profile.py (merge into admin.py)
- admin_notifications.py (merge into admin.py)
- admin_import.py (merge into admin.py)

# Keep and clean these core routers:
- auth.py (authentication only)
- contests.py (public contest operations)
- users.py (unified user operations)
- admin.py (all admin operations)
- entries.py (contest entries)
- media.py (file uploads)
```

### **5.2 Unified Admin Router**
```python
# app/api/v1/admin/controller.py
from fastapi import APIRouter
from .contests import router as contests_router
from .users import router as users_router
from .notifications import router as notifications_router
from .import_data import router as import_router

router = APIRouter(prefix="/admin", tags=["admin"])

# Include sub-routers for organization
router.include_router(contests_router)
router.include_router(users_router)
router.include_router(notifications_router)
router.include_router(import_router)

# Core admin endpoints
@router.get("/dashboard")
async def get_dashboard(admin_service: IAdminService = Depends(get_admin_service)):
    """Admin dashboard with clean service delegation"""
    dashboard_data = await admin_service.get_dashboard_data()
    return APIResponse(success=True, data=dashboard_data)
```

---

## 📋 **Implementation Phases**

### **Phase 1: Foundation (Week 1)**
- ✅ Centralize constants and configuration
- ✅ Implement standardized response models
- ✅ Create global error handling system
- ✅ Set up dependency injection framework

### **Phase 2: Service Layer (Week 2)**
- ✅ Extract business logic from routers to services
- ✅ Implement repository pattern
- ✅ Create domain entities with business rules
- ✅ Add comprehensive service tests

### **Phase 3: API Cleanup (Week 3)**
- ✅ Simplify routers to thin controllers
- ✅ Remove duplicate/legacy routes
- ✅ Implement unified authentication
- ✅ Add API response validation

### **Phase 4: Quality & Performance (Week 4)**
- ✅ Add comprehensive error boundaries
- ✅ Implement request/response logging
- ✅ Add performance monitoring
- ✅ Create integration tests

---

## 🎯 **Expected Outcomes**

### **Code Quality Improvements**
- **90% reduction** in code duplication
- **Single Responsibility Principle** enforced
- **Type safety** throughout the application
- **Testable** business logic in services
- **Maintainable** clean architecture

### **Developer Experience**
- **Clear separation of concerns**
- **Predictable error handling**
- **Easy to extend** new features
- **Self-documenting** code structure
- **Fast onboarding** for new developers

### **Performance Benefits**
- **Reduced response times** through optimized queries
- **Better caching** with repository pattern
- **Efficient error handling** without stack traces
- **Scalable** service architecture

---

## 🚀 **Ready to Begin Implementation**

This refactoring plan will transform the codebase into a clean, maintainable, and scalable backend that follows industry best practices. Each phase builds upon the previous one, ensuring a smooth transition without breaking existing functionality.

**Next Step:** Begin Phase 1 implementation with constants centralization and standardized responses.
