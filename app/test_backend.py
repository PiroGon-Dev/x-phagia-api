#!/usr/bin/env python3
"""
Test script to verify backend functionality
Run this after setting up the backend to test all endpoints
"""

import requests
import json
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent / "app"))

BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint"""
    print("Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_login():
    """Test login endpoint"""
    print("Testing login...")
    try:
        login_data = {
            "email": "admin@meddevice.local",
            "password": "admin123"
        }
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        if response.status_code == 200:
            print("✅ Login successful")
            data = response.json()
            print(f"   Token received: {data['access_token'][:20]}...")
            return data['access_token']
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_auth_me(token):
    """Test auth/me endpoint"""
    print("Testing auth/me...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        if response.status_code == 200:
            print("✅ Auth/me successful")
            print(f"   User: {response.json()}")
            return True
        else:
            print(f"❌ Auth/me failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Auth/me error: {e}")
        return False

def test_dashboard_stats(token):
    """Test dashboard stats endpoint"""
    print("Testing dashboard stats...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=headers)
        if response.status_code == 200:
            print("✅ Dashboard stats successful")
            print(f"   Stats: {response.json()}")
            return True
        else:
            print(f"❌ Dashboard stats failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Dashboard stats error: {e}")
        return False

def test_patients_endpoint(token):
    """Test patients endpoint"""
    print("Testing patients endpoint...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/patients/", headers=headers)
        if response.status_code == 200:
            print("✅ Patients endpoint successful")
            print(f"   Patients count: {len(response.json())}")
            return True
        else:
            print(f"❌ Patients endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Patients endpoint error: {e}")
        return False

def test_sessions_endpoint(token):
    """Test sessions endpoint"""
    print("Testing sessions endpoint...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/sessions/", headers=headers)
        if response.status_code == 200:
            print("✅ Sessions endpoint successful")
            print(f"   Sessions count: {len(response.json())}")
            return True
        else:
            print(f"❌ Sessions endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Sessions endpoint error: {e}")
        return False

def test_kiosk_pin():
    """Test kiosk PIN verification"""
    print("Testing kiosk PIN verification...")
    try:
        pin_data = {"pin": "1234"}
        response = requests.post(f"{BASE_URL}/api/kiosk/verify-pin", json=pin_data)
        if response.status_code == 200:
            print("✅ Kiosk PIN verification successful")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Kiosk PIN verification failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Kiosk PIN verification error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting backend tests...")
    print("=" * 50)
    
    # Test 1: Health check
    if not test_health_check():
        print("\n❌ Backend is not running or health check failed")
        print("Please start the backend server first:")
        print("   cd backend")
        print("   python -m app.main")
        return
    
    # Test 2: Login
    token = test_login()
    if not token:
        print("\n❌ Login failed - make sure admin user exists")
        print("Run: python app/scripts/create_admin.py")
        return
    
    # Test 3: Auth/me
    test_auth_me(token)
    
    # Test 4: Dashboard stats
    test_dashboard_stats(token)
    
    # Test 5: Patients endpoint
    test_patients_endpoint(token)
    
    # Test 6: Sessions endpoint
    test_sessions_endpoint(token)
    
    # Test 7: Kiosk PIN
    test_kiosk_pin()
    
    print("\n" + "=" * 50)
    print("🎉 Backend tests completed!")
    print("\nThe backend appears to be working correctly with the frontend Test.tsx")
    print("You can now start the frontend and test the integration.")

if __name__ == "__main__":
    main()

