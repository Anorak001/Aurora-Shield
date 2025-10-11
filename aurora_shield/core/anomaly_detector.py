"""
Real-time rule-based anomaly detection engine.
Monitors traffic patterns and identifies potential DDoS attacks.
"""

import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnomalyDetector:
    """Rule-based anomaly detection for DDoS attacks."""
    
    def __init__(self, config=None):
        """
        Initialize the anomaly detector.
        
        Args:
            config (dict): Configuration parameters for detection thresholds
        """
        self.config = config or {}
        self.request_window = self.config.get('request_window', 60)  # seconds
        self.rate_threshold = self.config.get('rate_threshold', 100)  # requests per window
        self.ip_requests = defaultdict(lambda: deque())
        self.blocked_ips = set()
        self.anomaly_log = []
        
    def check_request(self, ip_address, timestamp=None):
        """
        Check if a request from an IP is anomalous.
        
        Args:
            ip_address (str): The IP address making the request
            timestamp (float): Unix timestamp of the request
            
        Returns:
            dict: Detection result with status and details
        """
        if timestamp is None:
            timestamp = time.time()
            
        # Check if IP is already blocked
        if ip_address in self.blocked_ips:
            return {
                'allowed': False,
                'reason': 'IP blocked due to previous violations',
                'ip': ip_address
            }
        
        # Add request to tracking
        self.ip_requests[ip_address].append(timestamp)
        
        # Clean old requests outside the window
        cutoff_time = timestamp - self.request_window
        while self.ip_requests[ip_address] and self.ip_requests[ip_address][0] < cutoff_time:
            self.ip_requests[ip_address].popleft()
        
        # Check rate
        request_count = len(self.ip_requests[ip_address])
        
        if request_count > self.rate_threshold:
            self.blocked_ips.add(ip_address)
            self.log_anomaly(ip_address, request_count, timestamp)
            logger.warning(f"DDoS attack detected from {ip_address}: {request_count} requests in {self.request_window}s")
            return {
                'allowed': False,
                'reason': f'Rate limit exceeded: {request_count} requests in {self.request_window}s',
                'ip': ip_address,
                'count': request_count
            }
        
        return {
            'allowed': True,
            'ip': ip_address,
            'count': request_count
        }
    
    def log_anomaly(self, ip_address, request_count, timestamp):
        """Log detected anomaly."""
        self.anomaly_log.append({
            'ip': ip_address,
            'count': request_count,
            'timestamp': timestamp,
            'datetime': datetime.fromtimestamp(timestamp).isoformat()
        })
    
    def unblock_ip(self, ip_address):
        """Manually unblock an IP address."""
        if ip_address in self.blocked_ips:
            self.blocked_ips.remove(ip_address)
            logger.info(f"IP {ip_address} unblocked")
            return True
        return False
    
    def get_statistics(self):
        """Get current detection statistics."""
        return {
            'monitored_ips': len(self.ip_requests),
            'blocked_ips': len(self.blocked_ips),
            'total_anomalies': len(self.anomaly_log),
            'recent_anomalies': self.anomaly_log[-10:]
        }
    
    def reset(self):
        """Reset all tracking data."""
        self.ip_requests.clear()
        self.blocked_ips.clear()
        self.anomaly_log.clear()
