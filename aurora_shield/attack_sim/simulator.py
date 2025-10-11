"""
DDoS attack simulator for testing the protection framework.
"""

import random
import time
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AttackType(Enum):
    """Types of DDoS attacks to simulate."""
    HTTP_FLOOD = "http_flood"
    SLOWLORIS = "slowloris"
    SYN_FLOOD = "syn_flood"
    UDP_FLOOD = "udp_flood"
    DISTRIBUTED = "distributed"


class AttackSimulator:
    """Simulates various types of DDoS attacks for testing."""
    
    def __init__(self, config=None):
        """
        Initialize attack simulator.
        
        Args:
            config (dict): Configuration for simulation parameters
        """
        self.config = config or {}
        self.simulation_log = []
        
    def simulate_http_flood(self, target, duration=60, requests_per_second=100):
        """
        Simulate HTTP flood attack.
        
        Args:
            target: Target endpoint
            duration (int): Attack duration in seconds
            requests_per_second (int): Request rate
            
        Returns:
            dict: Simulation results
        """
        logger.info(f"Starting HTTP flood simulation: {requests_per_second} req/s for {duration}s")
        
        start_time = time.time()
        end_time = start_time + duration
        requests_sent = 0
        
        # Generate attack traffic
        attack_ips = [f"192.168.{random.randint(1,255)}.{random.randint(1,255)}" 
                      for _ in range(10)]
        
        while time.time() < end_time:
            for _ in range(requests_per_second):
                ip = random.choice(attack_ips)
                requests_sent += 1
            time.sleep(1)
        
        result = {
            'attack_type': AttackType.HTTP_FLOOD.value,
            'duration': duration,
            'requests_sent': requests_sent,
            'avg_rate': requests_sent / duration,
            'attacking_ips': attack_ips,
            'timestamp': start_time
        }
        
        self.simulation_log.append(result)
        logger.info(f"HTTP flood simulation completed: {requests_sent} requests sent")
        
        return result
    
    def simulate_slowloris(self, target, connections=100, duration=60):
        """
        Simulate Slowloris attack (slow HTTP requests).
        
        Args:
            target: Target endpoint
            connections (int): Number of slow connections
            duration (int): Attack duration in seconds
            
        Returns:
            dict: Simulation results
        """
        logger.info(f"Starting Slowloris simulation: {connections} connections for {duration}s")
        
        start_time = time.time()
        
        # Simulate slow connections
        slow_requests = []
        for i in range(connections):
            slow_requests.append({
                'id': i,
                'started': start_time,
                'bytes_sent': random.randint(10, 100)
            })
        
        result = {
            'attack_type': AttackType.SLOWLORIS.value,
            'duration': duration,
            'connections': connections,
            'avg_bytes_per_connection': sum(r['bytes_sent'] for r in slow_requests) / connections,
            'timestamp': start_time
        }
        
        self.simulation_log.append(result)
        logger.info(f"Slowloris simulation completed: {connections} slow connections")
        
        return result
    
    def simulate_distributed_attack(self, target, bot_count=50, duration=60):
        """
        Simulate distributed DDoS attack from multiple IPs.
        
        Args:
            target: Target endpoint
            bot_count (int): Number of attacking bots
            duration (int): Attack duration in seconds
            
        Returns:
            dict: Simulation results
        """
        logger.info(f"Starting distributed attack simulation: {bot_count} bots for {duration}s")
        
        start_time = time.time()
        
        # Generate bot IPs from different subnets
        bot_ips = [f"{random.randint(1,223)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}" 
                   for _ in range(bot_count)]
        
        # Each bot sends random number of requests
        bot_activity = {}
        for bot_ip in bot_ips:
            bot_activity[bot_ip] = random.randint(50, 200)
        
        total_requests = sum(bot_activity.values())
        
        result = {
            'attack_type': AttackType.DISTRIBUTED.value,
            'duration': duration,
            'bot_count': bot_count,
            'total_requests': total_requests,
            'avg_requests_per_bot': total_requests / bot_count,
            'bot_ips': bot_ips[:10],  # Sample of IPs
            'timestamp': start_time
        }
        
        self.simulation_log.append(result)
        logger.info(f"Distributed attack simulation completed: {total_requests} total requests")
        
        return result
    
    def generate_traffic_pattern(self, pattern_type='normal', duration=60):
        """
        Generate traffic patterns for testing.
        
        Args:
            pattern_type (str): Type of pattern (normal, bursty, attack)
            duration (int): Duration in seconds
            
        Returns:
            list: Generated traffic data
        """
        traffic = []
        
        if pattern_type == 'normal':
            # Normal traffic: steady rate with slight variation
            base_rate = 10
            for i in range(duration):
                rate = base_rate + random.randint(-2, 2)
                traffic.append({
                    'timestamp': time.time() + i,
                    'requests': rate,
                    'pattern': 'normal'
                })
        
        elif pattern_type == 'bursty':
            # Bursty traffic: periodic spikes
            for i in range(duration):
                if i % 10 == 0:
                    rate = random.randint(50, 100)  # Burst
                else:
                    rate = random.randint(5, 15)  # Normal
                traffic.append({
                    'timestamp': time.time() + i,
                    'requests': rate,
                    'pattern': 'bursty'
                })
        
        elif pattern_type == 'attack':
            # Attack traffic: sustained high rate
            for i in range(duration):
                rate = random.randint(100, 200)
                traffic.append({
                    'timestamp': time.time() + i,
                    'requests': rate,
                    'pattern': 'attack'
                })
        
        return traffic
    
    def get_simulation_summary(self):
        """Get summary of all simulations."""
        return {
            'total_simulations': len(self.simulation_log),
            'attack_types': list(set(s['attack_type'] for s in self.simulation_log)),
            'simulations': self.simulation_log
        }
