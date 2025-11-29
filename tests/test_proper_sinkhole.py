#!/usr/bin/env python3
"""
Test Aurora Shield's automated sinkhole through the load balancer.
"""

import requests
import time
import random
from concurrent.futures import ThreadPoolExecutor

class ProperSinkholeTest:
    def __init__(self):
        self.load_balancer_url = "http://localhost:8090"  # Load balancer routes through Aurora Shield
        self.dashboard_url = "http://localhost:8080"       # Direct dashboard access
        self.session = requests.Session()
        
    def authenticate_dashboard(self):
        """Authenticate with the dashboard."""
        login_data = {'username': 'admin', 'password': 'admin123'}
        response = self.session.post(f"{self.dashboard_url}/login", data=login_data)
        return response.status_code == 200
    
    def send_attack_traffic(self, source_ip, num_requests=20):
        """Send malicious traffic through the load balancer."""
        print(f"🎯 Sending attack traffic from {source_ip}")
        
        for i in range(num_requests):
            try:
                headers = {
                    'X-Forwarded-For': source_ip,
                    'X-Real-IP': source_ip,
                    'User-Agent': f'AttackBot/{random.randint(1,5)}.0'
                }
                
                # Mix different attack patterns
                if i % 4 == 0:
                    # SQL injection
                    params = {'id': "1' OR '1'='1", 'action': 'delete'}
                elif i % 4 == 1:
                    # XSS
                    params = {'search': '<script>alert("hack")</script>'}
                elif i % 4 == 2:
                    # Path traversal
                    params = {'file': '../../../etc/passwd'}
                else:
                    # Rapid fire
                    params = {'spam': 'true', 'count': i}
                
                # Send through load balancer (which routes through Aurora Shield)
                response = requests.get(
                    self.load_balancer_url,
                    params=params,
                    headers=headers,
                    timeout=3
                )
                
                if i % 5 == 0:
                    print(f"  Request {i+1}: {response.status_code}")
                
            except Exception as e:
                print(f"  Request {i+1} failed: {e}")
            
            time.sleep(0.1)  # Small delay between requests
    
    def send_legitimate_traffic(self, source_ip, num_requests=10):
        """Send legitimate traffic through the load balancer."""
        print(f"✅ Sending legitimate traffic from {source_ip}")
        
        for i in range(num_requests):
            try:
                headers = {
                    'X-Forwarded-For': source_ip,
                    'X-Real-IP': source_ip,
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                # Normal requests
                params = {'page': 'home', 'user': f'user_{i}'}
                
                response = requests.get(
                    self.load_balancer_url,
                    params=params,
                    headers=headers,
                    timeout=3
                )
                
                if i % 3 == 0:
                    print(f"  Request {i+1}: {response.status_code}")
                
            except Exception as e:
                print(f"  Request {i+1} failed: {e}")
            
            time.sleep(0.2)
    
    def check_aurora_shield_status(self):
        """Check Aurora Shield's attacking IP and sinkhole status."""
        if not self.authenticate_dashboard():
            print("❌ Failed to authenticate with dashboard")
            return
        
        print("\n🔍 Checking Aurora Shield Status...")
        
        try:
            # Check attacking IPs
            response = self.session.get(f"{self.dashboard_url}/api/dashboard/attacking-ips")
            if response.status_code == 200:
                data = response.json()
                attacking_data = data.get('data', {})
                
                recent_attacks = attacking_data.get('recent_attacks', [])
                print(f"📊 Recent attacks detected: {len(recent_attacks)}")
                
                for attack in recent_attacks[:5]:
                    if isinstance(attack, dict):
                        print(f"  🎯 {attack.get('ip', 'Unknown')}: {attack.get('attack_type', 'Unknown attack')}")
                
                sinkhole_summary = attacking_data.get('sinkhole_summary', {})
                print(f"\n🕳️  Sinkhole Summary:")
                print(f"   Sinkholed IPs: {sinkhole_summary.get('sinkholed_ips', 0)}")
                print(f"   Quarantined IPs: {sinkhole_summary.get('quarantined_ips', 0)}")
                print(f"   Blackholed IPs: {sinkhole_summary.get('blackholed_ips', 0)}")
                
                sinkholed_ips = attacking_data.get('sinkholed_ips', [])
                if sinkholed_ips:
                    print(f"\n🔒 Currently Sinkholed IPs:")
                    for ip in sinkholed_ips[:3]:
                        print(f"  - {ip}")
                
            else:
                print(f"❌ Failed to get attacking IPs: {response.status_code}")
            
            # Check general stats
            stats_response = self.session.get(f"{self.dashboard_url}/api/dashboard/stats")
            if stats_response.status_code == 200:
                stats = stats_response.json()
                print(f"\n📈 Overall Stats:")
                print(f"   Total requests: {stats.get('total_requests', 0)}")
                print(f"   Blocked requests: {stats.get('blocked_requests', 0)}")
                print(f"   Active threats: {stats.get('active_threats', 0)}")
                
        except Exception as e:
            print(f"❌ Status check failed: {e}")

def main():
    """Run the sinkhole automation test."""
    print("🛡️  Aurora Shield Sinkhole Automation Test")
    print("=" * 50)
    
    tester = ProperSinkholeTest()
    
    try:
        # Test 1: Send attack traffic to trigger sinkholing
        print("\n[TEST 1] Sending attack traffic to trigger automated sinkholing...")
        attack_ips = ['192.168.100.10', '10.0.50.25', '172.16.200.100']
        
        for ip in attack_ips:
            tester.send_attack_traffic(ip, 15)
            time.sleep(1)
        
        print("✅ Attack traffic sent")
        time.sleep(3)  # Wait for processing
        
        # Check status after attacks
        tester.check_aurora_shield_status()
        
        # Test 2: Send legitimate traffic
        print("\n[TEST 2] Sending legitimate traffic...")
        legit_ips = ['203.0.113.50', '198.51.100.75']
        
        for ip in legit_ips:
            tester.send_legitimate_traffic(ip, 8)
            time.sleep(1)
        
        print("✅ Legitimate traffic sent")
        time.sleep(2)
        
        # Final status check
        print("\n" + "="*50)
        print("🔍 FINAL STATUS CHECK")
        print("="*50)
        tester.check_aurora_shield_status()
        
        print("\n✅ Test completed! Check the dashboard at http://localhost:8080")
        
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

if __name__ == "__main__":
    main()