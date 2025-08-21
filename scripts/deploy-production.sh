#!/bin/bash
# 🏆 PRODUCTION DEPLOYMENT SCRIPT

set -e  # Exit on any error

echo "🏆 Starting Production Deployment..."
echo "===================================="

# Configuration
BRANCH="main"
SERVICE_NAME="contestlet-production"
HEALTH_URL="https://api.contestlet.com/health"
LOG_FILE="/var/log/contestlet/production-deploy.log"
BACKUP_DIR="/backups/contestlet"

# Require confirmation for production deployment
echo "⚠️  PRODUCTION DEPLOYMENT CONFIRMATION"
echo "This will deploy to the live production environment."
read -p "Are you sure you want to continue? (yes/no): " confirmation

if [ "$confirmation" != "yes" ]; then
    echo "❌ Deployment cancelled"
    exit 1
fi

# Create log entry
echo "$(date): Starting production deployment" >> $LOG_FILE

# 1. Pre-deployment Backup
echo "💾 Creating database backup..."
BACKUP_FILE="$BACKUP_DIR/backup-$(date +%Y%m%d-%H%M%S).sql"
mkdir -p $BACKUP_DIR

# Backup database
pg_dump $PRODUCTION_DATABASE_URL > $BACKUP_FILE

if [ $? -eq 0 ]; then
    echo "✅ Database backup created: $BACKUP_FILE"
else
    echo "❌ Database backup failed! Aborting deployment."
    exit 1
fi

# 2. Code Deployment
echo "📦 Pulling latest code from $BRANCH branch..."
git checkout $BRANCH
git pull origin $BRANCH

echo "✅ Code updated to latest $BRANCH"

# 3. Environment Setup
echo "⚙️  Verifying environment configuration..."
if [ ! -f ".env" ]; then
    echo "❌ .env file not found! Please configure production environment."
    exit 1
fi

# 4. Dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

echo "✅ Dependencies installed"

# 5. Database Migration (with backup verification)
echo "🗄️  Running database migrations..."

# Dry run first
alembic upgrade head --sql > migration_preview.sql
echo "📋 Migration preview saved to migration_preview.sql"

read -p "Review migration and confirm to proceed (yes/no): " migration_confirm
if [ "$migration_confirm" != "yes" ]; then
    echo "❌ Migration cancelled"
    exit 1
fi

# Run actual migration
alembic upgrade head

echo "✅ Database migrations completed"

# 6. Testing
echo "🧪 Running production smoke tests..."
python -m pytest tests/smoke/ --env=production -v

if [ $? -ne 0 ]; then
    echo "❌ Smoke tests failed! Consider rollback."
    read -p "Continue with deployment anyway? (yes/no): " continue_confirm
    if [ "$continue_confirm" != "yes" ]; then
        exit 1
    fi
fi

echo "✅ Smoke tests completed"

# 7. Blue-Green Deployment
echo "🔄 Performing blue-green deployment..."

# Start new instance
systemctl start $SERVICE_NAME-new

# Wait for new instance to be ready
sleep 10

# Health check on new instance
NEW_HEALTH_URL="https://api-new.contestlet.com/health"
for i in {1..5}; do
    if curl -f $NEW_HEALTH_URL > /dev/null 2>&1; then
        echo "✅ New instance health check passed!"
        break
    else
        echo "⏳ New instance health check attempt $i/5 failed, retrying..."
        sleep 5
    fi
    
    if [ $i -eq 5 ]; then
        echo "❌ New instance failed to start!"
        systemctl stop $SERVICE_NAME-new
        exit 1
    fi
done

# Switch traffic to new instance
echo "🔀 Switching traffic to new instance..."
nginx -s reload  # Reload nginx config to point to new instance

# Stop old instance
systemctl stop $SERVICE_NAME

# Rename services
systemctl stop $SERVICE_NAME-new
systemctl start $SERVICE_NAME

echo "✅ Blue-green deployment completed"

# 8. Final Health Check
echo "🏥 Running final health check..."
sleep 5

for i in {1..10}; do
    if curl -f $HEALTH_URL > /dev/null 2>&1; then
        echo "✅ Production health check passed!"
        break
    else
        echo "⏳ Health check attempt $i/10 failed, retrying..."
        sleep 3
    fi
    
    if [ $i -eq 10 ]; then
        echo "❌ Production health check failed!"
        echo "🚨 EMERGENCY: Production deployment failed!"
        echo "🔄 Initiating emergency rollback..."
        
        # Emergency rollback
        git checkout HEAD~1
        systemctl restart $SERVICE_NAME
        
        exit 1
    fi
done

# 9. Post-deployment Verification
echo "🔍 Running post-deployment verification..."
python scripts/production_verification.py

# 10. Monitoring Setup
echo "📊 Activating monitoring alerts..."
# curl -X POST $MONITORING_WEBHOOK_URL -d '{"status": "deployed", "version": "'$(git rev-parse HEAD)'"}'

# 11. Success
echo "🎉 Production deployment completed successfully!"
echo "📊 Deployment Summary:"
echo "   - Branch: $BRANCH"
echo "   - Commit: $(git rev-parse HEAD)"
echo "   - Timestamp: $(date)"
echo "   - Backup: $BACKUP_FILE"
echo "   - Health URL: $HEALTH_URL"

# Log success
echo "$(date): Production deployment completed successfully - $(git rev-parse HEAD)" >> $LOG_FILE

echo ""
echo "🔗 Production environment:"
echo "   API: $HEALTH_URL"
echo "   Docs: https://api.contestlet.com/docs"
echo "   Dashboard: https://dashboard.contestlet.com"
echo ""
echo "📋 Post-deployment checklist:"
echo "   ✅ Monitor error rates"
echo "   ✅ Check performance metrics"
echo "   ✅ Verify all integrations"
echo "   ✅ Test critical user flows"
