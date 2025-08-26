# 🗄️ **Database Migrations Documentation**

**Complete documentation for all database migrations and schema changes in Contestlet.**

---

## 📋 **Migration Overview**

This directory contains all database migration scripts used to evolve the Contestlet database schema from initial development to production deployment.

---

## 🔄 **Migration History**

### **Phase 1: Initial Schema Setup**
- **Initial database creation** with basic tables
- **User authentication** system implementation
- **Contest management** tables

### **Phase 2: Role System Implementation**
- **Role-based access control** tables
- **User role management** system
- **Admin and sponsor** profile tables

### **Phase 3: Enhanced Contest Features**
- **Advanced contest configuration** fields
- **SMS template system** implementation
- **Geographic targeting** enhancements

### **Phase 4: Security Implementation**
- **Row Level Security (RLS)** policies
- **User data isolation** implementation
- **Audit logging** and monitoring

---

## 📁 **Migration Files**

### **Core Schema Migrations**

#### **`migrate_role_system_sqlite.sql`**
- **Purpose**: Initial role system implementation for SQLite development
- **Tables**: users, admin_profiles, sponsor_profiles
- **Status**: ✅ Applied to development environment

#### **`migrate_role_system_dev.sql`**
- **Purpose**: Role system updates for development environment
- **Changes**: Enhanced user roles and permissions
- **Status**: ✅ Applied to development environment

#### **`migrate_staging_schema.sql`**
- **Purpose**: Schema synchronization for staging environment
- **Tables**: All core tables with role system
- **Status**: ✅ Applied to staging environment

#### **`migrate_production_schema.sql`**
- **Purpose**: Production schema deployment
- **Tables**: Production-ready schema with all features
- **Status**: ✅ Applied to production environment

### **Feature-Specific Migrations**

#### **`migrate_sponsor_profile_fields.sql`**
- **Purpose**: Add sponsor profile enhancement fields
- **Changes**: Additional sponsor information and verification
- **Status**: ✅ Applied to all environments

#### **`add_image_host_columns.sql`**
- **Purpose**: Add image hosting support for contests
- **Changes**: Image URL and CDN support fields
- **Status**: ✅ Applied to all environments

### **Security Implementation**

#### **`role_system_rls_policies.sql`**
- **Purpose**: Initial RLS policy implementation
- **Features**: Basic row-level security policies
- **Status**: ⚠️ Superseded by newer implementation

#### **`corrected_rls_implementation_v2.sql`**
- **Purpose**: Production-ready RLS implementation
- **Features**: Complete security policies for all tables
- **Status**: ✅ **CURRENT PRODUCTION VERSION**

---

## 🚀 **Current Production Schema**

### **Core Tables**
- **users** - User accounts with role system
- **contests** - Contest information and configuration
- **entries** - Contest participation records
- **sms_templates** - Customizable SMS messages
- **official_rules** - Legal compliance documents
- **notifications** - SMS audit logging
- **admin_profiles** - Admin user profiles
- **sponsor_profiles** - Sponsor user profiles

### **Security Features**
- **Row Level Security (RLS)** enabled on all tables
- **User data isolation** enforced at database level
- **Role-based access control** with proper permissions
- **Audit logging** for all administrative actions

---

## 🔧 **Applying Migrations**

### **Development Environment**
```bash
# SQLite development
sqlite3 contestlet.db < docs/migrations/migrate_role_system_sqlite.sql
```

### **Staging Environment**
```bash
# Supabase staging
psql "postgresql://postgres.staging:password@host:port/db" \
  -f docs/migrations/migrate_staging_schema.sql
```

### **Production Environment**
```bash
# Supabase production
psql "postgresql://postgres.production:password@host:port/db" \
  -f docs/migrations/migrate_production_schema.sql
```

### **Security Policies**
```bash
# Apply RLS policies (staging/production only)
psql "postgresql://postgres.environment:password@host:port/db" \
  -f docs/migrations/corrected_rls_implementation_v2.sql
```

---

## ⚠️ **Migration Guidelines**

### **Before Applying Migrations**
1. **Backup database** - Always create backup before migration
2. **Test in staging** - Never apply production migrations without testing
3. **Review changes** - Understand what the migration will change
4. **Check dependencies** - Ensure all required tables exist

### **Migration Best Practices**
1. **Version control** - All migrations are tracked in git
2. **Rollback plan** - Have a plan to reverse changes if needed
3. **Testing** - Test migrations in staging environment first
4. **Documentation** - Update this file when adding new migrations

### **Environment-Specific Notes**
- **Development**: Use SQLite migrations for local development
- **Staging**: Use Supabase staging branch migrations
- **Production**: Use Supabase production branch migrations
- **Security**: RLS policies only apply to PostgreSQL (Supabase)

---

## 🔍 **Troubleshooting Migrations**

### **Common Issues**
- **Permission errors** - Check database user permissions
- **Missing tables** - Ensure dependencies are created first
- **Constraint violations** - Check data integrity before migration
- **RLS errors** - Verify Supabase connection and permissions

### **Recovery Procedures**
1. **Check migration logs** for specific error messages
2. **Verify database state** matches expected pre-migration state
3. **Rollback if necessary** using backup or reverse migration
4. **Contact database team** for complex migration issues

---

## 📊 **Migration Status Dashboard**

| Environment | Schema Version | RLS Status | Last Updated |
|-------------|----------------|------------|--------------|
| **Development** | Role System v2 | ❌ Not Applicable | SQLite |
| **Staging** | Production v1 | ✅ Enabled | Supabase |
| **Production** | Production v1 | ✅ Enabled | Supabase |

---

## 🎯 **Next Steps**

### **Immediate Actions**
- ✅ **All migrations applied** to respective environments
- ✅ **RLS security implemented** in staging and production
- ✅ **Schema synchronized** across all environments

### **Future Migrations**
- **Performance optimizations** - Index improvements
- **Feature enhancements** - New contest types
- **Security updates** - Enhanced RLS policies
- **Compliance features** - Additional audit logging

---

## 📞 **Support**

### **Migration Issues**
- **Development**: Backend development team
- **Staging/Production**: Database team
- **Security**: Security team

### **Documentation**
- **Schema changes**: Check individual migration files
- **RLS policies**: See `corrected_rls_implementation_v2.sql`
- **Environment setup**: See deployment documentation

---

**🗄️ This migrations directory contains the complete history of database evolution for Contestlet. All migrations are tested and production-ready.** ✨
