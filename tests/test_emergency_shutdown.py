#!/usr/bin/env python3
"""
Test script for Emergency Shutdown API
Tests the new Docker shutdown functionality
"""
import requests
import json

def test_emergency_shutdown():
    """Test the emergency shutdown API endpoint"""
    
    # First, try to login to get a session
    login_url = "http://localhost:8080/login"
    dashboard_url = "http://localhost:8080/api/emergency/shutdown"
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    try:
        # Login first
        print("🔐 Attempting to log in...")
        login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        
        login_response = session.post(login_url, data=login_data)
        print(f"Login status: {login_response.status_code}")
        
        if login_response.status_code not in [200, 302]:
            print("❌ Login failed")
            return
            
        print("✅ Login successful")
        
        # Test emergency shutdown
        print("\n🚨 Testing Emergency Shutdown API...")
        
        shutdown_data = {
            'reason': 'Testing emergency shutdown functionality from script'
        }
        
        response = session.post(dashboard_url, 
                               json=shutdown_data,
                               headers={'Content-Type': 'application/json'})
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        try:
            result = response.json()
            print(f"\n📋 Response Data:")
            print(json.dumps(result, indent=2))
            
            if result.get('success'):
                print(f"\n✅ Emergency shutdown successful!")
                print(f"Containers stopped: {result.get('containers_stopped', 0)}")
                print(f"Containers failed: {result.get('containers_failed', 0)}")
                
                if 'results' in result:
                    print(f"\n📊 Container shutdown details:")
                    for container in result['results']:
                        status_icon = "✅" if container['status'] == 'stopped' else "❌"
                        print(f"{status_icon} {container['name']} ({container['id']}) - {container['status']}")
                        if container.get('error'):
                            print(f"   Error: {container['error']}")
                            
            else:
                print(f"❌ Emergency shutdown failed: {result.get('error', 'Unknown error')}")
                
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Aurora Shield dashboard. Is it running?")
        print("   Run: docker-compose up -d")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    print("🔥 Aurora Shield Emergency Shutdown Test")
    print("="*50)
    test_emergency_shutdown()