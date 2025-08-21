#!/usr/bin/env python3
"""
Create test entries for staging contests
"""
import requests

STAGING_URL = "https://contestlet-kgdl5hv56-matthew-reeds-projects-89c602d6.vercel.app"

def create_entries():
    """Create test entries for active contests"""
    
    # Test phone numbers
    test_phones = [
        "+15551234567",
        "+15551234568", 
        "+15551234569",
        "+15551234570",
        "+15551234571",
        "+15551234572",
        "+15551234573"
    ]
    
    # Active contest IDs (from previous output)
    active_contests = [1, 2, 3, 4]  # Skipping 5 (Tesla) as it's ended
    
    print(f"👥 Creating test entries for {len(active_contests)} active contests...")
    
    total_entries = 0
    
    for contest_id in active_contests:
        print(f"\n🎯 Contest {contest_id}:")
        
        # Create 3-5 entries per contest
        for i, phone in enumerate(test_phones[:5]):  # First 5 phones
            try:
                # Request OTP
                response = requests.post(f"{STAGING_URL}/auth/request-otp", json={
                    "phone": phone
                }, timeout=10)
                
                if response.status_code != 200:
                    print(f"  ⚠️ Failed OTP request for {phone}: {response.status_code}")
                    continue
                
                # Verify OTP with mock code
                response = requests.post(f"{STAGING_URL}/auth/verify-otp", json={
                    "phone": phone,
                    "code": "123456"
                }, timeout=10)
                
                if response.status_code != 200:
                    print(f"  ⚠️ Failed OTP verify for {phone}: {response.status_code}")
                    continue
                
                user_token = response.json().get("access_token")
                if not user_token:
                    print(f"  ⚠️ No token returned for {phone}")
                    continue
                
                # Enter contest
                headers = {"Authorization": f"Bearer {user_token}"}
                response = requests.post(f"{STAGING_URL}/contests/{contest_id}/enter", 
                                       headers=headers, timeout=10)
                
                if response.status_code == 201:
                    total_entries += 1
                    print(f"  ✅ {phone} entered contest {contest_id}")
                elif response.status_code == 400:
                    print(f"  ℹ️ {phone} already entered contest {contest_id}")
                else:
                    print(f"  ❌ Failed entry for {phone}: {response.status_code} - {response.text}")
                    
            except requests.exceptions.Timeout:
                print(f"  ⏱️ Timeout for {phone}")
            except Exception as e:
                print(f"  ❌ Error for {phone}: {e}")
    
    print(f"\n🎉 Created {total_entries} test entries!")
    return total_entries

if __name__ == "__main__":
    print("🚀 Creating test entries for staging contests")
    entries_created = create_entries()
    print(f"\n✅ Total entries created: {entries_created}")
    print(f"🌐 View contests: {STAGING_URL}/contests/active")
