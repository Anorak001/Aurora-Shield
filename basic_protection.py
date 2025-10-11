#!/usr/bin/env python3
"""
Basic Aurora Shield protection example.
Demonstrates how to use the core protection features.
"""

import logging
from aurora_shield.core.anomaly_detector import AnomalyDetector
from aurora_shield.mitigation.rate_limiter import RateLimiter
from aurora_shield.mitigation.ip_reputation import IPReputation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Basic protection example."""
    print("=" * 60)
    print("Aurora Shield - Basic Protection Example")
    print("=" * 60)
    
    # Initialize protection layers
    detector = AnomalyDetector({'rate_threshold': 50})
    limiter = RateLimiter({'rate': 10, 'burst': 20})
    reputation = IPReputation()
    
    # Simulate some normal traffic
    print("\n1. Testing normal traffic...")
    for i in range(5):
        ip = f"192.168.1.{i}"
        result = detector.check_request(ip)
        print(f"   IP {ip}: {'✅ ALLOWED' if result['allowed'] else '❌ BLOCKED'}")
    
    # Simulate attack from single IP
    print("\n2. Simulating attack from single IP...")
    attack_ip = "10.0.0.100"
    for i in range(120):
        result = detector.check_request(attack_ip)
    
    print(f"   After 120 requests from {attack_ip}:")
    print(f"   Status: {'❌ BLOCKED (DDoS detected!)' if not result['allowed'] else '✅ ALLOWED'}")
    
    # Check statistics
    print("\n3. Protection Statistics:")
    stats = detector.get_statistics()
    print(f"   Monitored IPs: {stats['monitored_ips']}")
    print(f"   Blocked IPs: {stats['blocked_ips']}")
    print(f"   Total Anomalies: {stats['total_anomalies']}")
    
    # Test rate limiting
    print("\n4. Testing rate limiting...")
    test_ip = "192.168.1.100"
    allowed = 0
    blocked = 0
    for i in range(30):
        result = limiter.allow_request(test_ip)
        if result['allowed']:
            allowed += 1
        else:
            blocked += 1
    
    print(f"   Allowed: {allowed}, Blocked: {blocked}")
    
    # Test IP reputation
    print("\n5. Testing IP reputation system...")
    good_ip = "192.168.1.200"
    bad_ip = "10.0.0.200"
    
    # Record violations
    for i in range(5):
        reputation.record_violation(bad_ip, 'anomaly', severity=15)
    
    print(f"   Good IP reputation: {reputation.get_reputation(good_ip)['score']}")
    print(f"   Bad IP reputation: {reputation.get_reputation(bad_ip)['score']}")
    print(f"   Bad IP status: {reputation.get_reputation(bad_ip)['status']}")
    
    print("\n" + "=" * 60)
    print("✅ Example completed successfully!")
    print("=" * 60)


if __name__ == '__main__':
    main()
