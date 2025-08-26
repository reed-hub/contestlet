# 🧪 **Contestlet API - Comprehensive Testing Guide**

**Production-ready testing infrastructure for the Contestlet platform.**

---

## 📋 **Testing Overview**

Contestlet maintains enterprise-grade quality standards through a comprehensive testing strategy that covers:

- ✅ **Unit Testing** - Individual component testing
- ✅ **Integration Testing** - Service layer testing  
- ✅ **API Testing** - Endpoint validation
- ✅ **Security Testing** - RLS and authentication validation
- ✅ **Performance Testing** - Load and stress testing
- ✅ **Coverage Analysis** - Code coverage reporting

---

## 🏗️ **Test Architecture**

### **Directory Structure**
```
tests/
├── conftest.py              # Pytest configuration and fixtures
├── requirements.txt          # Test dependencies
├── run_tests.py             # Comprehensive test runner
├── unit/                    # Unit tests for core services
│   ├── test_auth_service.py
│   ├── test_rate_limiter.py
│   └── test_twilio_service.py
├── integration/             # Integration tests
│   ├── test_contest_service.py
│   ├── test_admin_service.py
│   └── test_notification_service.py
├── api/                     # API endpoint tests
│   ├── test_auth_endpoints.py
│   ├── test_contest_endpoints.py
│   └── test_admin_endpoints.py
├── security/                # Security and RLS tests
│   ├── test_rls_policies.py
│   ├── test_authentication.py
│   └── test_authorization.py
└── performance/             # Performance and load tests
    ├── test_api_performance.py
    ├── test_concurrent_requests.py
    └── test_memory_usage.py
```

---

## 🚀 **Quick Start**

### **1. Install Test Dependencies**
```bash
# Install test requirements
pip install -r tests/requirements.txt

# Or use the test runner
python tests/run_tests.py --install-deps
```

### **2. Run All Tests**
```bash
# Run all tests with coverage
python tests/run_tests.py

# Or use pytest directly
pytest tests/ -v --cov=app --cov-report=html
```

### **3. Run Specific Test Categories**
```bash
# Unit tests only
python tests/run_tests.py --unit

# API tests only
python tests/run_tests.py --api

# Security tests only
python tests/run_tests.py --security

# Performance tests only
python tests/run_tests.py --performance

# Integration tests only
python tests/run_tests.py --integration

# Smoke tests (quick validation)
python tests/run_tests.py --smoke
```

---

## 🧪 **Test Categories**

### **Unit Tests (`tests/unit/`)**
**Purpose**: Test individual components in isolation

**Coverage**:
- ✅ Authentication service (JWT management)
- ✅ Rate limiting service
- ✅ Twilio service
- ✅ Configuration management
- ✅ Database utilities

**Example**:
```python
def test_create_access_token():
    """Test access token creation"""
    token = jwt_manager.create_access_token(
        user_id=1,
        phone="+15551234567",
        role="admin"
    )
    
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0
```

### **Integration Tests (`tests/integration/`)**
**Purpose**: Test service layer interactions

**Coverage**:
- ✅ Contest service business logic
- ✅ Admin service operations
- ✅ Notification service workflows
- ✅ Service-to-service communication

### **API Tests (`tests/api/`)**
**Purpose**: Test HTTP endpoints and responses

**Coverage**:
- ✅ Authentication endpoints
- ✅ Contest management endpoints
- ✅ Admin dashboard endpoints
- ✅ User management endpoints
- ✅ Error handling and validation

### **Security Tests (`tests/security/`)**
**Purpose**: Validate security policies and RLS

**Coverage**:
- ✅ Row Level Security (RLS) policies
- ✅ Authentication requirements
- ✅ Role-based access control
- ✅ Data isolation between users
- ✅ Token validation and expiration

### **Performance Tests (`tests/performance/`)**
**Purpose**: Validate performance characteristics

**Coverage**:
- ✅ Response time benchmarks
- ✅ Concurrent request handling
- ✅ Memory usage patterns
- ✅ Database query performance
- ✅ Load handling capabilities

---

## 🔧 **Test Configuration**

### **Pytest Configuration (`pytest.ini`)**
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --cov=app
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-fail-under=80
```

### **Test Fixtures (`tests/conftest.py`)**
**Database Fixtures**:
- In-memory SQLite database for testing
- Fresh database session for each test
- Automatic table creation and cleanup

**Authentication Fixtures**:
- Admin, sponsor, and user tokens
- Pre-configured authorization headers
- Test user data generation

**Utility Fixtures**:
- Test data factories
- Response validation helpers
- Error assertion utilities

---

## 📊 **Coverage Requirements**

### **Minimum Coverage Thresholds**
- **Overall Coverage**: 80%
- **Core Services**: 90%
- **API Endpoints**: 85%
- **Security Components**: 95%

### **Coverage Reports**
```bash
# Generate coverage reports
python tests/run_tests.py --coverage

# HTML coverage report
open htmlcov/index.html

# XML coverage report (for CI/CD)
cat coverage.xml
```

---

## 🚦 **Test Execution**

### **Local Development**
```bash
# Quick validation
pytest tests/ -x --tb=short

# Full test suite
pytest tests/ -v --cov=app

# Watch mode (requires pytest-watch)
ptw tests/ -- --tb=short
```

### **Continuous Integration**
```bash
# Install dependencies
pip install -r tests/requirements.txt

# Run tests with coverage
pytest tests/ --cov=app --cov-report=xml --cov-fail-under=80

# Run security tests
pytest tests/security/ -v

# Run performance tests
pytest tests/performance/ -v -m "performance"
```

### **Pre-deployment Validation**
```bash
# Full production readiness check
python tests/run_tests.py --all --coverage --lint --types

# Smoke test for quick validation
python tests/run_tests.py --smoke
```

---

## 🎯 **Test Markers**

### **Available Markers**
```python
@pytest.mark.unit          # Unit tests
@pytest.mark.integration   # Integration tests
@pytest.mark.api           # API tests
@pytest.mark.security      # Security tests
@pytest.mark.performance   # Performance tests
@pytest.mark.slow          # Slow tests
@pytest.mark.smoke         # Smoke tests
```

### **Usage Examples**
```bash
# Run only fast tests
pytest tests/ -m "not slow"

# Run security and API tests
pytest tests/ -m "security or api"

# Run all tests except performance
pytest tests/ -m "not performance"
```

---

## 🔍 **Test Data Management**

### **Test Data Factories**
```python
@pytest.fixture
def sample_contest_data() -> Dict[str, Any]:
    """Sample contest data for testing"""
    return {
        "name": "Test Contest",
        "description": "A test contest for testing purposes",
        "start_time": datetime.utcnow() + timedelta(hours=1),
        "end_time": datetime.utcnow() + timedelta(days=7),
        "prize_description": "Test prize worth $100"
    }
```

### **Database Seeding**
```python
def test_with_test_data(db_session: Session):
    """Test with seeded test data"""
    # Create test user
    user = User(phone="+15551234567", role="user", is_verified=True)
    db_session.add(user)
    db_session.commit()
    
    # Test functionality
    assert user.id is not None
```

---

## 🚨 **Error Handling Tests**

### **Validation Error Testing**
```python
def test_invalid_input_validation(client: TestClient):
    """Test input validation error handling"""
    response = client.post("/auth/request-otp", json={"phone": "invalid"})
    
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
```

### **Authentication Error Testing**
```python
def test_unauthorized_access(client: TestClient):
    """Test unauthorized access handling"""
    response = client.get("/admin/dashboard")
    
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
```

---

## 📈 **Performance Benchmarks**

### **Response Time Requirements**
- **Health Check**: < 100ms
- **Public Endpoints**: < 200ms
- **Authenticated Endpoints**: < 500ms
- **Database Queries**: < 300ms

### **Load Testing**
```python
def test_concurrent_requests(client: TestClient):
    """Test concurrent request handling"""
    import threading
    
    def make_request():
        response = client.get("/")
        assert response.status_code == 200
    
    # Start 10 concurrent requests
    threads = [threading.Thread(target=make_request) for _ in range(10)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
```

---

## 🔒 **Security Testing**

### **RLS Policy Validation**
```python
def test_user_data_isolation(client: TestClient, db_session: Session):
    """Test that users can only access their own data"""
    # Create test users and data
    user1 = create_test_user(db_session, {"phone": "+15551234567"})
    user2 = create_test_user(db_session, {"phone": "+15559876543"})
    
    # User1 should only see their own data
    response = client.get("/entries/mine", headers=get_user_headers(user1))
    data = response.json()
    
    for entry in data:
        assert entry["user_id"] == user1.id
```

### **Authentication Bypass Testing**
```python
def test_authentication_required(client: TestClient):
    """Test that protected endpoints require authentication"""
    protected_endpoints = [
        "/admin/dashboard",
        "/user/profile",
        "/admin/contests"
    ]
    
    for endpoint in protected_endpoints:
        response = client.get(endpoint)
        assert response.status_code == 401
```

---

## 🚀 **Production Readiness Checklist**

### **Test Coverage**
- [ ] **Unit Tests**: All core services covered
- [ ] **Integration Tests**: Service interactions validated
- [ ] **API Tests**: All endpoints tested
- [ ] **Security Tests**: RLS policies validated
- [ ] **Performance Tests**: Benchmarks established

### **Quality Gates**
- [ ] **Coverage Threshold**: ≥80% overall coverage
- [ ] **Test Execution**: All tests pass
- [ ] **Performance**: Response times within limits
- [ ] **Security**: All RLS policies validated
- [ ] **Error Handling**: Comprehensive error testing

### **Documentation**
- [ ] **Test Documentation**: This guide complete
- [ ] **API Documentation**: OpenAPI/Swagger updated
- [ ] **Deployment Guide**: Production deployment steps
- [ ] **Monitoring Setup**: Health checks and metrics

---

## 🛠️ **Troubleshooting**

### **Common Issues**

#### **Database Connection Errors**
```bash
# Ensure test database is accessible
export DATABASE_URL="sqlite:///:memory:"
pytest tests/ -v
```

#### **Import Errors**
```bash
# Install test dependencies
pip install -r tests/requirements.txt

# Check Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### **Performance Test Failures**
```bash
# Run performance tests in isolation
pytest tests/performance/ -v -m "performance"

# Check system resources
top -l 1 | grep python
```

### **Debug Mode**
```bash
# Run tests with debug output
pytest tests/ -v -s --tb=long

# Run specific test with debug
pytest tests/api/test_auth_endpoints.py::TestAuthEndpoints::test_health_check -v -s
```

---

## 📚 **Additional Resources**

### **Testing Best Practices**
- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/14/orm/session_transaction.html#joining-a-session-into-an-external-transaction)

### **Performance Testing**
- [Locust Load Testing](https://locust.io/)
- [Apache Bench](https://httpd.apache.org/docs/2.4/programs/ab.html)
- [Artillery](https://artillery.io/)

### **Security Testing**
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [SQL Injection Testing](https://owasp.org/www-community/attacks/SQL_Injection)
- [JWT Security](https://jwt.io/introduction)

---

## 🎯 **Next Steps**

### **Immediate Actions**
1. **Install test dependencies**: `pip install -r tests/requirements.txt`
2. **Run smoke tests**: `python tests/run_tests.py --smoke`
3. **Review coverage**: `python tests/run_tests.py --coverage`
4. **Fix any failing tests**

### **Continuous Improvement**
1. **Add new tests** for new features
2. **Update existing tests** when APIs change
3. **Monitor performance** benchmarks
4. **Enhance security** testing coverage

---

**🎉 With this comprehensive testing infrastructure, Contestlet is now production-ready and maintainable!**
