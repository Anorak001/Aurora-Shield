#!/usr/bin/env python3
"""
Test script for Aurora Shield Configuration GUI functionality.
"""

import requests
import json
import time

class ConfigGUITester:
    def __init__(self):
        self.base_url = "http://localhost:8080"
        self.session = requests.Session()
        
    def authenticate(self):
        """Authenticate with the dashboard."""
        login_data = {'username': 'admin', 'password': 'admin123'}
        response = self.session.post(f"{self.base_url}/login", data=login_data)
        return response.status_code == 200
    
    def test_get_config(self):
        """Test getting current configuration."""
        print("🔧 Testing GET /api/dashboard/config...")
        
        response = self.session.get(f"{self.base_url}/api/dashboard/config")
        if response.status_code == 200:
            config = response.json()
            print("✅ Configuration retrieved successfully")
            print(f"   Version: {config.get('version', 'Unknown')}")
            print(f"   Rate Limiter Rate: {config.get('rate_limiter', {}).get('rate', 'Unknown')}")
            print(f"   Anomaly Threshold: {config.get('anomaly_detector', {}).get('rate_threshold', 'Unknown')}")
            print(f"   IP Initial Score: {config.get('ip_reputation', {}).get('initial_score', 'Unknown')}")
            return config
        else:
            print(f"❌ Failed to get config: {response.status_code} - {response.text}")
            return None
    
    def test_update_config(self):
        """Test updating configuration."""
        print("\n🔧 Testing POST /api/dashboard/config...")
        
        # Test configuration with new values
        test_config = {
            'rate_limiter': {
                'enabled': True,
                'rate': 15,
                'burst': 25,
                'window_size': 90
            },
            'anomaly_detector': {
                'enabled': True,
                'request_window': 120,
                'rate_threshold': 150,
                'sensitivity': 'high'
            },
            'ip_reputation': {
                'enabled': True,
                'initial_score': 90,
                'reputation_threshold': 60,
                'decay_rate': 0.15
            },
            'thresholds': {
                'requests_per_second': 1500,
                'cpu_threshold': 85,
                'memory_threshold': 90
            }
        }
        
        response = self.session.post(
            f"{self.base_url}/api/dashboard/config",
            json=test_config,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Configuration updated successfully")
            print(f"   Message: {result.get('message', 'No message')}")
            return True
        else:
            print(f"❌ Failed to update config: {response.status_code} - {response.text}")
            return False
    
    def test_config_validation(self):
        """Test configuration validation with invalid values."""
        print("\n🔧 Testing configuration validation...")
        
        # Test with invalid values
        invalid_config = {
            'rate_limiter': {
                'rate': -5,  # Invalid: negative value
                'burst': 50000  # Invalid: too high
            },
            'anomaly_detector': {
                'sensitivity': 'invalid_value'  # Invalid: not in choices
            },
            'thresholds': {
                'cpu_threshold': 150  # Invalid: over 100%
            }
        }
        
        response = self.session.post(
            f"{self.base_url}/api/dashboard/config",
            json=invalid_config,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 400:
            print("✅ Configuration validation working correctly")
            print(f"   Error: {response.json().get('error', 'No error message')}")
            return True
        else:
            print(f"❌ Validation should have failed but got: {response.status_code}")
            return False
    
    def test_config_persistence(self):
        """Test that configuration changes persist."""
        print("\n🔧 Testing configuration persistence...")
        
        # Set a unique value
        test_value = int(time.time()) % 1000  # Use timestamp for uniqueness
        config_update = {
            'rate_limiter': {
                'rate': test_value
            }
        }
        
        # Update config
        update_response = self.session.post(
            f"{self.base_url}/api/dashboard/config",
            json=config_update,
            headers={'Content-Type': 'application/json'}
        )
        
        if update_response.status_code != 200:
            print(f"❌ Failed to update config for persistence test")
            return False
        
        # Wait a moment
        time.sleep(2)
        
        # Retrieve config and check if value persisted
        get_response = self.session.get(f"{self.base_url}/api/dashboard/config")
        if get_response.status_code == 200:
            config = get_response.json()
            retrieved_value = config.get('rate_limiter', {}).get('rate')
            
            if retrieved_value == test_value:
                print("✅ Configuration persistence working correctly")
                print(f"   Set value: {test_value}, Retrieved value: {retrieved_value}")
                return True
            else:
                print(f"❌ Configuration not persistent. Set: {test_value}, Got: {retrieved_value}")
                return False
        else:
            print(f"❌ Failed to retrieve config for persistence test")
            return False

def main():
    """Run comprehensive configuration GUI tests."""
    print("🛡️  Aurora Shield Configuration GUI Test Suite")
    print("=" * 60)
    
    tester = ConfigGUITester()
    
    # Authenticate
    if not tester.authenticate():
        print("❌ Authentication failed")
        return
    
    print("✅ Authentication successful")
    
    # Run tests
    tests = [
        ('Configuration Retrieval', tester.test_get_config),
        ('Configuration Update', tester.test_update_config),
        ('Configuration Validation', tester.test_config_validation),
        ('Configuration Persistence', tester.test_config_persistence)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📊 Results: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Configuration GUI is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the issues above.")
    
    print(f"\n🌐 Access the Configuration GUI at: {tester.base_url}")
    print("🔐 Login: admin / admin123")
    print("📍 Navigate to: Configuration tab")

if __name__ == "__main__":
    main()