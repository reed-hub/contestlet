# 📚 Contestlet Documentation

Welcome to the Contestlet API documentation. This directory contains all technical documentation organized by category.

## 📋 **Table of Contents**

### 🔌 **API Integration**
- **[Frontend Integration Guide](api-integration/FRONTEND_INTEGRATION_GUIDE.md)** - Complete guide for frontend developers
- **[API Quick Reference](api-integration/API_QUICK_REFERENCE.md)** - Compact endpoint reference
- **[JavaScript SDK](api-integration/contestlet-sdk.js)** - Ready-to-use SDK
- **[Demo HTML](api-integration/demo.html)** - Working examples

### 🚀 **Deployment**
- **[Vercel Deployment Guide](deployment/VERCEL_DEPLOYMENT_GUIDE.md)** - Complete Vercel setup
- **[Staging Deployment Guide](deployment/STAGING_DEPLOYMENT_GUIDE.md)** - Staging environment setup
- **[Deployment Summary](deployment/DEPLOYMENT_SUMMARY.md)** - Quick deployment overview

### 🗄️ **Database**
- **[Supabase Setup](database/setup_supabase.md)** - Database configuration
- **[Environment Separation](database/SUPABASE_ENVIRONMENT_SUCCESS.md)** - Production vs Staging
- **[Supabase Branching](database/SUPABASE_BRANCHING_SETUP.md)** - Branch strategy

### 🧪 **Testing**
- **[Test Data Summary](testing/TEST_DATA_SUMMARY.md)** - Test data and scenarios

### ⏰ **Timezone Handling**
- **[Timezone Guide](TIMEZONE_GUIDE.md)** - Complete timezone implementation

---

## 🎯 **Quick Start**

### **For Frontend Developers:**
1. Read the **[Frontend Integration Guide](api-integration/FRONTEND_INTEGRATION_GUIDE.md)**
2. Use the **[JavaScript SDK](api-integration/contestlet-sdk.js)**
3. Check the **[API Quick Reference](api-integration/API_QUICK_REFERENCE.md)**

### **For Backend Developers:**
1. Review **[Deployment Guide](deployment/VERCEL_DEPLOYMENT_GUIDE.md)**
2. Understand **[Database Setup](database/SUPABASE_ENVIRONMENT_SUCCESS.md)**
3. Check **[Timezone Implementation](TIMEZONE_GUIDE.md)**

### **For DevOps:**
1. Follow **[Vercel Deployment](deployment/VERCEL_DEPLOYMENT_GUIDE.md)**
2. Set up **[Database Branching](database/SUPABASE_BRANCHING_SETUP.md)**
3. Configure **[Environment Separation](database/ENVIRONMENT_SEPARATION_STATUS.md)**

---

## 🌍 **Live Environments**

### **Production**
- **URL**: `https://contestlet-f6b9oh0ag-matthew-reeds-projects-89c602d6.vercel.app`
- **Database**: Supabase Production Branch
- **Status**: ✅ Live

### **Staging**  
- **URL**: `https://contestlet-i7b9utrk0-matthew-reeds-projects-89c602d6.vercel.app`
- **Database**: Supabase Staging Branch
- **Status**: ✅ Ready for Testing

---

## 🔧 **Development Workflow**

```
Local Development → Staging Branch → Production Branch
      ↓                    ↓              ↓
   SQLite/Local      Staging Database  Production Database
```

### **Git Workflow:**
- `staging` branch → Auto-deploys to staging environment
- `main` branch → Auto-deploys to production environment

---

## 📞 **Support**

For questions about:
- **API Integration** → Check `api-integration/` directory
- **Deployment Issues** → Check `deployment/` directory  
- **Database Problems** → Check `database/` directory
- **Testing** → Check `testing/` directory

---

**Last Updated**: January 21, 2025  
**Version**: 1.0 (Environment Separation Complete)