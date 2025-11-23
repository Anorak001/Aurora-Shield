#!/usr/bin/env python3
"""
Test script for Logs Export API
Tests the new attack logs export functionality
"""
import requests
import json

def test_logs_export():
    """Test the logs export API endpoint"""
    
    # First, try to login to get a session
    login_url = "http://localhost:8080/login"
    export_url = "http://localhost:8080/api/export/logs"
    
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
        
        # Test logs export
        print("\n📋 Testing Logs Export API...")
        
        response = session.get(export_url)
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            # Check if it's JSON content
            content_type = response.headers.get('content-type', '')
            if 'application/json' in content_type:
                # Parse the JSON to validate structure
                try:
                    log_data = response.json()
                    print(f"\n✅ Logs export successful!")
                    print(f"📊 Export Summary:")
                    
                    if 'export_info' in log_data:
                        export_info = log_data['export_info']
                        print(f"   Generated at: {export_info.get('generated_at', 'N/A')}")
                        print(f"   Exported by: {export_info.get('exported_by', 'N/A')}")
                        print(f"   System uptime: {export_info.get('uptime', 'N/A')}")
                    
                    if 'attack_logs' in log_data:
                        attack_count = len(log_data['attack_logs'])
                        print(f"   Attack logs: {attack_count} entries")
                        
                        if attack_count > 0:
                            print(f"   Sample attack log:")
                            sample = log_data['attack_logs'][0]
                            print(f"     - IP: {sample.get('ip', 'N/A')}")
                            print(f"     - Status: {sample.get('status', 'N/A')}")
                            print(f"     - Timestamp: {sample.get('timestamp', 'N/A')}")
                    
                    if 'blocked_requests' in log_data:
                        blocked_info = log_data['blocked_requests']
                        print(f"   Blocked requests: {blocked_info.get('total_blocked', 0)}")
                        print(f"   Block rate: {blocked_info.get('block_rate', 'N/A')}")
                    
                    if 'reputation_scores' in log_data:
                        ip_count = len(log_data['reputation_scores'])
                        print(f"   IP reputation scores: {ip_count} IPs tracked")
                    
                    if 'mitigation_actions' in log_data:
                        mitigation_count = len(log_data['mitigation_actions'])
                        print(f"   Mitigation actions: {mitigation_count} active")
                    
                    # Show file size
                    content_length = len(response.content)
                    print(f"   Export file size: {content_length:,} bytes")
                    
                    # Save sample file for verification
                    with open('sample_export.json', 'w', encoding='utf-8') as f:
                        json.dump(log_data, f, indent=2, ensure_ascii=False)
                    print(f"   📁 Sample saved as: sample_export.json")
                    
                except json.JSONDecodeError as e:
                    print(f"❌ Invalid JSON response: {e}")
                    print(f"Raw content (first 500 chars): {response.text[:500]}")
            else:
                print(f"❌ Unexpected content type: {content_type}")
                
        else:
            try:
                error_data = response.json()
                print(f"❌ Export failed: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"❌ Export failed with status {response.status_code}: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Aurora Shield dashboard. Is it running?")
        print("   Run: docker-compose up -d aurora-shield")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    print("📋 Aurora Shield Logs Export Test")
    print("="*50)
    test_logs_export()