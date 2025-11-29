#!/usr/bin/env python3
"""
Test script to verify the complete traffic flow architecture:
1. Attack Simulator → Load Balancer (8090)
2. Load Balancer → Aurora Shield auth check
3. Load Balancer → Protected App (if authorized)
4. Dashboard statistics update properly
"""

import requests
import time
import json

def test_dashboard_access():
    """Test direct dashboard access"""
    print("🔍 Testing Dashboard Access...")
    try:
        response = requests.get('http://localhost:8080', timeout=5)
        print(f"   Dashboard Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Dashboard accessible")
        else:
            print("   ❌ Dashboard not accessible")
        return response.status_code == 200
    except Exception as e:
        print(f"   ❌ Dashboard error: {e}")
        return False

def test_load_balancer_access():
    """Test load balancer access to protected app"""
    print("\n🔍 Testing Load Balancer → Protected App...")
    try:
        response = requests.get('http://localhost:8090/', timeout=5)
        print(f"   Load Balancer Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Load balancer routing to protected app")
        else:
            print("   ❌ Load balancer routing failed")
        return response.status_code == 200
    except Exception as e:
        print(f"   ❌ Load balancer error: {e}")
        return False

def get_initial_stats():
    """Get initial statistics from dashboard"""
    print("\n📊 Getting Initial Statistics...")
    try:
        response = requests.get('http://localhost:8080/api/dashboard/stats', timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print(f"   Total Requests: {stats.get('total_requests', 0)}")
            print(f"   Blocked Requests: {stats.get('blocked_requests', 0)}")
            return stats
        elif response.status_code == 401:
            print("   ⚠️ Authentication required for stats")
            return {}
        else:
            print("   ❌ Failed to get stats")
            return None
    except Exception as e:
        print(f"   ❌ Stats error: {e}")
        return None

def send_test_requests():
    """Send test requests through load balancer"""
    print("\n🚀 Sending Test Requests through Load Balancer...")
    
    # Send 5 normal requests
    for i in range(5):
        try:
            response = requests.get('http://localhost:8090/', timeout=5)
            print(f"   Request {i+1}: Status {response.status_code}")
            time.sleep(0.5)
        except Exception as e:
            print(f"   Request {i+1}: Error {e}")

def get_updated_stats():
    """Get updated statistics from dashboard"""
    print("\n📊 Getting Updated Statistics...")
    try:
        response = requests.get('http://localhost:8080/api/dashboard/stats', timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print(f"   Total Requests: {stats.get('total_requests', 0)}")
            print(f"   Blocked Requests: {stats.get('blocked_requests', 0)}")
            return stats
        elif response.status_code == 401:
            print("   ⚠️ Authentication required for stats")
            return {}
        else:
            print("   ❌ Failed to get updated stats")
            return None
    except Exception as e:
        print(f"   ❌ Updated stats error: {e}")
        return None

def test_auth_endpoint():
    """Test the auth endpoint directly"""
    print("\n🔒 Testing Auth Endpoint...")
    try:
        # Test with normal request headers
        headers = {
            'X-Forwarded-For': '192.168.1.100',
            'User-Agent': 'TestAgent/1.0'
        }
        response = requests.get('http://localhost:8080/api/shield/check-request', 
                              headers=headers, timeout=5)
        print(f"   Auth Check Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Request authorized")
        elif response.status_code == 403:
            print("   🛡️ Request blocked")
        else:
            print(f"   ❓ Unexpected status: {response.status_code}")
        return True
    except Exception as e:
        print(f"   ❌ Auth endpoint error: {e}")
        return False

def main():
    print("� Aurora Shield Traffic Flow Test")
    print("=" * 50)
    
    # Step 1: Test dashboard access
    dashboard_ok = test_dashboard_access()
    
    # Step 2: Test load balancer
    lb_ok = test_load_balancer_access()
    
    # Step 3: Test auth endpoint
    auth_ok = test_auth_endpoint()
    
    if not all([dashboard_ok, auth_ok]):
        print("\n❌ Basic connectivity issues detected. Stopping test.")
        return
    
    # Step 4: Get initial stats
    initial_stats = get_initial_stats()
    
    # Step 5: Send test requests
    send_test_requests()
    
    # Wait a moment for processing
    time.sleep(2)
    
    # Step 6: Get updated stats
    updated_stats = get_updated_stats()
    
    # Step 7: Analyze results
    print("\n📈 Results Analysis...")
    if initial_stats and updated_stats:
        initial_total = initial_stats.get('total_requests', 0)
        updated_total = updated_stats.get('total_requests', 0)
        requests_processed = updated_total - initial_total
        
        print(f"   Requests processed: {requests_processed}")
        if requests_processed > 0:
            print("   ✅ Statistics are updating correctly!")
        else:
            print("   ❌ Statistics not updating - traffic may not be flowing through auth endpoint")
    
    print("\n🏁 Test Complete!")
    print("=" * 50)

if __name__ == "__main__":
    main()