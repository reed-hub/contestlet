#!/usr/bin/env python3
"""
Create test data for the staging environment
"""
import requests
import json
from datetime import datetime, timedelta
import random

# Staging environment URL (latest deployment)
STAGING_URL = "https://contestlet-kgdl5hv56-matthew-reeds-projects-89c602d6.vercel.app"

def get_admin_token():
    """Get admin token via OTP flow using mock code"""
    print("🔐 Getting admin token...")
    
    # Request OTP for admin phone
    admin_phone = "+18187958204"  # Test phone
    
    response = requests.post(f"{STAGING_URL}/auth/request-otp", json={
        "phone": admin_phone
    })
    
    if response.status_code != 200:
        print(f"❌ Failed to request OTP: {response.text}")
        return None
    
    print(f"📱 OTP requested for {admin_phone}")
    
    # Use mock OTP code automatically 
    otp_code = "123456"  # Mock code for staging
    print(f"🔧 Using mock OTP code: {otp_code}")
    
    # Verify OTP
    response = requests.post(f"{STAGING_URL}/auth/verify-otp", json={
        "phone": admin_phone,
        "code": otp_code
    })
    
    if response.status_code != 200:
        print(f"❌ Failed to verify OTP: {response.text}")
        return None
    
    token = response.json().get("access_token")
    print("✅ Admin token obtained!")
    return token

def create_contest(token, contest_data):
    """Create a contest via API"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(f"{STAGING_URL}/admin/contests", 
                           json=contest_data, headers=headers)
    
    if response.status_code == 201:
        contest = response.json()
        print(f"✅ Created contest: {contest['name']} (ID: {contest['id']})")
        return contest
    else:
        print(f"❌ Failed to create contest: {response.text}")
        return None

def create_test_users_and_entries(contest_id):
    """Create test users and entries for a contest"""
    test_phones = [
        "+15551234567",
        "+15551234568", 
        "+15551234569",
        "+15551234570",
        "+15551234571"
    ]
    
    print(f"👥 Creating test entries for contest {contest_id}...")
    
    for i, phone in enumerate(test_phones):
        try:
            # Request OTP
            response = requests.post(f"{STAGING_URL}/auth/request-otp", json={
                "phone": phone
            })
            
            if response.status_code != 200:
                print(f"⚠️ Failed to request OTP for {phone}")
                continue
            
            # Use mock OTP code
            response = requests.post(f"{STAGING_URL}/auth/verify-otp", json={
                "phone": phone,
                "code": "123456"  # Mock code
            })
            
            if response.status_code != 200:
                print(f"⚠️ Failed to verify OTP for {phone}")
                continue
            
            user_token = response.json().get("access_token")
            
            # Enter contest
            headers = {"Authorization": f"Bearer {user_token}"}
            response = requests.post(f"{STAGING_URL}/contests/{contest_id}/enter", 
                                   headers=headers)
            
            if response.status_code == 201:
                print(f"✅ User {phone} entered contest {contest_id}")
            else:
                print(f"⚠️ Failed to enter contest for {phone}: {response.text}")
                
        except Exception as e:
            print(f"⚠️ Error creating entry for {phone}: {e}")

def main():
    print("🚀 Creating test data for STAGING environment")
    print(f"📍 Staging URL: {STAGING_URL}")
    print()
    
    # Get admin token
    token = get_admin_token()
    if not token:
        print("❌ Could not get admin token. Exiting.")
        return
    
    # Test data contests
    now = datetime.utcnow()
    
    contests = [
        {
            "name": "🏖️ Summer Beach Vacation",
            "description": "Win a 7-day all-inclusive beach vacation to Hawaii! Includes flights, hotel, and activities.",
            "location": "Hawaii, USA",
            "latitude": 21.3099,
            "longitude": -157.8581,
            "start_time": (now - timedelta(days=1)).isoformat() + "Z",
            "end_time": (now + timedelta(days=7)).isoformat() + "Z",
            "prize_description": "$8000 Hawaii vacation package",
            "active": True,
            "official_rules": {
                "eligibility_text": "Open to US residents 18+ years old. Employees of sponsor and their families are not eligible.",
                "sponsor_name": "Contestlet Staging Test",
                "start_date": (now - timedelta(days=1)).isoformat() + "Z",
                "end_date": (now + timedelta(days=7)).isoformat() + "Z",
                "prize_value_usd": 8000,
                "terms_url": "https://example.com/terms"
            }
        },
        {
            "name": "📱 iPhone 16 Pro Giveaway",
            "description": "The latest iPhone 16 Pro with 256GB storage in your choice of color!",
            "location": "San Francisco, CA",
            "latitude": 37.7749,
            "longitude": -122.4194,
            "start_time": (now - timedelta(hours=12)).isoformat() + "Z",
            "end_time": (now + timedelta(days=5)).isoformat() + "Z",
            "prize_description": "iPhone 16 Pro 256GB",
            "active": True,
            "official_rules": {
                "eligibility_text": "Must be 18+ and a US resident. No purchase necessary. Void where prohibited.",
                "sponsor_name": "Tech Staging Giveaways",
                "start_date": (now - timedelta(hours=12)).isoformat() + "Z",
                "end_date": (now + timedelta(days=5)).isoformat() + "Z",
                "prize_value_usd": 1200,
                "terms_url": "https://example.com/iphone-terms"
            }
        },
        {
            "name": "🎮 Gaming Setup Contest",
            "description": "Complete gaming setup including PS5, 4K monitor, gaming chair, and $500 game credit!",
            "location": "Austin, TX",
            "latitude": 30.2672,
            "longitude": -97.7431,
            "start_time": now.isoformat() + "Z",
            "end_time": (now + timedelta(days=10)).isoformat() + "Z",
            "prize_description": "Ultimate gaming setup worth $2500",
            "active": True,
            "official_rules": {
                "eligibility_text": "Open to gamers 16+ in the US. Parent consent required for minors.",
                "sponsor_name": "Gaming World Staging",
                "start_date": now.isoformat() + "Z",
                "end_date": (now + timedelta(days=10)).isoformat() + "Z",
                "prize_value_usd": 2500,
                "terms_url": "https://example.com/gaming-terms"
            }
        },
        {
            "name": "💰 $1000 Cash Prize",
            "description": "Simple cash giveaway - $1000 directly to your bank account!",
            "location": "New York, NY",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "start_time": (now + timedelta(hours=2)).isoformat() + "Z",
            "end_time": (now + timedelta(days=3)).isoformat() + "Z",
            "prize_description": "$1000 cash prize",
            "active": True,
            "official_rules": {
                "eligibility_text": "US residents 21+ only. Tax responsibility of winner.",
                "sponsor_name": "Cash Contests Staging",
                "start_date": (now + timedelta(hours=2)).isoformat() + "Z",
                "end_date": (now + timedelta(days=3)).isoformat() + "Z",
                "prize_value_usd": 1000,
                "terms_url": "https://example.com/cash-terms"
            }
        },
        {
            "name": "🚗 Tesla Model Y Weekend",
            "description": "Win a weekend with a Tesla Model Y! 3 days of electric luxury driving.",
            "location": "Los Angeles, CA",
            "latitude": 34.0522,
            "longitude": -118.2437,
            "start_time": (now - timedelta(days=2)).isoformat() + "Z",
            "end_time": (now - timedelta(hours=1)).isoformat() + "Z",  # Ended contest
            "prize_description": "Tesla Model Y 3-day rental experience",
            "active": False,  # This one has ended
            "official_rules": {
                "eligibility_text": "Valid driver's license required. Must be 25+ with clean driving record.",
                "sponsor_name": "EV Experience Staging",
                "start_date": (now - timedelta(days=2)).isoformat() + "Z",
                "end_date": (now - timedelta(hours=1)).isoformat() + "Z",
                "prize_value_usd": 800,
                "terms_url": "https://example.com/tesla-terms"
            }
        }
    ]
    
    created_contests = []
    
    # Create all contests
    print("🎪 Creating test contests...")
    for contest_data in contests:
        contest = create_contest(token, contest_data)
        if contest:
            created_contests.append(contest)
    
    print(f"\n✅ Created {len(created_contests)} contests!")
    
    # Create entries for active contests
    print("\n👥 Creating test entries...")
    for contest in created_contests:
        if contest.get('active'):
            create_test_users_and_entries(contest['id'])
    
    print("\n🎉 Staging test data creation complete!")
    print(f"\n📊 Summary:")
    print(f"   • {len(created_contests)} contests created")
    print(f"   • {len([c for c in created_contests if c.get('active')])} active contests")
    print(f"   • {len([c for c in created_contests if not c.get('active')])} ended contests")
    print(f"   • ~25 test entries created")
    
    print(f"\n🌐 View staging API: {STAGING_URL}/docs")
    print(f"🔍 Test endpoints:")
    print(f"   • GET {STAGING_URL}/contests/active")
    print(f"   • GET {STAGING_URL}/admin/contests (with admin token)")

if __name__ == "__main__":
    main()
