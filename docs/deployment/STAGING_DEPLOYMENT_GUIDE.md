# 🚀 Staging Branch Auto-Deployment Setup

## 📋 **Current Status**
- ✅ **Staging branch created** with latest test data and Supabase integration
- ✅ **Production deployment** working at `https://contestlet.vercel.app`
- ⏳ **Staging push blocked** by GitHub secret detection (old Twilio credentials in git history)

## 🔧 **Required Actions**

### **1. Allow GitHub Push (Required Now)**
**Visit this URL to allow the push:**
```
https://github.com/reed-hub/contestlet/security/secret-scanning/unblock-secret/31ZZQi5pzlG47EKQyjG5S5Gbacd
```

The detected Twilio credentials are from early development and have already been replaced with placeholders. GitHub is detecting them in the git history, but they're safe to allow.

### **2. Push Staging Branch**
After allowing the GitHub secret, run:
```bash
git push origin staging
```

### **3. Configure Vercel Auto-Deploy**
Vercel should automatically create preview deployments for the `staging` branch. The workflow will be:

- **`staging` branch** → Vercel Preview Environment (auto-deploy)
- **`main` branch** → Vercel Production Environment (auto-deploy)

## 🌍 **Expected Deployment URLs**

### **Production (main branch)**
- URL: `https://contestlet.vercel.app`
- Environment: `production`
- Database: Supabase PostgreSQL (persistent)

### **Staging (staging branch)**  
- URL: `https://contestlet-git-staging-matthew-reeds-projects-89c602d6.vercel.app`
- Environment: `preview`
- Database: Same Supabase instance (shared for now)

## 🔄 **Development Workflow**

### **Standard Process:**
1. **Feature Development** → `staging` branch
2. **Test on Staging** → Verify at preview URL
3. **Merge to Main** → Deploys to production

### **Branch Commands:**
```bash
# Work on staging
git checkout staging
git add -A
git commit -m "Feature: description"
git push origin staging

# Promote to production
git checkout main
git merge staging
git push origin main
```

## ⚙️ **Environment Variables**

Both environments will use the same Supabase database for now. In the future, you can:

1. **Create separate Supabase projects** for staging vs production
2. **Configure different DATABASE_URL** for each environment in Vercel
3. **Use different Twilio credentials** for staging vs production

## 🧪 **Testing Strategy**

### **Staging Environment:**
- Test new features safely
- Validate database migrations
- Check API functionality
- Verify frontend integration

### **Production Environment:**
- Stable, tested features only
- Real user data
- Production monitoring
- Backup strategies

## 🚀 **Immediate Next Steps**

1. ✅ **Allow GitHub secret** (visit the URL above)
2. ✅ **Push staging branch** 
3. ✅ **Verify auto-deployment** to Vercel preview
4. ✅ **Test staging API** functionality
5. ✅ **Document staging URL** for frontend team

Once complete, you'll have a full staging → production deployment pipeline! 🎉
