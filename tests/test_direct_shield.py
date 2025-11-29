#!/usr/bin/env python3
"""
Test Aurora Shield's automated sinkhole via the shield API endpoint.
"""

import requests
import time
import random
import json

class DirectShieldTest:
    def __init__(self):
        self.shield_url = "http://localhost:8080"
        self.session = requests.Session()
        
    def authenticate(self):
        """Authenticate with the dashboard."""
        login_data = {'username': 'admin', 'password': 'admin123'}
        response = self.session.post(f"{self.shield_url}/login", data=login_data)
        return response.status_code == 200
    
    def send_request_for_protection_check(self, source_ip, is_malicious=True, request_id=None):
        """Send a request to Aurora Shield for protection check."""
        
        # Prepare request data for shield processing
        request_data = {
            'ip': source_ip,
            'method': 'GET',
            'url': '/test-endpoint',
            'headers': {
                'User-Agent': 'AttackBot/1.0' if is_malicious else 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'X-Forwarded-For': source_ip,
                'X-Real-IP': source_ip
            },
            'timestamp': int(time.time())
        }
        
        if is_malicious:
            # Add malicious patterns
            attack_types = [
                {'params': {'id': "1' OR '1'='1"}, 'type': 'sql_injection'},
                {'params': {'search': '<script>alert("xss")</script>'}, 'type': 'xss'},
                {'params': {'file': '../../../etc/passwd'}, 'type': 'path_traversal'},
                {'params': {'cmd': 'rm -rf /'}, 'type': 'command_injection'}
            ]
            
            attack = random.choice(attack_types)
            request_data['params'] = attack['params']
            request_data['attack_type'] = attack['type']
        else:
            # Legitimate request
            request_data['params'] = {'page': 'home', 'user_id': f'user_{random.randint(1000, 9999)}'}
        
        try:
            response = self.session.post(
                f"{self.shield_url}/api/shield/check-request",
                json=request_data,
                timeout=5
            )
            
            return {
                'status_code': response.status_code,
                'response': response.json() if response.status_code == 200 else response.text,
                'source_ip': source_ip,
                'malicious': is_malicious
            }
        except Exception as e:
            return {
                'status_code': 0,
                'response': str(e),
                'source_ip': source_ip,
                'malicious': is_malicious
            }
    
    def simulate_zero_reputation_attacks(self):
        """Simulate multiple attacks from IPs to trigger zero reputation."""
        print("🎯 [TEST 1] Simulating zero-reputation attacks...")
        
        attack_ips = ['192.168.100.50', '10.0.0.100', '172.16.0.200']
        results = []
        
        for ip in attack_ips:
            print(f"\n  Attacking from {ip}...")
            
            # Send multiple malicious requests to trigger reputation drop
            for i in range(15):
                result = self.send_request_for_protection_check(ip, is_malicious=True, request_id=i)
                results.append(result)
                
                if i % 5 == 0:
                    print(f"    Request {i+1}: Status {result['status_code']}")
                    if result['status_code'] == 200:
                        response = result['response']
                        print(f"    Action: {response.get('action', 'unknown')}")
                        if 'sinkhole' in str(response).lower():
                            print(f"    🕳️  SINKHOLED!")
                
                time.sleep(0.1)
        
        return results
    
    def simulate_legitimate_traffic(self):
        """Simulate legitimate traffic."""
        print("\n✅ [TEST 2] Simulating legitimate traffic...")
        
        legit_ips = ['203.0.113.25', '198.51.100.50']
        results = []
        
        for ip in legit_ips:
            print(f"\n  Legitimate requests from {ip}...")
            
            for i in range(8):
                result = self.send_request_for_protection_check(ip, is_malicious=False, request_id=i)
                results.append(result)
                
                if i % 3 == 0:
                    print(f"    Request {i+1}: Status {result['status_code']}")
                    if result['status_code'] == 200:
                        response = result['response']
                        print(f"    Action: {response.get('action', 'unknown')}")
                
                time.sleep(0.2)
        
        return results
    
    def check_sinkhole_and_attacks(self):
        """Check current sinkhole status and attacking IPs."""
        if not self.authenticate():
            print("❌ Failed to authenticate")
            return
        
        print("\n🔍 Checking Aurora Shield Status...")
        
        try:
            # Check attacking IPs
            attacking_response = self.session.get(f"{self.shield_url}/api/dashboard/attacking-ips")
            if attacking_response.status_code == 200:
                data = attacking_response.json()
                attacking_data = data.get('data', {}) if isinstance(data, dict) else data
                
                print(f"\n📊 Attacking IP Analysis:")
                recent_attacks = attacking_data.get('recent_attacks', [])
                print(f"   Recent attacks: {len(recent_attacks)}")
                
                sinkhole_summary = attacking_data.get('sinkhole_summary', {})
                print(f"   Sinkholed IPs: {sinkhole_summary.get('sinkholed_ips', 0)}")
                print(f"   Quarantined IPs: {sinkhole_summary.get('quarantined_ips', 0)}")
                
                sinkholed_ips = attacking_data.get('sinkholed_ips', [])
                if sinkholed_ips:
                    print(f"\n🔒 Currently Sinkholed:")
                    for ip in sinkholed_ips:
                        print(f"     - {ip}")
            
            # Check general stats
            stats_response = self.session.get(f"{self.shield_url}/api/dashboard/stats")
            if stats_response.status_code == 200:
                stats = stats_response.json()
                print(f"\n📈 Overall Aurora Shield Stats:")
                print(f"   Total requests processed: {stats.get('total_requests', 0)}")
                print(f"   Blocked requests: {stats.get('blocked_requests', 0)}")
                print(f"   Active threats: {stats.get('active_threats', 0)}")
            
        except Exception as e:
            print(f"❌ Status check failed: {e}")

def main():
    """Run direct Aurora Shield API test."""
    print("🛡️  Aurora Shield Direct API Test")
    print("Testing automated sinkhole via /api/shield/check-request")
    print("=" * 60)
    
    tester = DirectShieldTest()
    
    try:
        # Test authentication first
        if not tester.authenticate():
            print("❌ Authentication failed, but continuing with tests...")
        
        # Test 1: Zero reputation attacks
        attack_results = tester.simulate_zero_reputation_attacks()
        time.sleep(2)
        
        # Check status after attacks
        tester.check_sinkhole_and_attacks()
        time.sleep(2)
        
        # Test 2: Legitimate traffic
        legit_results = tester.simulate_legitimate_traffic()
        time.sleep(2)
        
        # Final comprehensive status check
        print("\n" + "="*60)
        print("🔍 FINAL COMPREHENSIVE STATUS")
        print("="*60)
        tester.check_sinkhole_and_attacks()
        
        # Summary
        print(f"\n📋 Test Summary:")
        attack_count = len([r for r in attack_results if r['malicious']])
        legit_count = len([r for r in legit_results if not r['malicious']])
        print(f"   Attack requests sent: {attack_count}")
        print(f"   Legitimate requests sent: {legit_count}")
        print(f"   ✅ Test completed!")
        print(f"\n🌐 Check the dashboard at http://localhost:8080")
        
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

if __name__ == "__main__":
    main()