"""
Advanced Multi-Key Rate Limiting System
Provides sophisticated rate limiting beyond simple per-IP blocking
"""

import time
import hashlib
import ipaddress
from collections import defaultdict, deque
from typing import Dict, List, Tuple, Optional
import threading
import json

class AdvancedRateLimiter:
    def __init__(self):
        # Multi-dimensional rate limiting stores
        self.per_ip_limits = defaultdict(lambda: deque())
        self.per_subnet_limits = defaultdict(lambda: deque())
        self.per_fingerprint_limits = defaultdict(lambda: deque())
        self.global_request_queue = deque()
        
        # Fair queuing per-IP queues
        self.per_ip_queues = defaultdict(lambda: deque())
        
        # Behavior pattern tracking
        self.behavior_patterns = defaultdict(lambda: {
            'request_intervals': deque(maxlen=20),
            'user_agents': set(),
            'paths_accessed': set(),
            'suspicious_score': 0.0,
            'last_analysis': 0
        })
        
        # Configuration
        self.config = {
            'per_ip_rps': 10,           # requests per second per IP
            'per_subnet_rps': 50,       # requests per second per /24 subnet
            'per_fingerprint_rps': 20,  # requests per second per browser fingerprint
            'global_rps': 1000,         # global requests per second
            'burst_allowance': 1.5,     # multiplier for short bursts
            'window_size': 60,          # sliding window in seconds
            'suspicious_threshold': 0.7, # behavior suspicion threshold
            'fair_queue_weight': 0.8    # weight for fair queuing (0-1)
        }
        
        # Lock for thread safety
        self.lock = threading.RLock()
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'blocked_by_ip': 0,
            'blocked_by_subnet': 0,
            'blocked_by_fingerprint': 0,
            'blocked_by_global': 0,
            'blocked_by_behavior': 0,
            'queued_requests': 0,
            'active_ips': 0,
            'active_subnets': 0
        }
        
        print("🛡️ Advanced Multi-Key Rate Limiter initialized")

    def check_request(self, request_data: Dict) -> Tuple[bool, str, Dict]:
        """
        Check if request should be allowed through advanced rate limiting
        
        Args:
            request_data: Dict containing:
                - ip: Client IP address
                - user_agent: User agent string
                - path: Requested path
                - headers: Request headers dict
                - timestamp: Request timestamp (optional)
        
        Returns:
            Tuple of (allowed: bool, reason: str, context: dict)
        """
        with self.lock:
            self.stats['total_requests'] += 1
            
            current_time = request_data.get('timestamp', time.time())
            client_ip = request_data['ip']
            user_agent = request_data.get('user_agent', '')
            path = request_data.get('path', '/')
            headers = request_data.get('headers', {})
            
            # Generate client fingerprint
            fingerprint = self._generate_fingerprint(user_agent, headers)
            
            # Get subnet (assuming IPv4 /24)
            subnet = self._get_subnet(client_ip)
            
            # 1. Check global rate limit
            if not self._check_global_limit(current_time):
                self.stats['blocked_by_global'] += 1
                return False, "global_rate_limit", {
                    'limit_type': 'global',
                    'current_rps': len(self.global_request_queue),
                    'limit_rps': self.config['global_rps']
                }
            
            # 2. Check per-IP rate limit
            if not self._check_per_ip_limit(client_ip, current_time):
                self.stats['blocked_by_ip'] += 1
                return False, "ip_rate_limit", {
                    'limit_type': 'per_ip',
                    'ip': client_ip,
                    'current_rps': len(self.per_ip_limits[client_ip]),
                    'limit_rps': self.config['per_ip_rps']
                }
            
            # 3. Check per-subnet rate limit
            if not self._check_per_subnet_limit(subnet, current_time):
                self.stats['blocked_by_subnet'] += 1
                return False, "subnet_rate_limit", {
                    'limit_type': 'per_subnet',
                    'subnet': subnet,
                    'current_rps': len(self.per_subnet_limits[subnet]),
                    'limit_rps': self.config['per_subnet_rps']
                }
            
            # 4. Check per-fingerprint rate limit
            if not self._check_per_fingerprint_limit(fingerprint, current_time):
                self.stats['blocked_by_fingerprint'] += 1
                return False, "fingerprint_rate_limit", {
                    'limit_type': 'per_fingerprint',
                    'fingerprint': fingerprint[:16] + "...",
                    'current_rps': len(self.per_fingerprint_limits[fingerprint]),
                    'limit_rps': self.config['per_fingerprint_rps']
                }
            
            # 5. Check behavior patterns
            behavior_result = self._analyze_behavior(client_ip, user_agent, path, current_time)
            if not behavior_result['allowed']:
                self.stats['blocked_by_behavior'] += 1
                return False, "suspicious_behavior", {
                    'limit_type': 'behavior',
                    'suspicion_score': behavior_result['score'],
                    'threshold': self.config['suspicious_threshold'],
                    'reasons': behavior_result['reasons']
                }
            
            # 6. Apply fair queuing if enabled
            if self.config['fair_queue_weight'] > 0:
                queue_result = self._apply_fair_queuing(client_ip, current_time)
                if not queue_result['immediate']:
                    self.stats['queued_requests'] += 1
                    return False, "fair_queue_delay", {
                        'limit_type': 'fair_queue',
                        'estimated_delay': queue_result['delay'],
                        'queue_position': queue_result['position']
                    }
            
            # Request allowed - record it
            self._record_allowed_request(client_ip, fingerprint, subnet, current_time)
            
            return True, "allowed", {
                'fingerprint': fingerprint[:16] + "...",
                'subnet': subnet,
                'behavior_score': behavior_result['score']
            }

    def _check_global_limit(self, current_time: float) -> bool:
        """Check global request rate limit"""
        window_start = current_time - self.config['window_size']
        
        # Remove old requests
        while self.global_request_queue and self.global_request_queue[0] < window_start:
            self.global_request_queue.popleft()
        
        # Check limit
        current_rps = len(self.global_request_queue)
        limit = self.config['global_rps'] * self.config['burst_allowance']
        
        return current_rps < limit

    def _check_per_ip_limit(self, ip: str, current_time: float) -> bool:
        """Check per-IP rate limit"""
        window_start = current_time - self.config['window_size']
        ip_requests = self.per_ip_limits[ip]
        
        # Remove old requests
        while ip_requests and ip_requests[0] < window_start:
            ip_requests.popleft()
        
        # Check limit
        current_rps = len(ip_requests)
        limit = self.config['per_ip_rps'] * self.config['burst_allowance']
        
        return current_rps < limit

    def _check_per_subnet_limit(self, subnet: str, current_time: float) -> bool:
        """Check per-subnet rate limit"""
        window_start = current_time - self.config['window_size']
        subnet_requests = self.per_subnet_limits[subnet]
        
        # Remove old requests
        while subnet_requests and subnet_requests[0] < window_start:
            subnet_requests.popleft()
        
        # Check limit
        current_rps = len(subnet_requests)
        limit = self.config['per_subnet_rps'] * self.config['burst_allowance']
        
        return current_rps < limit

    def _check_per_fingerprint_limit(self, fingerprint: str, current_time: float) -> bool:
        """Check per-fingerprint rate limit"""
        window_start = current_time - self.config['window_size']
        fp_requests = self.per_fingerprint_limits[fingerprint]
        
        # Remove old requests
        while fp_requests and fp_requests[0] < window_start:
            fp_requests.popleft()
        
        # Check limit
        current_rps = len(fp_requests)
        limit = self.config['per_fingerprint_rps'] * self.config['burst_allowance']
        
        return current_rps < limit

    def _analyze_behavior(self, ip: str, user_agent: str, path: str, current_time: float) -> Dict:
        """Analyze request behavior patterns for suspicion"""
        pattern = self.behavior_patterns[ip]
        
        # Update pattern data
        if pattern['last_analysis'] > 0:
            interval = current_time - pattern['last_analysis']
            pattern['request_intervals'].append(interval)
        
        pattern['user_agents'].add(user_agent)
        pattern['paths_accessed'].add(path)
        pattern['last_analysis'] = current_time
        
        # Calculate suspicion score
        score = 0.0
        reasons = []
        
        # 1. Check request timing patterns
        if len(pattern['request_intervals']) >= 5:
            intervals = list(pattern['request_intervals'])
            avg_interval = sum(intervals) / len(intervals)
            variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)
            
            # EXTREMELY regular intervals are suspicious (variance < 0.05)
            # AND very fast requests (< 1 second) indicate automated behavior
            if variance < 0.05 and avg_interval < 1.0:
                score += 0.2  # Reduced from 0.3
                reasons.append("robotic_timing")
            
            # Very fast requests are suspicious (< 0.3 seconds between requests)
            if avg_interval < 0.3:
                score += 0.2
                reasons.append("fast_requests")
        
        # 2. Check user agent diversity
        if len(pattern['user_agents']) > 5:
            score += 0.2
            reasons.append("multiple_user_agents")
        elif len(pattern['user_agents']) == 1 and len(pattern['paths_accessed']) > 10:
            score += 0.1
            reasons.append("single_ua_many_paths")
        
        # 3. Check path access patterns
        if len(pattern['paths_accessed']) > 20:
            score += 0.2
            reasons.append("path_scanning")
        
        # 4. Check for common bot signatures
        bot_indicators = ['bot', 'crawler', 'spider', 'scraper', 'curl', 'wget']
        if any(indicator in user_agent.lower() for indicator in bot_indicators):
            score += 0.15
            reasons.append("bot_user_agent")
        
        # 5. Legitimate browser behavior bonus
        # Reduce suspicion for realistic browser patterns
        legitimate_indicators = ['mozilla', 'chrome', 'safari', 'firefox', 'edge']
        if any(indicator in user_agent.lower() for indicator in legitimate_indicators):
            # Accessing common web resources indicates legitimate browsing
            common_paths = ['/', '/index.html', '/favicon.ico', '/robots.txt', '/sitemap.xml', '/health.html']
            if any(common_path in path for common_path in common_paths):
                score = max(0, score - 0.15)  # Reduce suspicion for legitimate patterns
        
        # 6. Check for missing common headers (in real implementation)
        # This would analyze the headers dict for typical browser headers
        
        pattern['suspicious_score'] = score
        
        return {
            'allowed': score < self.config['suspicious_threshold'],
            'score': round(score, 3),
            'reasons': reasons
        }

    def _apply_fair_queuing(self, ip: str, current_time: float) -> Dict:
        """Apply fair queuing to prevent IP dominance"""
        # This is a simplified fair queuing implementation
        # In production, you'd use more sophisticated algorithms like WFQ
        
        queue = self.per_ip_queues[ip]
        weight = self.config['fair_queue_weight']
        
        # Simple implementation: if IP has many recent requests, add delay
        if len(queue) > 5:
            estimated_delay = len(queue) * weight * 0.1  # 100ms per queued request
            return {
                'immediate': False,
                'delay': estimated_delay,
                'position': len(queue)
            }
        
        return {'immediate': True, 'delay': 0, 'position': 0}

    def _record_allowed_request(self, ip: str, fingerprint: str, subnet: str, current_time: float):
        """Record an allowed request in all tracking systems"""
        # Record in rate limiting systems
        self.global_request_queue.append(current_time)
        self.per_ip_limits[ip].append(current_time)
        self.per_subnet_limits[subnet].append(current_time)
        self.per_fingerprint_limits[fingerprint].append(current_time)
        
        # Update fair queuing
        self.per_ip_queues[ip].append(current_time)

    def _generate_fingerprint(self, user_agent: str, headers: Dict) -> str:
        """Generate a browser/client fingerprint"""
        # Combine various header elements for fingerprinting
        fingerprint_data = {
            'user_agent': user_agent,
            'accept': headers.get('Accept', ''),
            'accept_language': headers.get('Accept-Language', ''),
            'accept_encoding': headers.get('Accept-Encoding', ''),
            'connection': headers.get('Connection', ''),
            'dnt': headers.get('DNT', ''),
            'upgrade_insecure': headers.get('Upgrade-Insecure-Requests', '')
        }
        
        # Create hash of combined data
        combined = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.sha256(combined.encode()).hexdigest()

    def _get_subnet(self, ip: str) -> str:
        """Get /24 subnet for an IP address"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            if ip_obj.version == 4:
                # IPv4: return /24 subnet
                network = ipaddress.ip_network(f"{ip}/24", strict=False)
                return str(network.network_address) + "/24"
            else:
                # IPv6: return /64 subnet
                network = ipaddress.ip_network(f"{ip}/64", strict=False)
                return str(network.network_address) + "/64"
        except:
            # Fallback for invalid IPs
            return "unknown"

    def get_statistics(self) -> Dict:
        """Get current rate limiting statistics"""
        with self.lock:
            # Update active counts
            current_time = time.time()
            window_start = current_time - self.config['window_size']
            
            active_ips = sum(1 for ip_queue in self.per_ip_limits.values() 
                           if ip_queue and ip_queue[-1] > window_start)
            active_subnets = sum(1 for subnet_queue in self.per_subnet_limits.values() 
                               if subnet_queue and subnet_queue[-1] > window_start)
            
            self.stats.update({
                'active_ips': active_ips,
                'active_subnets': active_subnets,
                'current_global_rps': len(self.global_request_queue)
            })
            
            return self.stats.copy()

    def get_detailed_status(self) -> Dict:
        """Get detailed status for monitoring dashboard"""
        with self.lock:
            current_time = time.time()
            
            # Get top IPs by request count
            top_ips = []
            for ip, requests in list(self.per_ip_limits.items())[:10]:
                if requests:
                    recent_count = len(requests)
                    behavior = self.behavior_patterns.get(ip, {})
                    top_ips.append({
                        'ip': ip,
                        'requests': recent_count,
                        'suspicious_score': behavior.get('suspicious_score', 0),
                        'user_agents': len(behavior.get('user_agents', set())),
                        'paths': len(behavior.get('paths_accessed', set()))
                    })
            
            top_ips.sort(key=lambda x: x['requests'], reverse=True)
            
            # Get top subnets
            top_subnets = []
            for subnet, requests in list(self.per_subnet_limits.items())[:10]:
                if requests:
                    top_subnets.append({
                        'subnet': subnet,
                        'requests': len(requests)
                    })
            
            top_subnets.sort(key=lambda x: x['requests'], reverse=True)
            
            return {
                'config': self.config,
                'statistics': self.get_statistics(),
                'top_ips': top_ips[:5],
                'top_subnets': top_subnets[:5],
                'rate_limits': {
                    'global_current': len(self.global_request_queue),
                    'global_limit': self.config['global_rps'],
                    'per_ip_limit': self.config['per_ip_rps'],
                    'per_subnet_limit': self.config['per_subnet_rps'],
                    'per_fingerprint_limit': self.config['per_fingerprint_rps']
                },
                'timestamp': current_time
            }

    def update_config(self, new_config: Dict):
        """Update rate limiting configuration"""
        with self.lock:
            self.config.update(new_config)
            print(f"🔧 Rate limiter config updated: {new_config}")

    def reset_statistics(self):
        """Reset all statistics (for testing)"""
        with self.lock:
            self.stats = {key: 0 for key in self.stats}
            print("📊 Rate limiter statistics reset")

    def cleanup_old_data(self):
        """Clean up old tracking data to prevent memory leaks"""
        with self.lock:
            current_time = time.time()
            cutoff_time = current_time - (self.config['window_size'] * 2)  # Keep 2x window
            
            # Clean up empty or very old data
            for ip in list(self.per_ip_limits.keys()):
                if not self.per_ip_limits[ip] or self.per_ip_limits[ip][-1] < cutoff_time:
                    del self.per_ip_limits[ip]
                    if ip in self.per_ip_queues:
                        del self.per_ip_queues[ip]
                    if ip in self.behavior_patterns:
                        del self.behavior_patterns[ip]
            
            # Similar cleanup for other data structures
            for subnet in list(self.per_subnet_limits.keys()):
                if not self.per_subnet_limits[subnet] or self.per_subnet_limits[subnet][-1] < cutoff_time:
                    del self.per_subnet_limits[subnet]
            
            for fp in list(self.per_fingerprint_limits.keys()):
                if not self.per_fingerprint_limits[fp] or self.per_fingerprint_limits[fp][-1] < cutoff_time:
                    del self.per_fingerprint_limits[fp]


# Global instance
advanced_limiter = AdvancedRateLimiter()