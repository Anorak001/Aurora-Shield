#!/usr/bin/env python3
"""
Attack simulation example.
Demonstrates the attack simulator and auto-recovery features.
"""

import logging
from aurora_shield.attack_sim.simulator import AttackSimulator
from aurora_shield.auto_recovery.recovery_manager import RecoveryManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Attack simulation example."""
    print("=" * 60)
    print("Aurora Shield - Attack Simulation Example")
    print("=" * 60)
    
    # Initialize components
    simulator = AttackSimulator()
    recovery_manager = RecoveryManager()
    
    # Simulate HTTP Flood
    print("\n1. Simulating HTTP Flood Attack...")
    result = simulator.simulate_http_flood(
        target='example.com',
        duration=5,
        requests_per_second=150
    )
    print(f"   Attack Type: {result['attack_type']}")
    print(f"   Duration: {result['duration']}s")
    print(f"   Requests Sent: {result['requests_sent']}")
    print(f"   Average Rate: {result['avg_rate']:.2f} req/s")
    print(f"   Attacking IPs: {len(result['attacking_ips'])}")
    
    # Test auto-recovery
    print("\n2. Testing Auto-Recovery...")
    metrics = {
        'cpu_usage': 85,
        'request_rate': 1500,
        'error_rate': 0.15
    }
    
    assessment = recovery_manager.assess_situation(metrics)
    print(f"   Situation: {assessment['priority']} priority")
    print(f"   Recommended Actions: {', '.join(assessment['actions'])}")
    
    # Execute recovery actions
    print("\n3. Executing Recovery Actions...")
    for action in assessment['actions']:
        result = recovery_manager.execute_recovery(action)
        print(f"   ✅ {action}: {result['success']}")
    
    # Check recovery status
    print("\n4. Recovery Status:")
    status = recovery_manager.get_status()
    print(f"   Active Servers: {len(status['active_servers'])}")
    print(f"   Current Capacity: {status['current_capacity']}/{status['max_capacity']}")
    print(f"   Recovery Actions Taken: {status['recovery_actions_taken']}")
    
    # Simulate distributed attack
    print("\n5. Simulating Distributed Attack...")
    result = simulator.simulate_distributed_attack(
        target='example.com',
        bot_count=100,
        duration=5
    )
    print(f"   Bot Count: {result['bot_count']}")
    print(f"   Total Requests: {result['total_requests']}")
    print(f"   Avg per Bot: {result['avg_requests_per_bot']:.2f}")
    
    print("\n" + "=" * 60)
    print("✅ Simulation completed successfully!")
    print("=" * 60)


if __name__ == '__main__':
    main()
