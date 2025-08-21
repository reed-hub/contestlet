# 🌿 Supabase Branching Setup Guide

## 📋 **Current Status**
- ✅ **Production**: Using `main` branch (current database)
- ⏳ **Staging**: Need to create `staging` branch and configure

## 🔧 **Setup Steps**

### **1. Create Staging Branch in Supabase**
1. **Go to Supabase Dashboard** → Your contestlet project
2. **Click "Create branch"** (visible in your screenshot)
3. **Configure branch**:
   - **Name**: `staging`
   - **Description**: "Staging environment for testing"
   - **Base**: `main` (copy current data)
4. **Create branch**

### **2. Get New Connection Strings**

After creating the staging branch, you'll have two connection strings:

#### **Production (main branch)**
```
postgresql://postgres.nwekuurfwwkmcfeyptvc:[password]@aws-1-us-east-2.pooler.supabase.com:5432/postgres
```

#### **Staging (staging branch)** - NEW
```
postgresql://postgres.[staging-ref]:[password]@aws-1-us-east-2.pooler.supabase.com:5432/postgres
```

### **3. Update Vercel Environment Variables**

#### **Remove Current Shared DATABASE_URL**
```bash
vercel env rm DATABASE_URL
```

#### **Add Environment-Specific URLs**
```bash
# Production environment
printf "postgresql://postgres.nwekuurfwwkmcfeyptvc:[password]@aws-1-us-east-2.pooler.supabase.com:5432/postgres" | vercel env add DATABASE_URL production

# Staging environment (Preview)
printf "postgresql://postgres.[staging-ref]:[password]@aws-1-us-east-2.pooler.supabase.com:5432/postgres" | vercel env add DATABASE_URL preview
```

### **4. Redeploy Both Environments**
```bash
# Redeploy staging
git push origin staging

# Redeploy production
git push origin main
```

## 🌍 **Expected Result**

### **After Setup:**
- **Staging API**: Uses Supabase `staging` branch (isolated data)
- **Production API**: Uses Supabase `main` branch (production data)
- **Schema Sync**: Can promote changes from staging → main
- **Data Isolation**: Complete separation between environments

### **Benefits:**
- ✅ **Safe testing** - staging won't affect production data
- ✅ **Schema migrations** - test database changes first
- ✅ **Realistic testing** - staging can have its own test data
- ✅ **Easy promotion** - Supabase handles schema sync

## 📊 **Workflow After Setup**

### **Development Process:**
1. **Develop features** → push to `staging` branch
2. **Test on staging** → uses staging Supabase branch
3. **Test passes** → merge to `main` branch
4. **Production deploy** → uses production Supabase branch

### **Database Workflow:**
1. **Schema changes** → test on staging Supabase branch
2. **Data migration testing** → staging environment
3. **Schema promotion** → Supabase branch merge
4. **Production ready** → stable schema and data

## 🚀 **Next Steps**

1. ✅ **Create staging branch** in Supabase
2. ✅ **Get staging connection string** 
3. ✅ **Update Vercel environment variables**
4. ✅ **Test both environments** with separate data
5. ✅ **Verify isolation** - changes in staging don't affect production

This approach gives you **professional environment separation** while keeping everything manageable in a single Supabase project! 🎉
