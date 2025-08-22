#!/usr/bin/env python3
"""
Smart Location System Migration
==============================

This script adds the new smart location system fields to the contests table
while preserving existing location data for backward compatibility.

Usage:
    python smart_location_migration.py [environment]
    
    environment: development, staging, production (optional, defaults to development)
"""

import os
import sys
from sqlalchemy import create_engine, text
from urllib.parse import urlparse

def get_database_url(environment="development"):
    """Get the database URL for the specified environment"""
    
    if environment == "development":
        # Use local SQLite for development
        return "sqlite:///./contestlet.db"
    elif environment == "staging":
        # Use staging Supabase database
        return os.getenv('STAGING_DATABASE_URL', 'postgresql://postgres:wbGXUNSKLsBvWxsJ@db.nwekuurfwwkmcfeyptvc.supabase.co:5432/postgres')
    elif environment == "production":
        # Use production Supabase database
        return os.getenv('DATABASE_URL', 'postgresql://postgres:wbGXUNSKLsBvWxsJ@db.nwekuurfwwkmcfeyptvc.supabase.co:5432/postgres')
    else:
        raise ValueError(f"Unknown environment: {environment}")

def add_smart_location_fields(engine, environment):
    """Add smart location system fields to contests table"""
    
    print(f"🔧 Adding smart location system fields to {environment} database...")
    
    # SQL commands to add the new columns
    migrations = []
    
    if "sqlite" in str(engine.url):
        # SQLite migrations
        migrations = [
            "ALTER TABLE contests ADD COLUMN location_type TEXT DEFAULT 'united_states';",
            "ALTER TABLE contests ADD COLUMN selected_states TEXT;",  # JSON as TEXT in SQLite
            "ALTER TABLE contests ADD COLUMN radius_address TEXT;",
            "ALTER TABLE contests ADD COLUMN radius_miles INTEGER;",
            "ALTER TABLE contests ADD COLUMN radius_latitude REAL;",
            "ALTER TABLE contests ADD COLUMN radius_longitude REAL;",
        ]
    else:
        # PostgreSQL migrations
        migrations = [
            "ALTER TABLE contests ADD COLUMN IF NOT EXISTS location_type VARCHAR(20) DEFAULT 'united_states';",
            "ALTER TABLE contests ADD COLUMN IF NOT EXISTS selected_states JSONB;",
            "ALTER TABLE contests ADD COLUMN IF NOT EXISTS radius_address VARCHAR(500);",
            "ALTER TABLE contests ADD COLUMN IF NOT EXISTS radius_miles INTEGER;",
            "ALTER TABLE contests ADD COLUMN IF NOT EXISTS radius_latitude DECIMAL(10, 8);",
            "ALTER TABLE contests ADD COLUMN IF NOT EXISTS radius_longitude DECIMAL(11, 8);",
        ]
    
    # Execute each migration
    for i, migration_sql in enumerate(migrations, 1):
        try:
            print(f"📝 Executing migration {i}/{len(migrations)}...")
            
            with engine.begin() as connection:  # Auto-commit transaction
                connection.execute(text(migration_sql))
                print(f"   ✅ Migration {i} completed successfully")
                
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                print(f"   ℹ️  Migration {i} skipped - column already exists")
            else:
                print(f"   ❌ Migration {i} failed: {str(e)}")
                raise
    
    print("💾 All migrations completed!")

def migrate_legacy_data(engine, environment):
    """Migrate existing location data to smart location system"""
    
    print(f"\n🔄 Migrating legacy location data in {environment} database...")
    
    try:
        with engine.connect() as connection:
            # Get contests with legacy location data but no smart location data
            if "sqlite" in str(engine.url):
                result = connection.execute(text("""
                    SELECT id, location, latitude, longitude 
                    FROM contests 
                    WHERE location IS NOT NULL 
                    AND (location_type IS NULL OR location_type = 'united_states')
                    LIMIT 100;
                """))
            else:
                result = connection.execute(text("""
                    SELECT id, location, latitude, longitude 
                    FROM contests 
                    WHERE location IS NOT NULL 
                    AND (location_type IS NULL OR location_type = 'united_states')
                    LIMIT 100;
                """))
            
            contests_to_migrate = list(result)
            
            if not contests_to_migrate:
                print("   ℹ️  No legacy location data to migrate")
                return
            
            print(f"   📊 Found {len(contests_to_migrate)} contests with legacy location data")
            
            # Migrate each contest
            migrated_count = 0
            for contest_id, location, lat, lng in contests_to_migrate:
                try:
                    # Simple migration logic - detect if location contains state names
                    location_type = "united_states"  # Default
                    selected_states = None
                    
                    if location:
                        location_upper = location.upper()
                        
                        # Common state patterns
                        state_patterns = {
                            "CALIFORNIA": ["CA"], "CA": ["CA"],
                            "NEW YORK": ["NY"], "NY": ["NY"],
                            "TEXAS": ["TX"], "TX": ["TX"],
                            "FLORIDA": ["FL"], "FL": ["FL"],
                            "ILLINOIS": ["IL"], "IL": ["IL"],
                        }
                        
                        for pattern, states in state_patterns.items():
                            if pattern in location_upper:
                                location_type = "specific_states"
                                selected_states = states
                                break
                    
                    # Update the contest with smart location data
                    if selected_states:
                        if "sqlite" in str(engine.url):
                            connection.execute(text("""
                                UPDATE contests 
                                SET location_type = :location_type,
                                    selected_states = :selected_states
                                WHERE id = :contest_id
                            """), {
                                "location_type": location_type,
                                "selected_states": str(selected_states),  # Store as string in SQLite
                                "contest_id": contest_id
                            })
                        else:
                            connection.execute(text("""
                                UPDATE contests 
                                SET location_type = :location_type,
                                    selected_states = :selected_states
                                WHERE id = :contest_id
                            """), {
                                "location_type": location_type,
                                "selected_states": selected_states,
                                "contest_id": contest_id
                            })
                    else:
                        connection.execute(text("""
                            UPDATE contests 
                            SET location_type = :location_type
                            WHERE id = :contest_id
                        """), {
                            "location_type": location_type,
                            "contest_id": contest_id
                        })
                    
                    migrated_count += 1
                    
                except Exception as e:
                    print(f"   ⚠️  Failed to migrate contest {contest_id}: {str(e)}")
                    continue
            
            # Commit all changes
            connection.commit()
            print(f"   ✅ Successfully migrated {migrated_count} contests")
            
    except Exception as e:
        print(f"   ❌ Legacy data migration failed: {str(e)}")
        # Don't raise - migration can continue without legacy data migration

def verify_migration(engine, environment):
    """Verify that the migration was successful"""
    
    print(f"\n🔍 Verifying smart location migration in {environment} database...")
    
    expected_columns = [
        'location_type', 'selected_states', 'radius_address', 
        'radius_miles', 'radius_latitude', 'radius_longitude'
    ]
    
    try:
        with engine.connect() as connection:
            if "sqlite" in str(engine.url):
                # SQLite verification
                result = connection.execute(text("PRAGMA table_info(contests);"))
                columns = [row[1] for row in result]  # Column names are in index 1
            else:
                # PostgreSQL verification
                result = connection.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'contests' 
                    AND column_name IN ('location_type', 'selected_states', 'radius_address', 
                                       'radius_miles', 'radius_latitude', 'radius_longitude');
                """))
                columns = [row[0] for row in result]
            
            # Check for our new fields
            missing_columns = []
            for col in expected_columns:
                if col in columns:
                    print(f"   ✅ {col}: Present")
                else:
                    print(f"   ❌ {col}: Missing")
                    missing_columns.append(col)
            
            # Check data migration
            result = connection.execute(text("""
                SELECT COUNT(*) as total,
                       COUNT(CASE WHEN location_type = 'united_states' THEN 1 END) as us_contests,
                       COUNT(CASE WHEN location_type = 'specific_states' THEN 1 END) as state_contests
                FROM contests;
            """))
            
            row = result.fetchone()
            if row:
                total, us_contests, state_contests = row
                print(f"   📊 Contest location types:")
                print(f"      Total contests: {total}")
                print(f"      United States: {us_contests}")
                print(f"      State-specific: {state_contests}")
            
            return len(missing_columns) == 0
            
    except Exception as e:
        print(f"   ❌ Verification failed: {str(e)}")
        return False

def main():
    """Main migration function"""
    
    # Get environment from command line argument
    environment = sys.argv[1] if len(sys.argv) > 1 else "development"
    
    if environment not in ["development", "staging", "production"]:
        print(f"❌ Invalid environment: {environment}")
        print("   Valid options: development, staging, production")
        sys.exit(1)
    
    print("🚀 Smart Location System Migration")
    print("=" * 50)
    print(f"🌍 Environment: {environment}")
    
    # Get database URL
    try:
        db_url = get_database_url(environment)
    except ValueError as e:
        print(f"❌ {str(e)}")
        sys.exit(1)
    
    # Hide password in logs
    if "postgresql" in db_url:
        parsed = urlparse(db_url)
        safe_url = f"{parsed.scheme}://{parsed.username}:***@{parsed.hostname}:{parsed.port}{parsed.path}"
        print(f"🔗 Connecting to: {safe_url}")
    else:
        print(f"🔗 Connecting to: {db_url}")
    
    try:
        # Create engine
        engine = create_engine(db_url)
        
        # Test connection
        with engine.connect() as connection:
            if "sqlite" in str(engine.url):
                result = connection.execute(text("SELECT sqlite_version();"))
                version = result.scalar()
                print(f"✅ Connected to SQLite: {version}")
            else:
                result = connection.execute(text("SELECT version();"))
                version = result.scalar()
                print(f"✅ Connected to PostgreSQL: {version}")
        
        # Run migrations
        add_smart_location_fields(engine, environment)
        
        # Migrate legacy data
        migrate_legacy_data(engine, environment)
        
        # Verify migration
        success = verify_migration(engine, environment)
        
        print(f"\n🎉 Smart location migration completed for {environment}!")
        if success:
            print("   ✅ All smart location fields are now available")
            print("   🎯 Contest location targeting system is ready")
            print("   📍 Legacy location data has been preserved")
        else:
            print("   ⚠️  Some fields may not have been added correctly")
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
