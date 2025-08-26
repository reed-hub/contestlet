# 🧪 **Testing & Quality Assurance Guide**

**Comprehensive testing documentation for the Contestlet platform.**

---

## 📋 **Testing Overview**

Contestlet maintains high quality standards through comprehensive testing across all environments and features. This guide covers all testing procedures, tools, and best practices.

---

## 🎯 **Testing Strategy**

### **Multi-Environment Testing**
- **Development** - Local testing with SQLite
- **Staging** - Supabase staging branch testing
- **Production** - Live environment validation

### **Testing Layers**
1. **Unit Testing** - Individual component testing
2. **Integration Testing** - API endpoint testing
3. **Security Testing** - RLS and authentication validation
4. **End-to-End Testing** - Complete workflow testing
5. **Performance Testing** - Load and stress testing

---

## 🔧 **Testing Tools & Scripts**

### **Core Testing Scripts**

#### **`test_role_system.py`**
- **Purpose**: Comprehensive role system testing
- **Features**: User role validation, permission testing
- **Usage**: `python3 docs/testing/test_role_system.py`
- **Status**: ✅ Production ready

#### **`test_role_system_comprehensive.py`**
- **Purpose**: Extended role system validation
- **Features**: Edge cases, error scenarios, admin functions
- **Usage**: `python3 docs/testing/test_role_system_comprehensive.py`
- **Status**: ✅ Production ready

#### **`test_sponsor_profile_fix.py`**
- **Purpose**: Sponsor profile functionality testing
- **Features**: Profile creation, updates, validation
- **Usage**: `python3 docs/testing/test_sponsor_profile_fix.py`
- **Status**: ✅ Production ready

#### **`test_frontend_backend_integration.md`**
- **Purpose**: Frontend-backend integration testing guide
- **Features**: API endpoint validation, data flow testing
- **Status**: 📚 Documentation only

#### **`test_cors_fix.py`**
- **Purpose**: CORS configuration testing
- **Features**: Cross-origin request validation
- **Usage**: `python3 docs/testing/test_cors_fix.py`
- **Status**: ✅ Production ready

---

## 🧪 **Testing Procedures**

### **1. Local Development Testing**

#### **Setup Local Environment**
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp env.example .env
# Edit .env with local configuration

# Run tests
python3 docs/testing/test_role_system.py
python3 docs/testing/test_sponsor_profile_fix.py
python3 docs/testing/test_cors_fix.py
```

#### **Local Test Coverage**
- ✅ **Role System** - User roles and permissions
- ✅ **Sponsor Profiles** - Profile management
- ✅ **CORS Configuration** - Cross-origin requests
- ✅ **Database Operations** - CRUD operations
- ✅ **Authentication** - JWT and OTP validation

### **2. Staging Environment Testing**

#### **Staging Test Setup**
```bash
# Set staging environment
export DATABASE_URL="postgresql://postgres.staging:password@host:port/db"
export ENVIRONMENT=staging

# Run staging tests
python3 docs/testing/test_role_system_comprehensive.py
```

#### **Staging Test Coverage**
- ✅ **Multi-User Scenarios** - Multiple user interactions
- ✅ **Role Escalation** - Permission boundary testing
- ✅ **Data Isolation** - User data separation
- ✅ **Admin Functions** - Administrative operations
- ✅ **SMS Integration** - Real Twilio testing (whitelist)

### **3. Production Validation**

#### **Production Test Procedures**
```bash
# Production validation (read-only)
export DATABASE_URL="postgresql://postgres.production:password@host:port/db"
export ENVIRONMENT=production

# Run validation tests
python3 docs/testing/test_role_system.py --validate-only
```

#### **Production Test Coverage**
- ✅ **Data Integrity** - Schema validation
- ✅ **Security Policies** - RLS enforcement
- ✅ **Performance** - Response time validation
- ✅ **Integration** - External service connectivity

---

## 🔒 **Security Testing**

### **Row Level Security (RLS) Testing**

#### **User Isolation Testing**
```python
# Test user A cannot access user B's data
user_a_token = get_user_token("user_a_phone")
user_b_data = fetch_user_data(user_a_token, "user_b_id")
assert user_b_data is None or user_b_data.get("error")
```

#### **Admin Access Testing**
```python
# Test admin can access all data
admin_token = get_admin_token()
all_users = fetch_all_users(admin_token)
assert len(all_users) > 0
```

#### **Public Data Access Testing**
```python
# Test public contest viewing
public_contests = fetch_public_contests()
assert len(public_contests) > 0
```

### **Authentication Testing**

#### **JWT Token Validation**
```python
# Test token expiration
expired_token = create_expired_token()
response = make_authenticated_request(expired_token)
assert response.status_code == 401
```

#### **Rate Limiting Testing**
```python
# Test OTP rate limiting
for i in range(10):
    response = request_otp("test_phone")
    if i < 5:
        assert response.status_code == 200
    else:
        assert response.status_code == 429
```

---

## 📊 **Test Data Management**

### **Development Test Data**
- **SQLite Database** - Local test data
- **Mock SMS** - Console output for OTP
- **Test Users** - Sample user accounts
- **Test Contests** - Sample contest data

### **Staging Test Data**
- **Clean Database** - Fresh test data for each deployment
- **Real SMS** - Twilio integration with phone whitelist
- **Test Scenarios** - Comprehensive test cases
- **Performance Data** - Load testing scenarios

### **Production Data Protection**
- **Live Data** - Real user data (read-only testing)
- **No Test Data** - Production environment protection
- **Audit Logging** - All test activities logged
- **Validation Only** - No destructive operations

---

## 🚨 **Testing Best Practices**

### **Before Running Tests**
1. **Environment Check** - Verify correct environment variables
2. **Database Backup** - Backup staging data before testing
3. **Dependencies** - Ensure all required services are running
4. **Permissions** - Verify test user permissions

### **During Testing**
1. **Logging** - Enable detailed logging for debugging
2. **Monitoring** - Monitor system resources during tests
3. **Error Handling** - Capture and document all errors
4. **Data Validation** - Verify test results match expectations

### **After Testing**
1. **Cleanup** - Remove test data and temporary files
2. **Documentation** - Update test results and findings
3. **Issue Reporting** - Document any bugs or issues found
4. **Performance Analysis** - Analyze test performance metrics

---

## 🔍 **Troubleshooting Tests**

### **Common Test Issues**

#### **Database Connection Errors**
```bash
# Check database connection
python3 -c "
import os
from app.database.database import get_database_url
print(f'Database URL: {get_database_url()}')
"
```

#### **Authentication Errors**
```bash
# Verify JWT token format
python3 -c "
from app.core.auth import verify_token
token = 'your_token_here'
result = verify_token(token)
print(f'Token valid: {result is not None}')
"
```

#### **Permission Errors**
```bash
# Check user role and permissions
python3 -c "
from app.core.auth import extract_user_info
token = 'your_token_here'
user_info = extract_user_info(token)
print(f'User role: {user_info.get(\"role\")}')
"
```

### **Test Recovery Procedures**
1. **Reset Test Environment** - Clean database and restart services
2. **Verify Configuration** - Check environment variables and settings
3. **Check Dependencies** - Ensure all required services are running
4. **Review Logs** - Check application and test logs for errors

---

## 📈 **Performance Testing**

### **Load Testing Scenarios**
- **Concurrent Users** - Test with multiple simultaneous users
- **Database Queries** - Validate query performance under load
- **API Response Times** - Measure endpoint response times
- **Memory Usage** - Monitor memory consumption during tests

### **Stress Testing**
- **High Volume** - Test with large amounts of data
- **Rate Limiting** - Validate rate limiting under stress
- **Error Handling** - Test system behavior under failure conditions
- **Recovery** - Test system recovery after stress conditions

---

## 🎯 **Test Coverage Goals**

### **Current Coverage**
- ✅ **API Endpoints** - 100% endpoint coverage
- ✅ **Authentication** - Complete auth flow testing
- ✅ **Role System** - Full role and permission testing
- ✅ **Data Operations** - CRUD operation validation
- ✅ **Security Policies** - RLS and access control testing

### **Target Coverage**
- 🎯 **Integration Tests** - 95% integration coverage
- 🎯 **Performance Tests** - Load testing for all endpoints
- 🎯 **Security Tests** - Penetration testing and vulnerability assessment
- 🎯 **User Experience** - End-to-end workflow testing

---

## 📞 **Testing Support**

### **Test Issues**
- **Development Testing** - Backend development team
- **Staging Testing** - DevOps team
- **Production Testing** - Database and security teams

### **Test Documentation**
- **Test Scripts** - All test files in this directory
- **Test Results** - Documented test outcomes
- **Issue Tracking** - Bug reports and resolution

---

## 🎉 **Testing Success Metrics**

### **Quality Indicators**
- ✅ **Zero Critical Bugs** in production
- ✅ **100% API Coverage** for all endpoints
- ✅ **Security Validation** passed for all environments
- ✅ **Performance Targets** met for all operations

### **Continuous Improvement**
- **Regular Testing** - Automated testing in CI/CD pipeline
- **Test Updates** - Updated tests for new features
- **Coverage Expansion** - Increased test coverage over time
- **Performance Optimization** - Improved test execution times

---

**🧪 This testing guide ensures Contestlet maintains the highest quality standards across all environments and features.** ✨
