#!/bin/bash
# 🚀 Vercel Environment Variables Setup
# Run this script to configure your Vercel project environments

echo '🔧 Setting up Vercel environment variables...'

echo '🏆 Setting Production environment variables...'
vercel env add JWT_ALGORITHM production --value="HS256"
vercel env add JWT_EXPIRE_MINUTES production --value="1440"
vercel env add RATE_LIMIT_REQUESTS production --value="5"
vercel env add RATE_LIMIT_WINDOW production --value="300"
vercel env add ENVIRONMENT production --value="production"
vercel env add DEBUG production --value="false"
vercel env add LOG_LEVEL production --value="WARNING"
vercel env add USE_MOCK_SMS production --value="false"
vercel env add DATABASE_URL production --value="${PRODUCTION_DATABASE_URL}"
vercel env add SECRET_KEY production --value="${PRODUCTION_SECRET_KEY}"
vercel env add TWILIO_ACCOUNT_SID production --value="${PRODUCTION_TWILIO_ACCOUNT_SID}"
vercel env add TWILIO_AUTH_TOKEN production --value="${PRODUCTION_TWILIO_AUTH_TOKEN}"
vercel env add TWILIO_PHONE_NUMBER production --value="${PRODUCTION_TWILIO_PHONE_NUMBER}"
vercel env add TWILIO_VERIFY_SERVICE_SID production --value="${PRODUCTION_TWILIO_VERIFY_SERVICE_SID}"
vercel env add ADMIN_TOKEN production --value="${PRODUCTION_ADMIN_TOKEN}"
vercel env add ADMIN_PHONES production --value="${PRODUCTION_ADMIN_PHONES}"
vercel env add CORS_ORIGINS production --value="https://app.contestlet.com,https://contestlet.com"
vercel env add REDIS_URL production --value="${PRODUCTION_REDIS_URL}"
vercel env add SENTRY_DSN production --value="${PRODUCTION_SENTRY_DSN}"

echo '🧪 Setting Preview (Staging) environment variables...'
vercel env add JWT_ALGORITHM preview --value="HS256"
vercel env add JWT_EXPIRE_MINUTES preview --value="1440"
vercel env add RATE_LIMIT_REQUESTS preview --value="5"
vercel env add RATE_LIMIT_WINDOW preview --value="300"
vercel env add ENVIRONMENT preview --value="staging"
vercel env add DEBUG preview --value="false"
vercel env add LOG_LEVEL preview --value="INFO"
vercel env add USE_MOCK_SMS preview --value="false"
vercel env add DATABASE_URL preview --value="${STAGING_DATABASE_URL}"
vercel env add SECRET_KEY preview --value="${STAGING_SECRET_KEY}"
vercel env add TWILIO_ACCOUNT_SID preview --value="${STAGING_TWILIO_ACCOUNT_SID}"
vercel env add TWILIO_AUTH_TOKEN preview --value="${STAGING_TWILIO_AUTH_TOKEN}"
vercel env add TWILIO_PHONE_NUMBER preview --value="${STAGING_TWILIO_PHONE_NUMBER}"
vercel env add TWILIO_VERIFY_SERVICE_SID preview --value="${STAGING_TWILIO_VERIFY_SERVICE_SID}"
vercel env add ADMIN_TOKEN preview --value="${STAGING_ADMIN_TOKEN}"
vercel env add ADMIN_PHONES preview --value="${STAGING_ADMIN_PHONES}"
vercel env add CORS_ORIGINS preview --value="https://staging.contestlet.com,https://contestlet-frontend-git-staging.vercel.app"
vercel env add REDIS_URL preview --value="${STAGING_REDIS_URL}"
vercel env add SENTRY_DSN preview --value="${STAGING_SENTRY_DSN}"

echo '✅ Environment variables configured!'
echo '📋 Next steps:'
echo '  1. Replace ${...} placeholders with actual values'
echo '  2. Run: vercel --prod to deploy production'
echo '  3. Run: vercel to deploy preview'