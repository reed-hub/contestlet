# 🚀 **Cursor Agent Onboarding Guide - Contestlet**

**Welcome to the Contestlet codebase!** This document provides everything you need to understand and work with this micro sweepstakes platform.

---

## 🎯 **Project Overview**

**Contestlet** is a production-ready FastAPI backend for hosting micro sweepstakes contests with:
- **100% Form Support** - All 25 frontend form fields implemented
- **Enterprise Security** - Row Level Security (RLS) with Supabase
- **Multi-Environment** - Development, Staging, Production
- **SMS Integration** - Twilio with custom templates
- **Legal Compliance** - Official rules and audit logging

---

## 🏗️ **Architecture & Technology Stack**

### **Backend Framework**
- **FastAPI** - Modern, fast web framework for building APIs
- **Python 3.9+** - Core language
- **SQLAlchemy 2.0** - ORM for database operations
- **Pydantic** - Data validation and serialization

### **Database & Infrastructure**
- **Supabase** - PostgreSQL with real-time features
- **Multi-Environment** - Separate databases for dev/staging/production
- **Row Level Security** - Database-level access control
- **Environment Branching** - Git-based environment management

### **Authentication & Security**
- **JWT Tokens** - Stateless authentication
- **Phone-based OTP** - Twilio Verify integration
- **Role-based Access** - Admin, Sponsor, User roles
- **Rate Limiting** - OTP abuse prevention

### **External Services**
- **Twilio** - SMS verification and notifications
- **Vercel** - Serverless deployment platform
- **Redis** - Rate limiting and caching (production)

---

## 📁 **Project Structure**

```
contestlet/
├── app/                          # 🚀 Main application code
│   ├── core/                    # 🔧 Core services & utilities
│   │   ├── config.py           # Environment configuration
│   │   ├── auth.py             # JWT authentication
│   │   ├── admin_auth.py       # Admin role validation
│   │   ├── twilio_verify_service.py  # OTP verification
│   │   ├── sms_notification_service.py  # SMS messaging
│   │   ├── timezone_utils.py   # Timezone handling
│   │   └── vercel_config.py    # Environment detection
│   ├── database/               # 🗄️ Database configuration
│   │   └── database.py         # Connection and session management
│   ├── models/                 # 📊 SQLAlchemy models
│   │   ├── user.py             # User model with role system
│   │   ├── contest.py          # Enhanced contest model
│   │   ├── entry.py            # Contest entry model
│   │   ├── sms_template.py     # SMS template model
│   │   ├── official_rules.py   # Legal compliance
│   │   └── notification.py     # SMS audit logging
│   ├── routers/                # 🛣️ API endpoints
│   │   ├── auth.py             # Authentication endpoints
│   │   ├── contests.py         # Public contest API
│   │   ├── admin.py            # Admin management
│   │   ├── entries.py          # Entry management
│   │   ├── user.py             # User profile management
│   │   ├── location.py         # Geolocation services
│   │   ├── sponsor.py          # Sponsor profile management
│   │   └── admin_profile.py    # Admin profile management
│   ├── schemas/                # 📝 Pydantic validation schemas
│   │   ├── auth.py             # Authentication schemas
│   │   ├── contest.py          # Contest validation
│   │   ├── user.py             # User validation
│   │   └── admin.py            # Admin validation
│   ├── services/               # 🔄 Business logic
│   │   └── campaign_import_service.py  # Campaign import
│   └── main.py                 # 🚀 FastAPI application entry point
├── docs/                       # 📚 Comprehensive documentation
├── environments/               # 🌍 Environment templates
├── scripts/                    # 🔧 Deployment scripts
├── requirements.txt            # 📦 Python dependencies
└── vercel.json                # 🚀 Vercel deployment config
```

---

## 🔐 **Security Implementation**

### **Row Level Security (RLS)**
- **Database-level security** enforced at the PostgreSQL level
- **User data isolation** - users can only access their own data
- **Admin bypass** - admins can access all data
- **Public data access** - contests and rules publicly viewable

### **Authentication Flow**
```
1. User requests OTP → Twilio sends SMS
2. User verifies OTP → Backend validates
3. Backend issues JWT → Contains user_id, phone, role
4. Frontend includes JWT → In Authorization header
5. Backend validates JWT → Extracts user context
6. RLS policies enforce → Data access permissions
```

### **Role System**
- **User** - Can view/edit own profile, enter contests
- **Sponsor** - Can manage own contests and entries
- **Admin** - Full access to all data and management

---

## 🌍 **Environment Management**

### **Three-Environment Strategy**
```
Development (Local) → Staging → Production
```

### **Environment-Specific Configurations**
- **Development**: SQLite database, mock SMS, localhost CORS
- **Staging**: Supabase staging branch, real SMS (whitelist), preview domain
- **Production**: Supabase production branch, full SMS, production domain

### **Database Branching**
- **Supabase branches** for each environment
- **Schema synchronization** between environments
- **Data isolation** - staging has clean test data

---

## 📱 **SMS Integration**

### **Twilio Services**
- **Verify API** - OTP verification
- **SMS API** - Contest notifications
- **Template System** - Customizable messages with variables

### **Template Variables**
```
{contest_name}        # Contest name
{prize_description}   # Prize details
{winner_name}         # Winner's name
{claim_instructions}  # How to claim prize
{sponsor_name}        # Contest sponsor
{end_time}           # Contest end time
```

### **Environment-Aware SMS**
- **Development**: Mock SMS (console output)
- **Staging**: Real SMS with phone whitelist
- **Production**: Full SMS integration

---

## 🎯 **Form Support System**

### **100% Frontend Form Coverage**
All 25 form fields are fully supported:

| Category | Fields | Features |
|----------|--------|----------|
| **Basic Info** | 8 | Name, description, location, timing |
| **Advanced Options** | 10 | Contest type, entry methods, limits |
| **SMS Templates** | 3 | Entry, winner, non-winner messages |
| **Legal Compliance** | 6 | Rules, terms, age validation |

### **Contest Configuration**
- **Types**: general, sweepstakes, instant_win
- **Entry Methods**: sms, email, web_form
- **Winner Selection**: random, scheduled, instant
- **Geographic Targeting**: radius, states, custom locations

---

## 🚀 **Development Workflow**

### **Local Development Setup**
```bash
# 1. Clone repository
git clone <repository-url>
cd contestlet

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment
cp env.example .env
# Edit .env with your configuration

# 4. Run development server
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### **Branch Strategy**
```
feature-branch → staging → main (production)
```

### **Testing Process**
1. **Local Development** - Test with local database
2. **Staging Deployment** - Test with staging Supabase
3. **Production Merge** - Deploy to production

---

## 📊 **Database Schema**

### **Core Tables**
- **users** - User accounts with role system
- **contests** - Contest information and configuration
- **entries** - Contest participation records
- **sms_templates** - Customizable SMS messages
- **official_rules** - Legal compliance documents
- **notifications** - SMS audit logging

### **Key Relationships**
- Users can have multiple contest entries
- Contests can have multiple SMS templates
- Contests require official rules
- All actions are logged in notifications

---

## 🔧 **Common Development Tasks**

### **Adding New API Endpoints**
1. **Create router** in `app/routers/`
2. **Define schemas** in `app/schemas/`
3. **Add to main.py** router registration
4. **Update documentation** in docs/

### **Database Schema Changes**
1. **Update models** in `app/models/`
2. **Create migration** SQL script
3. **Test in staging** first
4. **Apply to production** after validation

### **Environment Configuration**
1. **Update templates** in `environments/`
2. **Set Vercel variables** for deployment
3. **Test configuration** in staging
4. **Deploy to production**

---

## 🧪 **Testing & Quality Assurance**

### **Test Coverage Areas**
- **API Endpoints** - All endpoints tested
- **Schema Validation** - All form fields validated
- **SMS Integration** - Mock and real SMS testing
- **Security Policies** - RLS and authentication testing
- **Multi-Environment** - All environments validated

### **Testing Tools**
- **FastAPI TestClient** - API endpoint testing
- **SQLite** - Local development testing
- **Supabase** - Staging and production testing
- **Twilio Test Credentials** - SMS integration testing

---

## 🚨 **Important Security Notes**

### **JWT Token Security**
- **Never expose** JWT tokens in client-side code
- **Validate expiration** on every request
- **Secure storage** in HTTP-only cookies or secure storage

### **Database Security**
- **RLS policies** enforce data access at database level
- **User isolation** prevents cross-user data access
- **Admin privileges** carefully controlled and audited

### **API Security**
- **Rate limiting** prevents abuse
- **Input validation** prevents injection attacks
- **CORS configuration** restricts cross-origin access

---

## 📚 **Documentation Structure**

### **Core Documentation**
- **README.md** - Project overview and quick start
- **docs/README.md** - Comprehensive documentation hub
- **FRONTEND_RLS_UPDATE.md** - Security implementation details

### **API Documentation**
- **Interactive docs** at `/docs` endpoint
- **ReDoc** at `/redoc` endpoint
- **OpenAPI spec** available programmatically

### **Environment Documentation**
- **Deployment guides** in `docs/deployment/`
- **Database setup** in `docs/database/`
- **API integration** in `docs/api-integration/`

---

## 🔍 **Troubleshooting Common Issues**

### **Database Connection Issues**
- **Check DATABASE_URL** in environment variables
- **Verify Supabase credentials** for staging/production
- **Test connection** with `test_supabase_connection.py`

### **SMS Integration Issues**
- **Check Twilio credentials** in environment
- **Verify phone numbers** are in whitelist (staging)
- **Test with mock SMS** in development

### **Authentication Issues**
- **Verify JWT token** format and expiration
- **Check RLS policies** are properly configured
- **Validate user role** and permissions

---

## 🎯 **Next Steps for New Agents**

### **Immediate Actions**
1. **Read this document** completely
2. **Set up local development** environment
3. **Explore the codebase** structure
4. **Run the application** locally
5. **Review API documentation** at `/docs`

### **Learning Path**
1. **Understand authentication** flow and JWT system
2. **Learn RLS policies** and security implementation
3. **Explore SMS integration** and template system
4. **Review form support** and validation schemas
5. **Understand environment** management and deployment

### **Key Areas to Master**
- **FastAPI application** structure and routing
- **SQLAlchemy models** and relationships
- **Pydantic schemas** and validation
- **Supabase integration** and RLS
- **Twilio SMS** services and templates

---

## 📞 **Getting Help**

### **Documentation Resources**
- **This onboarding guide** - Start here
- **docs/README.md** - Comprehensive documentation hub
- **API documentation** - Interactive docs at `/docs`
- **Code comments** - Inline documentation in source

### **Development Team**
- **Backend Team** - API and database questions
- **DevOps Team** - Deployment and environment questions
- **Security Team** - RLS and authentication questions

---

## 🎉 **Welcome to Contestlet!**

You're now ready to work with a **production-ready, enterprise-grade** micro sweepstakes platform. The codebase is well-structured, thoroughly documented, and follows industry best practices.

**Key strengths:**
- ✅ **100% form support** implemented
- ✅ **Enterprise security** with RLS
- ✅ **Multi-environment** deployment
- ✅ **Comprehensive documentation**
- ✅ **Production ready** and scalable

**Happy coding!** 🚀
