#!/usr/bin/env python3
"""
Test script to generate traffic patterns for testing the new rate limiting GUI.
This will create different types of traffic to show:
- Normal IPs (under limit)
- High load IPs (80%+ of limit)
- Rate-limited IPs (over limit)
"""

import requests
import threading
import time
import random

# Aurora Shield gateway endpoint
GATEWAY_URL = "http://localhost:8081"  # Assuming gateway runs on 8081
DASHBOARD_URL = "http://localhost:8080"

class TrafficGenerator:
    def __init__(self):
        self.running = False
        self.threads = []
    
    def start_normal_traffic(self, ip_base="192.168.1", count=5):
        """Generate normal traffic from multiple IPs (under 100 req/min)"""
        def normal_pattern(ip_suffix):
            while self.running:
                try:
                    fake_ip = f"{ip_base}.{ip_suffix}"
                    headers = {
                        'X-Forwarded-For': fake_ip,
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                    
                    # Normal rate: 30-60 requests per minute
                    requests.get(f"{GATEWAY_URL}/", headers=headers, timeout=2)
                    time.sleep(random.uniform(1.5, 2.5))  # 24-40 req/min
                    
                except Exception as e:
                    print(f"Normal traffic error for {fake_ip}: {e}")
                    time.sleep(1)
        
        print(f"🟢 Starting normal traffic from {count} IPs...")
        for i in range(1, count + 1):
            thread = threading.Thread(target=normal_pattern, args=(i,))
            self.threads.append(thread)
            thread.start()
    
    def start_high_load_traffic(self, ip_base="192.168.2", count=3):
        """Generate high load traffic (80%+ of limit but not blocked)"""
        def high_load_pattern(ip_suffix):
            while self.running:
                try:
                    fake_ip = f"{ip_base}.{ip_suffix}"
                    headers = {
                        'X-Forwarded-For': fake_ip,
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                    
                    # High load: 80-95 requests per minute
                    requests.get(f"{GATEWAY_URL}/", headers=headers, timeout=2)
                    time.sleep(random.uniform(0.65, 0.75))  # 80-90 req/min
                    
                except Exception as e:
                    print(f"High load traffic error for {fake_ip}: {e}")
                    time.sleep(1)
        
        print(f"🟡 Starting high load traffic from {count} IPs...")
        for i in range(1, count + 1):
            thread = threading.Thread(target=high_load_pattern, args=(i,))
            self.threads.append(thread)
            thread.start()
    
    def start_rate_limited_traffic(self, ip_base="192.168.3", count=2):
        """Generate traffic that will be rate limited (over 100 req/min)"""
        def rate_limited_pattern(ip_suffix):
            while self.running:
                try:
                    fake_ip = f"{ip_base}.{ip_suffix}"
                    headers = {
                        'X-Forwarded-For': fake_ip,
                        'User-Agent': 'AttackBot/1.0'  # Suspicious user agent
                    }
                    
                    # Aggressive rate: 150-200 requests per minute
                    requests.get(f"{GATEWAY_URL}/", headers=headers, timeout=2)
                    time.sleep(random.uniform(0.3, 0.4))  # 150-200 req/min
                    
                except Exception as e:
                    print(f"Rate limited traffic error for {fake_ip}: {e}")
                    time.sleep(1)
        
        print(f"🔴 Starting rate limited traffic from {count} IPs...")
        for i in range(1, count + 1):
            thread = threading.Thread(target=rate_limited_pattern, args=(i,))
            self.threads.append(thread)
            thread.start()
    
    def start_legitimate_bypass_traffic(self, ip_base="192.168.4", count=2):
        """Generate legitimate traffic that should bypass rate limiting"""
        def legitimate_pattern(ip_suffix):
            while self.running:
                try:
                    fake_ip = f"{ip_base}.{ip_suffix}"
                    headers = {
                        'X-Forwarded-For': fake_ip,
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    }
                    
                    # Legitimate paths that trigger bypass
                    paths = ['/favicon.ico', '/robots.txt', '/sitemap.xml', '/']
                    path = random.choice(paths)
                    
                    # High rate but should bypass due to legitimate patterns
                    requests.get(f"{GATEWAY_URL}{path}", headers=headers, timeout=2)
                    time.sleep(random.uniform(0.4, 0.6))  # 100-150 req/min but bypassed
                    
                except Exception as e:
                    print(f"Legitimate bypass traffic error for {fake_ip}: {e}")
                    time.sleep(1)
        
        print(f"✅ Starting legitimate bypass traffic from {count} IPs...")
        for i in range(1, count + 1):
            thread = threading.Thread(target=legitimate_pattern, args=(i,))
            self.threads.append(thread)
            thread.start()
    
    def start_all_patterns(self):
        """Start all traffic patterns for comprehensive testing"""
        self.running = True
        
        print("🚀 Starting comprehensive traffic patterns...")
        print("=" * 60)
        
        # Start different traffic patterns
        self.start_normal_traffic(count=5)
        time.sleep(2)
        
        self.start_high_load_traffic(count=3)
        time.sleep(2)
        
        self.start_rate_limited_traffic(count=2)
        time.sleep(2)
        
        self.start_legitimate_bypass_traffic(count=2)
        
        print("=" * 60)
        print("✅ All traffic patterns started!")
        print("📊 Check the dashboard at: http://localhost:8080")
        print("   Navigate to 'Live Requests' tab to see rate limiting visualization")
        print("🛑 Press Ctrl+C to stop all traffic")
        print("=" * 60)
    
    def stop_all(self):
        """Stop all traffic generation"""
        print("\n🛑 Stopping all traffic generation...")
        self.running = False
        
        for thread in self.threads:
            thread.join(timeout=2)
        
        print("✅ All traffic stopped")


def main():
    """Main function to run traffic generation"""
    generator = TrafficGenerator()
    
    try:
        # Check if gateway is running
        try:
            response = requests.get(f"{GATEWAY_URL}/", timeout=5)
            print("✅ Gateway is reachable")
        except:
            print("❌ Warning: Gateway might not be running at http://localhost:8081")
            print("   You can still test with simulated data in the dashboard")
        
        # Start traffic generation
        generator.start_all_patterns()
        
        # Keep running until interrupted
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        generator.stop_all()
    except Exception as e:
        print(f"❌ Error: {e}")
        generator.stop_all()


if __name__ == "__main__":
    main()