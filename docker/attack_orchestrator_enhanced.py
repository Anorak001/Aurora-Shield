#!/usr/bin/env python3
"""
Enhanced Attack Orchestrator with Virtual IP Management
Generates virtual IPs from different subnets for attack simulation
No real containers spawned - just intelligent virtual attack simulation
"""

import json
import time
import random
import threading
import requests
import ipaddress
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class VirtualBot:
    """Virtual bot with configurable attack parameters"""
    id: str
    ip: str
    subnet: str
    attack_type: str
    rate: float  # requests per second
    target_url: str
    user_agent: str
    status: str  # 'active', 'paused', 'stopped'
    total_requests: int
    successful_requests: int
    blocked_requests: int
    start_time: float
    last_activity: float
    payload_size: int
    concurrent_connections: int
    attack_duration: int  # seconds
    randomize_headers: bool
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'ip': self.ip,
            'subnet': self.subnet,
            'attack_type': self.attack_type,
            'rate': self.rate,
            'target_url': self.target_url,
            'user_agent': self.user_agent,
            'status': self.status,
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'blocked_requests': self.blocked_requests,
            'start_time': self.start_time,
            'last_activity': self.last_activity,
            'payload_size': self.payload_size,
            'concurrent_connections': self.concurrent_connections,
            'attack_duration': self.attack_duration,
            'randomize_headers': self.randomize_headers,
            'uptime': time.time() - self.start_time if self.status == 'active' else 0
        }

class VirtualBotManager:
    """Manages virtual attack bots with sophisticated IP generation"""
    
    def __init__(self):
        self.bots: Dict[str, VirtualBot] = {}
        self.active_threads: Dict[str, threading.Thread] = {}
        self.target_host = "load-balancer:8090"  # Target load balancer which routes through Aurora Shield
        self.attack_templates = {
            'normal': {
                'rate_range': (0.3, 2.0),  # Slower, more human-like rates
                'user_agents': ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'],
                'payloads': [50, 100, 200],
                'paths': ['/', '/index.html', '/favicon.ico', '/robots.txt', '/sitemap.xml', '/health.html']  # Paths that actually exist or are common
            },
            'http_flood': {
                'rate_range': (10, 100),
                'user_agents': ['AttackBot/1.0', 'FloodBot/2.1', 'HTTPStorm/1.5'],
                'payloads': [100, 500, 1000, 2000],
                'paths': ['/api/data', '/login', '/admin', '/upload', '/search']
            },
            'slowloris': {
                'rate_range': (0.1, 2),
                'user_agents': ['SlowClient/1.0', 'LowBandwidth/0.5'],
                'payloads': [50, 100],
                'paths': ['/login', '/admin', '/dashboard']
            },
            'ddos_burst': {
                'rate_range': (50, 500),
                'user_agents': ['BurstBot/3.0', 'RapidFire/2.0'],
                'payloads': [10, 50, 100],
                'paths': ['/api/endpoint', '/data', '/services']
            },
            'brute_force': {
                'rate_range': (1, 10),
                'user_agents': ['BruteForce/1.0', 'LoginBot/2.5'],
                'payloads': [200, 300],
                'paths': ['/login', '/admin/login', '/api/auth']
            },
            'resource_exhaustion': {
                'rate_range': (5, 50),
                'user_agents': ['ResourceBot/1.0', 'MemoryEater/1.5'],
                'payloads': [5000, 10000, 20000],
                'paths': ['/upload', '/process', '/generate']
            }
        }
        
        # Subnet ranges for generating diverse IPs
        self.subnet_ranges = [
            '192.168.0.0/16',    # Private network
            '10.0.0.0/8',        # Private network  
            '172.16.0.0/12',     # Private network
            '203.0.113.0/24',    # Test network
            '198.51.100.0/24',   # Test network
            '203.113.0.0/16',    # Various ranges
            '185.199.0.0/16',
            '151.101.0.0/16'
        ]
    
    def generate_virtual_ip(self, subnet_hint: str = None) -> tuple:
        """Generate a virtual IP from a specific subnet"""
        if subnet_hint:
            network = ipaddress.IPv4Network(subnet_hint, strict=False)
        else:
            subnet = random.choice(self.subnet_ranges)
            network = ipaddress.IPv4Network(subnet)
        
        # Generate random IP within the subnet
        network_int = int(network.network_address)
        broadcast_int = int(network.broadcast_address)
        random_int = random.randint(network_int + 1, broadcast_int - 1)
        
        ip = str(ipaddress.IPv4Address(random_int))
        subnet = str(network)
        
        return ip, subnet
    
    def create_virtual_bot(self, attack_type: str = None, custom_config: dict = None) -> VirtualBot:
        """Create a new virtual bot with specified or random configuration"""
        if not attack_type:
            attack_type = random.choice(list(self.attack_templates.keys()))
        
        # Validate attack type
        if attack_type not in self.attack_templates:
            raise ValueError(f"Invalid attack type: {attack_type}. Available types: {list(self.attack_templates.keys())}")
        
        template = self.attack_templates[attack_type]
        bot_id = f"vbot_{len(self.bots) + 1}_{int(time.time())}"
        
        # Generate IP and subnet
        ip, subnet = self.generate_virtual_ip()
        
        # Ensure unique IP
        while any(bot.ip == ip for bot in self.bots.values()):
            ip, subnet = self.generate_virtual_ip()
        
        # Create bot configuration
        rate = random.uniform(*template['rate_range'])
        user_agent = random.choice(template['user_agents'])
        payload_size = random.choice(template['payloads'])
        target_path = random.choice(template['paths'])
        
        bot = VirtualBot(
            id=bot_id,
            ip=ip,
            subnet=subnet,
            attack_type=attack_type,
            rate=rate,
            target_url=f"http://{self.target_host}{target_path}",
            user_agent=user_agent,
            status='stopped',
            total_requests=0,
            successful_requests=0,
            blocked_requests=0,
            start_time=time.time(),
            last_activity=time.time(),
            payload_size=payload_size,
            concurrent_connections=random.randint(1, 10),
            attack_duration=random.randint(60, 300),  # 1-5 minutes
            randomize_headers=True if attack_type == 'normal' else random.choice([True, False])
        )
        
        # Apply custom configuration if provided
        if custom_config:
            for key, value in custom_config.items():
                if hasattr(bot, key):
                    setattr(bot, key, value)
        
        self.bots[bot_id] = bot
        logger.info(f"Created virtual bot {bot_id} with IP {ip} for {attack_type}")
        return bot
    
    def start_bot(self, bot_id: str) -> bool:
        """Start a virtual bot's attack simulation"""
        if bot_id not in self.bots:
            return False
        
        bot = self.bots[bot_id]
        if bot.status == 'active':
            return True
        
        bot.status = 'active'
        bot.start_time = time.time()
        
        # Start attack thread
        thread = threading.Thread(
            target=self._bot_attack_loop,
            args=(bot_id,),
            daemon=True
        )
        thread.start()
        self.active_threads[bot_id] = thread
        
        logger.info(f"Started virtual bot {bot_id} ({bot.ip}) - {bot.attack_type}")
        return True
    
    def stop_bot(self, bot_id: str) -> bool:
        """Stop a virtual bot's attack"""
        if bot_id not in self.bots:
            return False
        
        bot = self.bots[bot_id]
        bot.status = 'stopped'
        
        # Remove from active threads
        if bot_id in self.active_threads:
            del self.active_threads[bot_id]
        
        logger.info(f"Stopped virtual bot {bot_id} ({bot.ip})")
        return True
    
    def pause_bot(self, bot_id: str) -> bool:
        """Pause a virtual bot's attack"""
        if bot_id not in self.bots:
            return False
        
        self.bots[bot_id].status = 'paused'
        logger.info(f"Paused virtual bot {bot_id}")
        return True
    
    def remove_bot(self, bot_id: str) -> bool:
        """Remove a virtual bot completely"""
        if bot_id not in self.bots:
            return False
        
        self.stop_bot(bot_id)
        del self.bots[bot_id]
        logger.info(f"Removed virtual bot {bot_id}")
        return True
    
    def update_bot_config(self, bot_id: str, config: dict) -> bool:
        """Update bot configuration"""
        if bot_id not in self.bots:
            return False
        
        bot = self.bots[bot_id]
        for key, value in config.items():
            if hasattr(bot, key):
                setattr(bot, key, value)
        
        logger.info(f"Updated bot {bot_id} configuration: {config}")
        return True
    
    def _bot_attack_loop(self, bot_id: str):
        """Main attack loop for virtual bot"""
        bot = self.bots.get(bot_id)
        if not bot:
            return
        
        logger.info(f"Bot {bot_id} attack loop started")
        
        while bot.status == 'active':
            try:
                # Simulate sending request
                self._simulate_request(bot)
                
                # Wait based on rate with randomness for normal bots
                if bot.rate > 0:
                    base_sleep = 1.0 / bot.rate
                    if bot.attack_type == 'normal':
                        # Add randomness for normal bots to avoid detection as automated
                        # Vary timing by ±50% to simulate human-like irregular patterns
                        variation = random.uniform(0.5, 1.5)
                        sleep_time = base_sleep * variation
                        # Also add occasional longer pauses (like a human reading)
                        if random.random() < 0.1:  # 10% chance of longer pause
                            sleep_time += random.uniform(2, 8)
                    else:
                        sleep_time = base_sleep
                    time.sleep(sleep_time)
                else:
                    time.sleep(1.0)
                
                # Check if attack duration exceeded
                if time.time() - bot.start_time > bot.attack_duration:
                    bot.status = 'stopped'
                    logger.info(f"Bot {bot_id} reached attack duration limit")
                    break
                    
            except Exception as e:
                logger.error(f"Error in bot {bot_id} attack loop: {e}")
                time.sleep(1)
        
        logger.info(f"Bot {bot_id} attack loop ended")
    
    def _simulate_request(self, bot: VirtualBot):
        """Simulate sending a request to the target"""
        try:
            # Prepare request data
            headers = {
                'User-Agent': bot.user_agent,
                'X-Forwarded-For': bot.ip,
                'X-Real-IP': bot.ip,
                'X-Original-IP': bot.ip  # For Aurora Shield IP detection
            }
            
            if bot.randomize_headers:
                headers.update({
                    'Accept': random.choice(['*/*', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'application/json']),
                    'Accept-Language': random.choice(['en-US,en;q=0.5', 'en-GB,en;q=0.5', 'de-DE,de;q=0.5']),
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': random.choice(['keep-alive', 'close'])
                })
            
            # Choose request method based on attack type
            if bot.attack_type == 'normal':
                method = 'GET'
                payload = None
            elif bot.attack_type in ['brute_force', 'resource_exhaustion']:
                method = 'POST'
                payload = 'x' * bot.payload_size if bot.payload_size > 0 else 'data=test&user=admin'
            else:
                method = random.choice(['GET', 'POST'])
                payload = 'x' * bot.payload_size if bot.payload_size > 0 else None
            
            # Send request to load balancer which should forward through Aurora Shield
            if method == 'GET':
                response = requests.get(
                    bot.target_url,
                    headers=headers,
                    timeout=10,
                    allow_redirects=True
                )
            else:
                response = requests.post(
                    bot.target_url,
                    headers=headers,
                    data=payload,
                    timeout=10,
                    allow_redirects=True
                )
            
            bot.total_requests += 1
            bot.last_activity = time.time()
            
            # Check response for blocking indicators
            if response.status_code == 200:
                bot.successful_requests += 1
                logger.debug(f"Bot {bot.id} request successful: {response.status_code}")
            elif response.status_code in [403, 429, 503]:  # Common blocking status codes
                bot.blocked_requests += 1
                logger.debug(f"Bot {bot.id} request blocked: {response.status_code}")
            elif response.status_code in [404, 500, 502, 503, 504]:  # Error status codes
                bot.blocked_requests += 1
                logger.debug(f"Bot {bot.id} request failed: {response.status_code}")
            else:
                # Other status codes might indicate partial success or server issues
                bot.successful_requests += 1
                logger.debug(f"Bot {bot.id} request completed with status: {response.status_code}")
                
        except requests.exceptions.Timeout:
            # Timeout might indicate rate limiting or DDoS protection
            bot.total_requests += 1
            bot.blocked_requests += 1
            bot.last_activity = time.time()
            logger.debug(f"Bot {bot.id} request timed out (likely blocked)")
        except requests.exceptions.ConnectionError:
            # Connection error might indicate blocking or network issues
            bot.total_requests += 1
            bot.blocked_requests += 1
            bot.last_activity = time.time()
            logger.debug(f"Bot {bot.id} connection error (likely blocked)")
        except requests.exceptions.RequestException as e:
            # Other request errors
            bot.total_requests += 1
            bot.blocked_requests += 1
            bot.last_activity = time.time()
            logger.debug(f"Bot {bot.id} request exception: {e}")
        except Exception as e:
            logger.error(f"Error simulating request for bot {bot.id}: {e}")
    
    def get_all_bots(self) -> List[dict]:
        """Get all bots as dictionary list"""
        return [bot.to_dict() for bot in self.bots.values()]
    
    def get_bot_stats(self) -> dict:
        """Get overall bot statistics"""
        total_bots = len(self.bots)
        active_bots = len([b for b in self.bots.values() if b.status == 'active'])
        paused_bots = len([b for b in self.bots.values() if b.status == 'paused'])
        stopped_bots = len([b for b in self.bots.values() if b.status == 'stopped'])
        
        total_requests = sum(bot.total_requests for bot in self.bots.values())
        total_blocked = sum(bot.blocked_requests for bot in self.bots.values())
        
        # Count attack types
        attack_type_counts = {}
        for bot in self.bots.values():
            attack_type_counts[bot.attack_type] = attack_type_counts.get(bot.attack_type, 0) + 1
        
        # Count subnets
        subnet_counts = {}
        for bot in self.bots.values():
            subnet_counts[bot.subnet] = subnet_counts.get(bot.subnet, 0) + 1
        
        return {
            'total_bots': total_bots,
            'active_bots': active_bots,
            'paused_bots': paused_bots,
            'stopped_bots': stopped_bots,
            'total_requests': total_requests,
            'total_blocked': total_blocked,
            'block_rate': (total_blocked / max(total_requests, 1)) * 100,
            'attack_types': attack_type_counts,
            'subnets': subnet_counts,
            'timestamp': time.time()
        }

# Initialize the bot manager
bot_manager = VirtualBotManager()

# Flask application
app = Flask(__name__)

@app.route('/')
def dashboard():
    """Enhanced dashboard for virtual bot management"""
    return render_template('attack_orchestrator_enhanced.html')

@app.route('/api/bots', methods=['GET'])
def get_bots():
    """Get all virtual bots"""
    return jsonify({
        'success': True,
        'bots': bot_manager.get_all_bots(),
        'stats': bot_manager.get_bot_stats()
    })

@app.route('/api/bots/create', methods=['POST'])
def create_bot():
    """Create a new virtual bot"""
    data = request.get_json() or {}
    
    attack_type = data.get('attack_type')
    
    # Build custom config from form data
    custom_config = {}
    
    # Rate configuration
    if 'rate' in data:
        custom_config['rate'] = float(data['rate'])
    
    # Duration configuration
    if 'duration' in data:
        custom_config['attack_duration'] = int(data['duration'])
    
    # Target configuration
    if 'target' in data:
        custom_config['target_url'] = data['target']
    
    # Path configuration
    if 'path' in data:
        custom_config['target_path'] = data['path']
    
    # User agent configuration
    if 'user_agent' in data:
        custom_config['user_agent'] = data['user_agent']
    
    # Payload size configuration
    if 'payload_size' in data:
        custom_config['payload_size'] = int(data['payload_size'])
    
    # Concurrent connections configuration
    if 'concurrent_connections' in data:
        custom_config['concurrent_connections'] = int(data['concurrent_connections'])
    
    # Headers randomization
    if 'randomize_headers' in data:
        custom_config['randomize_headers'] = bool(data['randomize_headers'])
    
    # Add any other custom config
    if 'config' in data:
        custom_config.update(data['config'])
    
    try:
        bot = bot_manager.create_virtual_bot(attack_type, custom_config)
        return jsonify({
            'success': True,
            'bot': bot.to_dict(),
            'message': f'Created virtual bot {bot.id}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/bots/<bot_id>/start', methods=['POST'])
def start_bot(bot_id):
    """Start a virtual bot"""
    success = bot_manager.start_bot(bot_id)
    if success:
        return jsonify({
            'success': True,
            'message': f'Started bot {bot_id}'
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Bot not found'
        }), 404

@app.route('/api/bots/<bot_id>/stop', methods=['POST'])
def stop_bot(bot_id):
    """Stop a virtual bot"""
    success = bot_manager.stop_bot(bot_id)
    if success:
        return jsonify({
            'success': True,
            'message': f'Stopped bot {bot_id}'
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Bot not found'
        }), 404

@app.route('/api/bots/<bot_id>/pause', methods=['POST'])
def pause_bot(bot_id):
    """Pause a virtual bot"""
    success = bot_manager.pause_bot(bot_id)
    if success:
        return jsonify({
            'success': True,
            'message': f'Paused bot {bot_id}'
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Bot not found'
        }), 404

@app.route('/api/bots/<bot_id>/remove', methods=['DELETE'])
def remove_bot(bot_id):
    """Remove a virtual bot"""
    success = bot_manager.remove_bot(bot_id)
    if success:
        return jsonify({
            'success': True,
            'message': f'Removed bot {bot_id}'
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Bot not found'
        }), 404

@app.route('/api/bots/<bot_id>/config', methods=['PUT'])
def update_bot_config(bot_id):
    """Update bot configuration"""
    data = request.get_json() or {}
    success = bot_manager.update_bot_config(bot_id, data)
    
    if success:
        return jsonify({
            'success': True,
            'message': f'Updated bot {bot_id} configuration'
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Bot not found'
        }), 404

@app.route('/api/bots/bulk/start', methods=['POST'])
def start_all_bots():
    """Start all stopped bots"""
    started = 0
    for bot_id, bot in bot_manager.bots.items():
        if bot.status == 'stopped':
            if bot_manager.start_bot(bot_id):
                started += 1
    
    return jsonify({
        'success': True,
        'message': f'Started {started} bots'
    })

@app.route('/api/bots/bulk/stop', methods=['POST'])
def stop_all_bots():
    """Stop all active bots"""
    stopped = 0
    for bot_id, bot in bot_manager.bots.items():
        if bot.status == 'active':
            if bot_manager.stop_bot(bot_id):
                stopped += 1
    
    return jsonify({
        'success': True,
        'message': f'Stopped {stopped} bots'
    })

@app.route('/api/attack-types')
def get_attack_types():
    """Get available attack types"""
    return jsonify({
        'success': True,
        'attack_types': list(bot_manager.attack_templates.keys()),
        'templates': bot_manager.attack_templates
    })

@app.route('/api/bots/delete-all', methods=['DELETE'])
def delete_all_bots():
    """Delete all bots"""
    try:
        # Stop all active threads
        for thread in bot_manager.active_threads.values():
            if thread.is_alive():
                thread.join(timeout=1)
        
        # Clear all bots and threads
        bot_manager.bots.clear()
        bot_manager.active_threads.clear()
        
        logger.info("🗑️ All virtual bots deleted")
        return jsonify({
            'success': True,
            'message': 'All bots deleted successfully',
            'timestamp': time.time()
        })
    except Exception as e:
        logger.error(f"Error deleting all bots: {e}")
        return jsonify({
            'success': False,
            'message': str(e),
            'timestamp': time.time()
        }), 500

@app.route('/api/analytics')
def get_analytics():
    """Get analytics data for dashboard"""
    try:
        # Calculate analytics from current bot data
        total_requests = sum(bot.total_requests for bot in bot_manager.bots.values())
        total_successful = sum(bot.successful_requests for bot in bot_manager.bots.values())
        total_blocked = sum(bot.blocked_requests for bot in bot_manager.bots.values())
        
        # Request types distribution
        request_types = {}
        for bot in bot_manager.bots.values():
            if bot.attack_type in request_types:
                request_types[bot.attack_type] += bot.total_requests
            else:
                request_types[bot.attack_type] = bot.total_requests
        
        # Status codes (simulated based on success/block rates)
        status_codes = {
            '200': total_successful,
            '403': total_blocked,
            '429': int(total_blocked * 0.3),  # Rate limited
            '500': int(total_requests * 0.05)  # Server errors
        }
        
        # Attack types distribution
        attack_types = {}
        for bot in bot_manager.bots.values():
            if bot.attack_type in attack_types:
                attack_types[bot.attack_type] += 1
            else:
                attack_types[bot.attack_type] = 1
        
        # Timeline data (simulated - last 10 minutes)
        timeline = []
        current_time = time.time()
        for i in range(10):
            minute_ago = current_time - (i * 60)
            timestamp = datetime.fromtimestamp(minute_ago).strftime('%H:%M')
            requests_per_minute = random.randint(50, 200) if bot_manager.bots else 0
            timeline.append({
                'time': timestamp,
                'requests': requests_per_minute
            })
        timeline.reverse()
        
        # Calculate rates
        error_rate = (total_blocked / total_requests * 100) if total_requests > 0 else 0
        active_bots = len([b for b in bot_manager.bots.values() if b.status == 'active'])
        requests_per_second = sum(bot.rate for bot in bot_manager.bots.values() if bot.status == 'active')
        
        analytics = {
            'total_requests': total_requests,
            'requests_per_second': requests_per_second,
            'avg_response_time': random.randint(50, 300),  # Simulated
            'error_rate': error_rate,
            'request_types': request_types,
            'status_codes': status_codes,
            'timeline': timeline,
            'attack_types': attack_types,
            'active_bots': active_bots
        }
        
        return jsonify({
            'success': True,
            'analytics': analytics,
            'timestamp': time.time()
        })
    except Exception as e:
        logger.error(f"Error generating analytics: {e}")
        return jsonify({
            'success': False,
            'message': str(e),
            'timestamp': time.time()
        }), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time(),
        'version': '2.0.0',
        'active_bots': len([b for b in bot_manager.bots.values() if b.status == 'active'])
    })

if __name__ == '__main__':
    logger.info("🤖 Starting Enhanced Virtual Attack Orchestrator")
    logger.info("🎯 Features: Virtual IPs, Multi-subnet attacks, No container spawning")
    
    # Create some initial bots for demonstration
    for attack_type in ['http_flood', 'ddos_burst', 'slowloris', 'brute_force']:
        bot_manager.create_virtual_bot(attack_type)
    
    logger.info(f"✅ Created {len(bot_manager.bots)} initial virtual bots")
    
    app.run(host='0.0.0.0', port=5000, debug=False)