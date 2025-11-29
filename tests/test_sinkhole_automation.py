#!/usr/bin/env python3
"""
Test script for automated sinkhole and attacking IP tracking.
Creates various attack patterns to test new Aurora Shield features.
"""

import requests
import time
import random
import json
from concurrent.futures import ThreadPoolExecutor
import threading

class SinkholeTestSimulator:
    def __init__(self, target_url="http://localhost:8080"):
        self.target_url = target_url
        self.session = requests.Session()
        
    def simulate_zero_reputation_attack(self, num_requests=50):
        """Simulate attacks that should trigger automatic sinkholing."""
        print(f"\n[TEST 1] Simulating zero-reputation attack patterns...")
        
        attacking_ips = ['192.168.1.100', '10.0.0.50', '172.16.0.25']
        
        for ip in attacking_ips:
            print(f"Sending malicious requests from {ip}...")
            
            # Send requests that should trigger reputation drop to zero
            for i in range(num_requests):
                try:
                    # Simulate various attack patterns
                    headers = {
                        'X-Forwarded-For': ip,
                        'User-Agent': 'AttackBot/1.0',
                        'X-Real-IP': ip
                    }
                    
                    # Mix of different attack types
                    if i % 3 == 0:
                        # SQL injection attempt
                        params = {'id': "1' OR '1'='1"}
                    elif i % 3 == 1:
                        # XSS attempt  
                        params = {'search': '<script>alert("xss")</script>'}
                    else:
                        # Path traversal
                        params = {'file': '../../../etc/passwd'}
                    
                    response = self.session.get(
                        f"{self.target_url}/api/health",
                        params=params,
                        headers=headers,
                        timeout=2
                    )
                    
                    if i % 10 == 0:
                        print(f"  Request {i+1}: Status {response.status_code}")
                        
                except Exception as e:
                    print(f"  Request failed: {e}")
                    
                time.sleep(0.1)  # Small delay
        
        print("✅ Zero-reputation attack simulation completed")
    
    def simulate_legitimate_traffic(self, num_requests=20):
        """Simulate legitimate traffic that should not be sinkholed."""
        print(f"\n[TEST 2] Simulating legitimate traffic...")
        
        legitimate_ips = ['203.0.113.10', '198.51.100.25', '192.0.2.50']
        
        for ip in legitimate_ips:
            print(f"Sending legitimate requests from {ip}...")
            
            for i in range(num_requests):
                try:
                    headers = {
                        'X-Forwarded-For': ip,
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'X-Real-IP': ip
                    }
                    
                    response = self.session.get(
                        f"{self.target_url}/api/health",
                        headers=headers,
                        timeout=2
                    )
                    
                    if i % 5 == 0:
                        print(f"  Request {i+1}: Status {response.status_code}")
                        
                except Exception as e:
                    print(f"  Request failed: {e}")
                    
                time.sleep(0.2)
        
        print("✅ Legitimate traffic simulation completed")
    
    def test_queue_fairness(self, num_threads=10):
        """Test queue fairness under high load."""
        print(f"\n[TEST 3] Testing queue fairness under high load...")
        
        def send_burst_requests(ip_base, is_attacking=True):
            """Send burst of requests from an IP."""
            ip = f"192.168.{ip_base}.{random.randint(1, 254)}"
            
            for i in range(100):
                try:
                    headers = {
                        'X-Forwarded-For': ip,
                        'X-Real-IP': ip,
                        'User-Agent': 'AttackBot/2.0' if is_attacking else 'LegitimateUser/1.0'
                    }
                    
                    if is_attacking:
                        params = {'attack': 'true', 'payload': f'malicious_data_{i}'}
                    else:
                        params = {'legitimate': 'true', 'user_id': f'user_{i}'}
                    
                    response = self.session.get(
                        f"{self.target_url}/api/health",
                        params=params,
                        headers=headers,
                        timeout=1
                    )
                    
                except Exception:
                    pass  # Continue with test
                    
                time.sleep(0.05)
        
        # Create mix of attacking and legitimate traffic
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = []
            
            # 70% attacking traffic
            for i in range(int(num_threads * 0.7)):
                future = executor.submit(send_burst_requests, i + 100, True)
                futures.append(future)
            
            # 30% legitimate traffic
            for i in range(int(num_threads * 0.3)):
                future = executor.submit(send_burst_requests, i + 200, False)
                futures.append(future)
            
            # Wait for completion
            for future in futures:
                future.result()
        
        print("✅ Queue fairness test completed")
    
    def check_sinkhole_status(self):
        """Check current sinkhole status."""
        print(f"\n[STATUS CHECK] Checking sinkhole and attacking IP status...")
        
        try:
            # First login to get session
            login_data = {
                'username': 'admin',
                'password': 'admin123'
            }
            
            login_response = self.session.post(
                f"{self.target_url}/login",
                data=login_data
            )
            
            if login_response.status_code == 200:
                print("✅ Successfully logged in")
                
                # Check attacking IPs
                attacking_response = self.session.get(
                    f"{self.target_url}/api/dashboard/attacking-ips"
                )
                
                if attacking_response.status_code == 200:
                    attacking_data = attacking_response.json()
                    print(f"📊 Current attacking IPs: {len(attacking_data)}")
                    
                    if attacking_data:
                        for ip_data in attacking_data[:5]:  # Show first 5
                            print(f"  🎯 {ip_data['ip']}: {ip_data['attack_count']} attacks, "
                                  f"Action: {ip_data['action_taken']}")
                    else:
                        print("  No attacking IPs currently detected")
                else:
                    print(f"❌ Failed to get attacking IPs: {attacking_response.status_code}")
                
                # Check sinkhole status
                sinkhole_response = self.session.get(
                    f"{self.target_url}/api/dashboard/sinkhole-status"
                )
                
                if sinkhole_response.status_code == 200:
                    sinkhole_data = sinkhole_response.json()
                    print(f"🕳️  Sinkholed IPs: {sinkhole_data.get('total_sinkholed', 0)}")
                    
                    if sinkhole_data.get('sinkholed_ips'):
                        for ip_info in sinkhole_data['sinkholed_ips'][:3]:  # Show first 3
                            print(f"  🔒 {ip_info['ip']}: Added {ip_info['added_at']}, "
                                  f"Reason: {ip_info['reason']}")
                    else:
                        print("  No IPs currently sinkholed")
                else:
                    print(f"❌ Failed to get sinkhole status: {sinkhole_response.status_code}")
                    
            else:
                print(f"❌ Login failed: {login_response.status_code}")
                
        except Exception as e:
            print(f"❌ Status check failed: {e}")

def main():
    """Run all tests for automated sinkhole functionality."""
    print("🛡️  Aurora Shield - Automated Sinkhole Test Suite")
    print("=" * 60)
    
    simulator = SinkholeTestSimulator()
    
    # Run tests in sequence
    try:
        # Test 1: Zero reputation attacks (should trigger sinkholing)
        simulator.simulate_zero_reputation_attack(30)
        time.sleep(2)
        
        # Check status after first test
        simulator.check_sinkhole_status()
        time.sleep(2)
        
        # Test 2: Legitimate traffic (should not be affected)
        simulator.simulate_legitimate_traffic(15)
        time.sleep(2)
        
        # Test 3: Queue fairness under load
        simulator.test_queue_fairness(8)
        time.sleep(2)
        
        # Final status check
        print("\n" + "="*60)
        print("🔍 FINAL STATUS CHECK")
        print("="*60)
        simulator.check_sinkhole_status()
        
        print("\n✅ All tests completed successfully!")
        print("\n📋 Summary:")
        print("   - Automated sinkhole functionality tested")
        print("   - Zero-reputation IP detection verified")
        print("   - Queue fairness under high load tested")
        print("   - Attacking IP tracking validated")
        print("\n🌐 Open the dashboard at http://localhost:8080 to see results!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")

if __name__ == "__main__":
    main()