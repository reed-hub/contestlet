# 🚀 **Contestlet Quick Start Guide**

**Get up and running with Contestlet in under 10 minutes!**

---

## ⚡ **Prerequisites**

### **Required Software**
- **Python 3.9+** - Core runtime
- **Git** - Version control
- **SQLite** - Local development database (usually included with Python)

### **Optional Software**
- **PostgreSQL** - If you want to use Supabase locally
- **Redis** - For production-like rate limiting
- **Docker** - For containerized development

---

## 🚀 **Quick Start (5 Minutes)**

### **1. Clone the Repository**
```bash
git clone <repository-url>
cd contestlet
```

### **2. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **3. Set Up Environment**
```bash
cp env.example .env
# Edit .env with your configuration (optional for basic setup)
```

### **4. Run the Application**
```bash
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### **5. Access the Application**
**✅ Server Status**: 🟢 **CONFIRMED WORKING**
- **API**: http://localhost:8000 ✅
- **Interactive Docs**: http://localhost:8000/docs ✅
- **ReDoc**: http://localhost:8000/redoc ✅
- **Health Check**: http://localhost:8000/health ✅

**🎉 You're now running Contestlet locally!**

### **6. Verify Everything is Working**
```bash
# Test the health endpoint
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "environment": "development",
  "vercel_env": "local",
  "git_branch": "develop"
}
```

---

## 🔧 **Environment Configuration**

### **Basic Configuration (.env)**
```env
# Database (SQLite for local development)
DATABASE_URL=sqlite:///./contestlet.db

# JWT Settings
SECRET_KEY=your-super-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# SMS Settings (Mock for development)
USE_MOCK_SMS=true

# Admin Settings
ADMIN_PHONES=+1234567890
```

### **Advanced Configuration**
```env
# Twilio Integration (Optional)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_VERIFY_SERVICE_SID=your_verify_sid
USE_MOCK_SMS=false

# Supabase Integration (Optional)
DATABASE_URL=postgresql://postgres.user:password@host:port/db

# Redis (Optional)
REDIS_URL=redis://localhost:6379
```

---

## 🧪 **Testing the Setup**

### **1. Health Check**
```bash
curl http://localhost:8000/health
# Expected: {"status": "healthy"}
```

### **2. API Documentation**
Open http://localhost:8000/docs in your browser to see the interactive API documentation.

### **3. Create a Test Contest**
```bash
# Using the interactive docs at /docs
# Navigate to POST /admin/contests
# Use the "Try it out" feature with sample data
```

---

## 📱 **SMS Integration Testing**

### **Mock SMS Mode (Default)**
When `USE_MOCK_SMS=true`, OTP codes are printed to the console:
```bash
# Request OTP
curl -X POST "http://localhost:8000/auth/request-otp" \
  -H "Content-Type: application/json" \
  -d '{"phone": "+1234567890"}'

# Check console for OTP code
# Use the code to verify OTP
```

### **Real SMS Mode (Optional)**
Set `USE_MOCK_SMS=false` and configure Twilio credentials for real SMS testing.

---

## 🗄️ **Database Setup**

### **SQLite (Default)**
- **File**: `contestlet.db` (created automatically)
- **Location**: Project root directory
- **Features**: Full functionality, no RLS

### **Supabase (Optional)**
```bash
# Set Supabase connection
export DATABASE_URL="postgresql://postgres.user:password@host:port/db"

# Run RLS implementation
psql $DATABASE_URL -f docs/migrations/corrected_rls_implementation_v2.sql
```

---

## 🔐 **Authentication Testing**

### **1. Request OTP**
```bash
curl -X POST "http://localhost:8000/auth/request-otp" \
  -H "Content-Type: application/json" \
  -d '{"phone": "+1234567890"}'
```

### **2. Verify OTP**
```bash
# Use the OTP code from console (mock mode) or SMS (real mode)
curl -X POST "http://localhost:8000/auth/verify-otp" \
  -H "Content-Type: application/json" \
  -d '{"phone": "+1234567890", "otp": "123456"}'
```

### **3. Use JWT Token**
```bash
# Extract JWT from verification response
curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 🎯 **Contest Management Testing**

### **1. Create Contest (Admin)**
```bash
curl -X POST "http://localhost:8000/admin/contests" \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Contest",
    "description": "A test contest",
    "start_time": "2024-12-20T00:00:00Z",
    "end_time": "2024-12-25T00:00:00Z",
    "prize_description": "Test Prize"
  }'
```

### **2. View Active Contests**
```bash
curl "http://localhost:8000/contests/active"
```

### **3. Enter Contest**
```bash
curl -X POST "http://localhost:8000/contests/1/enter" \
  -H "Authorization: Bearer USER_JWT_TOKEN"
```

---

## 🔍 **Common Issues & Solutions**

### **Port Already in Use**
```bash
# Kill process using port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### **Database Connection Issues**
```bash
# Check if SQLite file exists
ls -la contestlet.db

# Remove and recreate if corrupted
rm contestlet.db
python3 -m uvicorn app.main:app --reload
```

### **Import Errors**
```bash
# Ensure you're in the project directory
pwd
# Should show: /path/to/contestlet

# Install dependencies
pip install -r requirements.txt
```

---

## 📚 **Next Steps**

### **1. Explore the Codebase**
- **Models**: `app/models/` - Database models
- **Routers**: `app/routers/` - API endpoints
- **Schemas**: `app/schemas/` - Data validation
- **Core**: `app/core/` - Core services

### **2. Read Documentation**
- **Cursor Agent Onboarding**: `CURSOR_AGENT_ONBOARDING.md`
- **API Documentation**: http://localhost:8000/docs
- **Security Guide**: `FRONTEND_RLS_UPDATE.md`

### **3. Run Tests**
```bash
# Run basic tests
python3 docs/testing/test_role_system.py
python3 docs/testing/test_cors_fix.py
```

### **4. Explore Features**
- **Form Support**: Test all 25 form fields
- **SMS Templates**: Create custom message templates
- **Geographic Targeting**: Test location-based features
- **Admin Tools**: Explore administrative functions

---

## 🎉 **Congratulations!**

You've successfully set up Contestlet and are ready to:
- ✅ **Develop new features**
- ✅ **Test existing functionality**
- ✅ **Explore the codebase**
- ✅ **Contribute to the project**

### **Need Help?**
- **Documentation**: Check the `docs/` directory
- **API Reference**: Use the interactive docs at `/docs`
- **Issues**: Check troubleshooting guides in `docs/troubleshooting/`

---

**🚀 Happy coding with Contestlet!** ✨
