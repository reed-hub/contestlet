# 🗄️ Supabase Setup Guide

## Current Status
- ✅ Supabase project created
- ❌ Need correct connection string (pooler format)
- ⏳ Waiting for connection string verification

## Expected Connection String Format
Your connection string should look like one of these:

### Session Mode (Recommended for Apps)
```
postgresql://postgres.nwekuurfwwkmcfeyptvc:wbGXUNSKLsBvWxsJ@aws-0-[region].pooler.supabase.com:5432/postgres
```

### Transaction Mode (Alternative)
```
postgresql://postgres.nwekuurfwwkmcfeyptvc:wbGXUNSKLsBvWxsJ@aws-0-[region].pooler.supabase.com:6543/postgres
```

## Where to Find It
1. **Supabase Dashboard** → **Settings** → **Database**
2. Look for **"Connection string"** section
3. Choose **"Session mode"** or **"Transaction mode"**
4. Copy the full URL

## Current Issue
The format `db.nwekuurfwwkmcfeyptvc.supabase.co` doesn't resolve - likely because Supabase uses pooler connections for external access.

## Next Steps
1. ✅ Get correct connection string from Supabase
2. ✅ Test connection locally
3. ✅ Deploy to Vercel with DATABASE_URL
4. ✅ Verify all API endpoints work

## Deployment Commands (Ready)
```bash
# Test locally (once we have correct URL)
export DATABASE_URL="postgresql://postgres.nwekuurfwwkmcfeyptvc:wbGXUNSKLsBvWxsJ@[correct-host]:5432/postgres"
python3 -m uvicorn app.main:app --reload

# Deploy to Vercel
vercel --prod
# Then add DATABASE_URL to Vercel environment variables
```
