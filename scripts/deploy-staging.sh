#!/bin/bash
# 🧪 STAGING DEPLOYMENT SCRIPT

set -e  # Exit on any error

echo "🧪 Starting Staging Deployment..."
echo "================================"

# Configuration
BRANCH="staging"
SERVICE_NAME="contestlet-staging"
HEALTH_URL="https://staging-api.contestlet.com/health"
LOG_FILE="/var/log/contestlet/staging-deploy.log"

# Create log entry
echo "$(date): Starting staging deployment" >> $LOG_FILE

# 1. Code Deployment
echo "📦 Pulling latest code from $BRANCH branch..."
git checkout $BRANCH
git pull origin $BRANCH

echo "✅ Code updated to latest $BRANCH"

# 2. Environment Setup
echo "⚙️  Setting up environment..."
if [ ! -f ".env" ]; then
    echo "🔧 Creating .env from staging template..."
    cp environments/staging.env.template .env
    echo "⚠️  Please configure .env with staging secrets"
fi

# 3. Dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

echo "✅ Dependencies installed"

# 4. Database Migration
echo "🗄️  Running database migrations..."
alembic upgrade head

echo "✅ Database migrations completed"

# 5. Testing
echo "🧪 Running tests..."
python -m pytest tests/ --env=staging -v

if [ $? -ne 0 ]; then
    echo "❌ Tests failed! Aborting deployment."
    exit 1
fi

echo "✅ All tests passed"

# 6. Service Restart
echo "🔄 Restarting services..."

# Stop service gracefully
systemctl stop $SERVICE_NAME

# Start service
systemctl start $SERVICE_NAME

# Restart reverse proxy
systemctl reload nginx

echo "✅ Services restarted"

# 7. Health Check
echo "🏥 Running health check..."
sleep 5  # Wait for service to start

for i in {1..10}; do
    if curl -f $HEALTH_URL > /dev/null 2>&1; then
        echo "✅ Health check passed!"
        break
    else
        echo "⏳ Health check attempt $i/10 failed, retrying..."
        sleep 3
    fi
    
    if [ $i -eq 10 ]; then
        echo "❌ Health check failed after 10 attempts!"
        echo "🔄 Rolling back..."
        systemctl stop $SERVICE_NAME
        git checkout HEAD~1
        systemctl start $SERVICE_NAME
        exit 1
    fi
done

# 8. Smoke Tests
echo "💨 Running smoke tests..."
python scripts/smoke_tests.py --env=staging

if [ $? -ne 0 ]; then
    echo "⚠️  Smoke tests failed but deployment continues"
fi

# 9. Success
echo "🎉 Staging deployment completed successfully!"
echo "📊 Deployment Summary:"
echo "   - Branch: $BRANCH"
echo "   - Timestamp: $(date)"
echo "   - Health URL: $HEALTH_URL"
echo "   - Service: $SERVICE_NAME"

# Log success
echo "$(date): Staging deployment completed successfully" >> $LOG_FILE

echo ""
echo "🔗 Access staging environment:"
echo "   API: $HEALTH_URL"
echo "   Docs: https://staging-api.contestlet.com/docs"
echo ""
echo "📋 Next steps:"
echo "   1. Run QA validation tests"
echo "   2. Test new features thoroughly"
echo "   3. If validated, promote to production"
