"""
IP reputation system for tracking and scoring IP addresses.
"""

import time
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class IPReputation:
    """IP reputation tracking and scoring system."""
    
    def __init__(self, config=None):
        """
        Initialize IP reputation system.
        
        Args:
            config (dict): Configuration parameters
        """
        self.config = config or {}
        self.reputation_scores = defaultdict(lambda: 100)  # Start at 100
        self.violation_history = defaultdict(list)
        self.whitelist = set()
        self.blacklist = set()
        
    def get_reputation(self, ip_address):
        """
        Get reputation score for an IP.
        
        Args:
            ip_address (str): IP address to check
            
        Returns:
            dict: Reputation information
        """
        if ip_address in self.whitelist:
            return {
                'ip': ip_address,
                'score': 100,
                'status': 'whitelisted',
                'allowed': True
            }
        
        if ip_address in self.blacklist:
            return {
                'ip': ip_address,
                'score': 0,
                'status': 'blacklisted',
                'allowed': False
            }
        
        score = self.reputation_scores[ip_address]
        return {
            'ip': ip_address,
            'score': score,
            'status': self._get_status(score),
            'allowed': score > 30
        }
    
    def _get_status(self, score):
        """Get status based on score."""
        if score >= 80:
            return 'trusted'
        elif score >= 50:
            return 'neutral'
        elif score >= 30:
            return 'suspicious'
        else:
            return 'malicious'
    
    def record_violation(self, ip_address, violation_type, severity=10):
        """
        Record a violation for an IP address.
        
        Args:
            ip_address (str): IP that violated
            violation_type (str): Type of violation
            severity (int): Severity score (1-100)
        """
        old_score = self.reputation_scores[ip_address]
        self.reputation_scores[ip_address] = max(0, self.reputation_scores[ip_address] - severity)
        new_score = self.reputation_scores[ip_address]
        
        logger.info(f"IP {ip_address} violation recorded: {violation_type} (severity: {severity}). Score: {old_score} -> {new_score}")
        
        self.violation_history[ip_address].append({
            'type': violation_type,
            'severity': severity,
            'timestamp': time.time()
        })
        
        # Let the sinkhole system handle auto-blacklisting based on violation patterns
        # Don't auto-blacklist here - let the multi-layer protection system decide
        # The sinkhole system will handle escalation based on violation history and patterns
    
    def record_good_behavior(self, ip_address, improvement=5):
        """
        Increase reputation for good behavior.
        
        Args:
            ip_address (str): IP address
            improvement (int): Points to add
        """
        self.reputation_scores[ip_address] = min(100, self.reputation_scores[ip_address] + improvement)
    
    def add_to_whitelist(self, ip_address):
        """Add IP to whitelist."""
        self.whitelist.add(ip_address)
        if ip_address in self.blacklist:
            self.blacklist.remove(ip_address)
        logger.info(f"IP {ip_address} added to whitelist")
    
    def add_to_blacklist(self, ip_address):
        """Add IP to blacklist."""
        self.blacklist.add(ip_address)
        if ip_address in self.whitelist:
            self.whitelist.remove(ip_address)
        logger.info(f"IP {ip_address} added to blacklist")
    
    def get_stats(self):
        """Get reputation system statistics."""
        return {
            'tracked_ips': len(self.reputation_scores),
            'whitelisted': len(self.whitelist),
            'blacklisted': len(self.blacklist),
            'total_violations': sum(len(v) for v in self.violation_history.values())
        }
