"""
Sinkhole/Blackhole Implementation for Aurora Shield
Advanced traffic redirection and isolation for malicious actors
"""

import time
import threading
import ipaddress
from collections import defaultdict, deque
from typing import Dict, List, Set, Optional, Tuple
import logging
import json
import hashlib
from flask import Flask, request, jsonify, render_template

logger = logging.getLogger(__name__)

class SinkholeManager:
    """
    Manages sinkhole/blackhole operations for malicious traffic isolation
    """
    
    def __init__(self):
        # Sinkhole classifications
        self.ip_sinkholes = set()           # Individual IPs in sinkhole
        self.subnet_sinkholes = set()       # Subnets in sinkhole
        self.fingerprint_sinkholes = set()  # Browser fingerprints in sinkhole
        
        # Blackhole (complete block) lists
        self.ip_blackholes = set()
        self.subnet_blackholes = set()
        
        # Temporary quarantine (time-based isolation)
        self.quarantine = defaultdict(lambda: {'until': 0, 'reason': '', 'violations': 0})
        
        # Sinkhole servers (fake endpoints)
        self.sinkhole_responses = {
            'web': self._generate_fake_webpage,
            'api': self._generate_fake_api_response,
            'file': self._generate_fake_file,
            'redirect': self._generate_redirect_loop
        }
        
        # Statistics and monitoring
        self.stats = {
            'sinkholed_requests': 0,
            'blackholed_requests': 0,
            'quarantined_requests': 0,
            'honeypot_interactions': 0,
            'total_malicious_ips': 0,
            'data_collected': 0  # bytes of attack data collected
        }
        
        # Auto-learning system
        self.reputation_decay = {}
        self.behavior_patterns = defaultdict(list)
        
        # Sinkhole configuration
        self.config = {
            'auto_sinkhole_threshold': 10,      # violations before auto-sinkhole
            'auto_blackhole_threshold': 50,     # violations before auto-blackhole
            'quarantine_duration': 3600,        # 1 hour default quarantine
            'reputation_decay_rate': 0.1,       # reputation improvement over time
            'honeypot_delay_min': 1.0,          # minimum response delay
            'honeypot_delay_max': 30.0,         # maximum response delay
            'data_collection_enabled': True,    # collect attack patterns
            'learning_mode': True               # auto-adapt to new attack patterns
        }
        
        # Lock for thread safety
        self.lock = threading.RLock()
        
        print("🕳️ Sinkhole/Blackhole Manager initialized")

    def check_request(self, ip: str, fingerprint: str = None, user_agent: str = None) -> Dict:
        """
        Check if request should be sinkholed, blackholed, or quarantined
        
        Returns:
            Dict with action: 'allow', 'sinkhole', 'blackhole', 'quarantine'
        """
        with self.lock:
            subnet = self._get_subnet(ip)
            
            # 1. Check blackhole lists (highest priority - complete block)
            if ip in self.ip_blackholes:
                self.stats['blackholed_requests'] += 1
                return {
                    'action': 'blackhole',
                    'reason': 'ip_blacklisted',
                    'ip': ip,
                    'response': None
                }
            
            if subnet in self.subnet_blackholes:
                self.stats['blackholed_requests'] += 1
                return {
                    'action': 'blackhole', 
                    'reason': 'subnet_blacklisted',
                    'subnet': subnet,
                    'response': None
                }
            
            # 2. Check quarantine status
            if ip in self.quarantine:
                quarantine_info = self.quarantine[ip]
                if time.time() < quarantine_info['until']:
                    self.stats['quarantined_requests'] += 1
                    return {
                        'action': 'quarantine',
                        'reason': quarantine_info['reason'],
                        'until': quarantine_info['until'],
                        'violations': quarantine_info['violations'],
                        'response': self._generate_quarantine_response()
                    }
                else:
                    # Quarantine expired, remove from list
                    del self.quarantine[ip]
            
            # 3. Check sinkhole lists (traffic redirection)
            if ip in self.ip_sinkholes:
                self.stats['sinkholed_requests'] += 1
                return {
                    'action': 'sinkhole',
                    'reason': 'ip_sinkholed',
                    'ip': ip,
                    'response': self._generate_sinkhole_response(ip, user_agent)
                }
            
            if subnet in self.subnet_sinkholes:
                self.stats['sinkholed_requests'] += 1
                return {
                    'action': 'sinkhole',
                    'reason': 'subnet_sinkholed', 
                    'subnet': subnet,
                    'response': self._generate_sinkhole_response(ip, user_agent)
                }
            
            if fingerprint and fingerprint in self.fingerprint_sinkholes:
                self.stats['sinkholed_requests'] += 1
                return {
                    'action': 'sinkhole',
                    'reason': 'fingerprint_sinkholed',
                    'fingerprint': fingerprint[:16] + "...",
                    'response': self._generate_sinkhole_response(ip, user_agent)
                }
            
            # 4. Request is allowed
            return {'action': 'allow', 'reason': 'not_malicious'}

    def add_to_sinkhole(self, target: str, target_type: str, reason: str = "manual"):
        """Add IP, subnet, or fingerprint to sinkhole"""
        with self.lock:
            if target_type == 'ip':
                self.ip_sinkholes.add(target)
                logger.info(f"🕳️ Added IP {target} to sinkhole: {reason}")
            elif target_type == 'subnet':
                self.subnet_sinkholes.add(target)
                logger.info(f"🕳️ Added subnet {target} to sinkhole: {reason}")
            elif target_type == 'fingerprint':
                self.fingerprint_sinkholes.add(target)
                logger.info(f"🕳️ Added fingerprint {target[:16]}... to sinkhole: {reason}")
            
            self.stats['total_malicious_ips'] = len(self.ip_sinkholes)

    def add_to_blackhole(self, target: str, target_type: str, reason: str = "manual"):
        """Add IP or subnet to blackhole (complete block)"""
        with self.lock:
            if target_type == 'ip':
                self.ip_blackholes.add(target)
                # Remove from sinkhole if present
                self.ip_sinkholes.discard(target)
                logger.info(f"🕳️ Added IP {target} to blackhole: {reason}")
            elif target_type == 'subnet':
                self.subnet_blackholes.add(target)
                self.subnet_sinkholes.discard(target)
                logger.info(f"🕳️ Added subnet {target} to blackhole: {reason}")

    def quarantine_ip(self, ip: str, duration: int = None, reason: str = "suspicious_activity"):
        """Place IP in temporary quarantine"""
        with self.lock:
            duration = duration or self.config['quarantine_duration']
            until_time = time.time() + duration
            
            self.quarantine[ip] = {
                'until': until_time,
                'reason': reason,
                'violations': self.quarantine[ip]['violations'] + 1 if ip in self.quarantine else 1
            }
            
            logger.info(f"⏰ Quarantined IP {ip} for {duration}s: {reason}")

    def process_violation(self, ip: str, violation_type: str, severity: int = 1):
        """
        Process a security violation and potentially escalate to sinkhole/blackhole
        """
        with self.lock:
            # Record violation pattern
            self.behavior_patterns[ip].append({
                'type': violation_type,
                'severity': severity,
                'timestamp': time.time()
            })
            
            # Calculate total violations in last hour
            recent_violations = [
                v for v in self.behavior_patterns[ip]
                if time.time() - v['timestamp'] < 3600
            ]
            violation_score = sum(v['severity'] for v in recent_violations)
            
            subnet = self._get_subnet(ip)
            
            # Auto-escalation logic
            if violation_score >= self.config['auto_blackhole_threshold']:
                self.add_to_blackhole(ip, 'ip', f"auto_escalation:{violation_type}:score_{violation_score}")
                logger.warning(f"🚨 Auto-blackholed {ip} (score: {violation_score})")
                
            elif violation_score >= self.config['auto_sinkhole_threshold']:
                self.add_to_sinkhole(ip, 'ip', f"auto_escalation:{violation_type}:score_{violation_score}")
                logger.warning(f"🕳️ Auto-sinkholed {ip} (score: {violation_score})")
                
            elif violation_score >= 5:  # Quarantine threshold
                self.quarantine_ip(ip, reason=f"repeated_violations:{violation_type}")
                logger.warning(f"⏰ Auto-quarantined {ip} (score: {violation_score})")
            
            # Subnet-level analysis
            subnet_violations = 0
            for other_ip in self.behavior_patterns:
                if self._get_subnet(other_ip) == subnet:
                    recent_subnet_violations = [
                        v for v in self.behavior_patterns[other_ip]
                        if time.time() - v['timestamp'] < 3600
                    ]
                    subnet_violations += len(recent_subnet_violations)
            
            # Subnet-level escalation
            if subnet_violations >= 20:  # Multiple IPs from same subnet
                self.add_to_sinkhole(subnet, 'subnet', f"subnet_pattern:{subnet_violations}_violations")
                logger.warning(f"🕳️ Auto-sinkholed subnet {subnet} ({subnet_violations} violations)")

    def _generate_sinkhole_response(self, ip: str, user_agent: str = None) -> Dict:
        """Generate appropriate sinkhole response based on request characteristics"""
        self.stats['honeypot_interactions'] += 1
        
        # Analyze request to determine best sinkhole response
        if user_agent and any(bot in user_agent.lower() for bot in ['bot', 'crawler', 'curl', 'wget']):
            response_type = 'api'
        elif user_agent and 'mozilla' in user_agent.lower():
            response_type = 'web'
        else:
            response_type = 'redirect'
        
        # Add artificial delay to waste attacker resources
        delay = min(
            self.config['honeypot_delay_max'],
            max(self.config['honeypot_delay_min'], hash(ip) % 10)
        )
        
        return {
            'type': response_type,
            'delay': delay,
            'content': self.sinkhole_responses[response_type](ip, user_agent),
            'collect_data': self.config['data_collection_enabled']
        }

    def _generate_fake_webpage(self, ip: str, user_agent: str = None) -> str:
        """Generate realistic fake webpage to waste attacker time"""
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>System Maintenance</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 50px; }}
        .loading {{ text-align: center; }}
        .spinner {{ 
            border: 4px solid #f3f3f3;
            border-top: 4px solid #3498db;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 2s linear infinite;
            margin: 20px auto;
        }}
        @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
    </style>
</head>
<body>
    <div class="loading">
        <h2>System Maintenance in Progress</h2>
        <div class="spinner"></div>
        <p>Please wait while we prepare your content...</p>
        <p>Session ID: {hashlib.md5(ip.encode()).hexdigest()}</p>
        <script>
            setTimeout(function() {{
                document.body.innerHTML += '<p>Loading additional resources...</p>';
            }}, 5000);
            // Honeypot JavaScript to collect bot behavior
            var honeypot = {{
                clientIP: '{ip}',
                userAgent: '{user_agent or "unknown"}',
                timestamp: new Date().toISOString(),
                actions: []
            }};
        </script>
    </div>
</body>
</html>"""

    def _generate_fake_api_response(self, ip: str, user_agent: str = None) -> Dict:
        """Generate fake API response to collect bot behavior"""
        return {
            'status': 'processing',
            'message': 'Request queued for processing',
            'request_id': hashlib.md5(f"{ip}{time.time()}".encode()).hexdigest(),
            'estimated_time': 30,
            'next_check': '/api/status/check',
            'metadata': {
                'client_info': {
                    'ip': ip,
                    'user_agent': user_agent,
                    'session': hashlib.md5(ip.encode()).hexdigest()
                }
            }
        }

    def _generate_fake_file(self, ip: str, user_agent: str = None) -> bytes:
        """Generate fake file content"""
        content = f"""# System Configuration File
# Generated for client: {ip}
# Timestamp: {time.time()}

[system]
status=maintenance
client_id={hashlib.md5(ip.encode()).hexdigest()}
user_agent={user_agent or 'unknown'}

[processing]
queue_position=1
estimated_wait=300
retry_after=60

# Please wait for system to complete maintenance
# Do not modify this file
""".encode('utf-8')
        
        return content

    def _generate_redirect_loop(self, ip: str, user_agent: str = None) -> Dict:
        """Generate redirect loop to waste resources"""
        paths = [
            '/loading',
            '/wait',
            '/processing', 
            '/queue',
            '/status',
            '/check'
        ]
        
        redirect_path = paths[hash(ip) % len(paths)]
        
        return {
            'status': 302,
            'location': redirect_path,
            'delay': 2 + (hash(ip) % 5)  # 2-6 second delay
        }

    def _generate_quarantine_response(self) -> Dict:
        """Generate response for quarantined IPs"""
        return {
            'status': 429,
            'message': 'Rate limit exceeded - temporary restriction in effect',
            'retry_after': 300,
            'type': 'quarantine'
        }

    def _get_subnet(self, ip: str) -> str:
        """Get /24 subnet for IPv4 or /64 for IPv6"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            if ip_obj.version == 4:
                network = ipaddress.ip_network(f"{ip}/24", strict=False)
                return str(network.network_address) + "/24"
            else:
                network = ipaddress.ip_network(f"{ip}/64", strict=False)
                return str(network.network_address) + "/64"
        except:
            return "unknown"

    def get_statistics(self) -> Dict:
        """Get sinkhole/blackhole statistics"""
        with self.lock:
            return {
                'counts': {
                    'sinkholed_ips': len(self.ip_sinkholes),
                    'sinkholed_subnets': len(self.subnet_sinkholes),
                    'sinkholed_fingerprints': len(self.fingerprint_sinkholes),
                    'blackholed_ips': len(self.ip_blackholes),
                    'blackholed_subnets': len(self.subnet_blackholes),
                    'quarantined_ips': len(self.quarantine)
                },
                'stats': self.stats.copy(),
                'active_quarantine': {
                    ip: info for ip, info in self.quarantine.items()
                    if time.time() < info['until']
                }
            }

    def get_detailed_status(self) -> Dict:
        """Get detailed status for monitoring"""
        with self.lock:
            # Get top violating IPs
            top_violators = []
            for ip, violations in list(self.behavior_patterns.items())[:10]:
                recent_violations = [v for v in violations if time.time() - v['timestamp'] < 3600]
                if recent_violations:
                    top_violators.append({
                        'ip': ip,
                        'violations': len(recent_violations),
                        'total_severity': sum(v['severity'] for v in recent_violations),
                        'last_violation': max(v['timestamp'] for v in recent_violations)
                    })
            
            top_violators.sort(key=lambda x: x['total_severity'], reverse=True)
            
            return {
                'statistics': self.get_statistics(),
                'top_violators': top_violators[:5],
                'recent_actions': self._get_recent_actions(),
                'config': self.config,
                'timestamp': time.time()
            }

    def _get_recent_actions(self) -> List[Dict]:
        """Get recent sinkhole/blackhole actions"""
        # This would be implemented with a proper action log in production
        return [
            {
                'timestamp': time.time() - 300,
                'action': 'sinkhole',
                'target': 'IP 192.168.1.100',
                'reason': 'repeated_violations'
            },
            {
                'timestamp': time.time() - 600,
                'action': 'quarantine',
                'target': 'IP 10.0.1.50',
                'reason': 'suspicious_activity'
            }
        ]

    def cleanup_expired_data(self):
        """Clean up expired quarantine entries and old behavior data"""
        with self.lock:
            current_time = time.time()
            
            # Remove expired quarantine entries
            expired_ips = [
                ip for ip, info in self.quarantine.items()
                if current_time > info['until']
            ]
            for ip in expired_ips:
                del self.quarantine[ip]
            
            # Clean old behavior patterns (keep last 24 hours)
            cutoff_time = current_time - 86400
            for ip in list(self.behavior_patterns.keys()):
                self.behavior_patterns[ip] = [
                    v for v in self.behavior_patterns[ip]
                    if v['timestamp'] > cutoff_time
                ]
                if not self.behavior_patterns[ip]:
                    del self.behavior_patterns[ip]

    def export_threat_intelligence(self) -> Dict:
        """Export threat intelligence data for sharing"""
        with self.lock:
            return {
                'export_timestamp': time.time(),
                'malicious_ips': list(self.ip_blackholes),
                'sinkholed_ips': list(self.ip_sinkholes),
                'malicious_subnets': list(self.subnet_blackholes),
                'threat_patterns': {
                    ip: [
                        {
                            'type': v['type'],
                            'severity': v['severity'],
                            'timestamp': v['timestamp']
                        }
                        for v in violations[-10:]  # Last 10 violations per IP
                    ]
                    for ip, violations in self.behavior_patterns.items()
                    if violations
                },
                'statistics': self.stats.copy()
            }


# Global sinkhole manager instance
sinkhole_manager = SinkholeManager()


def start_sinkhole_cleanup_thread():
    """Start background thread for cleanup operations"""
    def cleanup_loop():
        while True:
            try:
                sinkhole_manager.cleanup_expired_data()
                time.sleep(300)  # Cleanup every 5 minutes
            except Exception as e:
                logger.error(f"Sinkhole cleanup error: {e}")
                time.sleep(60)
    
    cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
    cleanup_thread.start()
    logger.info("🧹 Sinkhole cleanup thread started")