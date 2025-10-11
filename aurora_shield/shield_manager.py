"""
Main Aurora Shield manager that coordinates all components.
"""

import logging
import time
from aurora_shield.core.anomaly_detector import AnomalyDetector
from aurora_shield.mitigation.rate_limiter import RateLimiter
from aurora_shield.mitigation.ip_reputation import IPReputation
from aurora_shield.mitigation.challenge_response import ChallengeResponse
from aurora_shield.auto_recovery.recovery_manager import RecoveryManager
from aurora_shield.attack_sim.simulator import AttackSimulator
from aurora_shield.integrations.elk_integration import ELKIntegration
from aurora_shield.integrations.prometheus_integration import PrometheusIntegration

logger = logging.getLogger(__name__)


class AuroraShieldManager:
    """Main manager coordinating all Aurora Shield components."""
    
    def __init__(self, config=None):
        """
        Initialize Aurora Shield manager.
        
        Args:
            config (dict): Configuration for all components
        """
        self.config = config or {}
        
        # Initialize all components
        logger.info("Initializing Aurora Shield components...")
        
        self.anomaly_detector = AnomalyDetector(self.config.get('anomaly_detector'))
        self.rate_limiter = RateLimiter(self.config.get('rate_limiter'))
        self.ip_reputation = IPReputation(self.config.get('ip_reputation'))
        self.challenge_response = ChallengeResponse(self.config.get('challenge_response'))
        self.recovery_manager = RecoveryManager(self.config.get('recovery_manager'))
        self.attack_simulator = AttackSimulator(self.config.get('attack_simulator'))
        self.elk_integration = ELKIntegration(self.config.get('elk'))
        self.prometheus_integration = PrometheusIntegration(self.config.get('prometheus'))
        
        # Request tracking
        self.total_requests = 0
        self.blocked_requests = 0
        self.start_time = time.time()
        
        logger.info("Aurora Shield initialized successfully")
    
    def process_request(self, request_data):
        """
        Process an incoming request through all protection layers.
        
        Args:
            request_data (dict): Request information
            
        Returns:
            dict: Decision with allowed status and details
        """
        self.total_requests += 1
        ip_address = request_data.get('ip')
        
        # Layer 1: IP Reputation Check
        reputation = self.ip_reputation.get_reputation(ip_address)
        if not reputation['allowed']:
            self.blocked_requests += 1
            self.elk_integration.log_event('request_blocked', {
                'ip': ip_address,
                'reason': 'ip_reputation',
                'score': reputation['score']
            })
            return {
                'allowed': False,
                'reason': 'IP reputation too low',
                'layer': 'ip_reputation'
            }
        
        # Layer 2: Rate Limiting
        rate_check = self.rate_limiter.allow_request(ip_address)
        if not rate_check['allowed']:
            self.blocked_requests += 1
            self.elk_integration.log_event('request_blocked', {
                'ip': ip_address,
                'reason': 'rate_limit'
            })
            self.ip_reputation.record_violation(ip_address, 'rate_limit', severity=5)
            return {
                'allowed': False,
                'reason': 'Rate limit exceeded',
                'layer': 'rate_limiter'
            }
        
        # Layer 3: Anomaly Detection (Rule-Based)
        anomaly_check = self.anomaly_detector.check_request(ip_address)
        if not anomaly_check['allowed']:
            self.blocked_requests += 1
            self.elk_integration.log_attack({
                'ip': ip_address,
                'type': 'anomaly_detected',
                'count': anomaly_check.get('count', 0)
            })
            self.prometheus_integration.record_attack('anomaly')
            self.ip_reputation.record_violation(ip_address, 'anomaly', severity=20)
            return {
                'allowed': False,
                'reason': 'Anomaly detected',
                'layer': 'anomaly_detector'
            }
        
        # All checks passed
        self.prometheus_integration.record_request(200, 0.1)
        return {
            'allowed': True,
            'ip': ip_address
        }
    
    def handle_attack(self, attack_data):
        """
        Handle detected attack with mitigation and recovery.
        
        Args:
            attack_data (dict): Information about the attack
            
        Returns:
            dict: Actions taken
        """
        logger.warning(f"Handling attack: {attack_data}")
        
        # Log the attack
        self.elk_integration.log_attack(attack_data)
        
        # Assess situation for recovery
        metrics = {
            'cpu_usage': attack_data.get('cpu_usage', 50),
            'request_rate': attack_data.get('request_rate', 100),
            'error_rate': attack_data.get('error_rate', 0.1)
        }
        
        assessment = self.recovery_manager.assess_situation(metrics)
        
        # Execute recovery actions
        actions_taken = []
        for action in assessment['actions']:
            result = self.recovery_manager.execute_recovery(action)
            actions_taken.append(result)
            self.elk_integration.log_recovery(result)
            self.prometheus_integration.record_mitigation(action)
        
        return {
            'attack': attack_data,
            'assessment': assessment,
            'actions_taken': actions_taken
        }
    
    def run_simulation(self):
        """Run attack simulation for testing."""
        logger.info("Running attack simulation...")
        
        result = self.attack_simulator.simulate_http_flood(
            target='test_endpoint',
            duration=10,
            requests_per_second=50
        )
        
        # Process simulated attacks
        for ip in result['attacking_ips'][:5]:
            attack_data = {
                'ip': ip,
                'type': 'http_flood',
                'request_rate': 50,
                'cpu_usage': 70,
                'error_rate': 0.1
            }
            self.handle_attack(attack_data)
        
        return {
            'status': 'completed',
            'message': f"Simulated attack with {result['requests_sent']} requests",
            'result': result
        }
    
    def get_stats(self):
        """Get simplified statistics for dashboard."""
        all_stats = self.get_all_stats()
        return {
            'requests_per_second': self.total_requests / max((time.time() - self.start_time), 1),
            'threats_blocked': self.blocked_requests,
            'active_connections': all_stats.get('monitored_ips', 0),
            'system_health': 99.9,  # Could be calculated based on component status
            'recent_attacks': []  # Could be retrieved from logs
        }
    
    def check_request(self, ip, user_agent, method, uri):
        """Check if a request should be blocked."""
        try:
            # Simple request data structure
            request_data = {
                'ip': ip,
                'user_agent': user_agent,
                'method': method,
                'uri': uri,
                'timestamp': time.time()
            }
            
            # Process through Aurora Shield
            result = self.process_request(request_data)
            return result.get('action') == 'block'
            
        except Exception as e:
            logger.error(f"Error checking request: {e}")
            return False  # Default to allow if there's an error
    
    def get_all_stats(self):
        """Get statistics from all components."""
        return {
            'anomaly_detector': self.anomaly_detector.get_statistics(),
            'rate_limiter': self.rate_limiter.get_stats(),
            'ip_reputation': self.ip_reputation.get_stats(),
            'challenge_response': self.challenge_response.get_stats(),
            'recovery_manager': self.recovery_manager.get_status(),
            'elk_integration': self.elk_integration.get_stats(),
            'prometheus_integration': self.prometheus_integration.get_stats(),
            'threats_blocked': self.blocked_requests,
            'total_requests': self.total_requests,
            'monitored_ips': self.anomaly_detector.get_statistics()['monitored_ips'],
            'uptime': time.time() - self.start_time
        }
    
    def reset_all(self):
        """Reset all components."""
        logger.info("Resetting all Aurora Shield components...")
        self.anomaly_detector.reset()
        self.rate_limiter.buckets.clear()
        self.ip_reputation.reputation_scores.clear()
        self.ip_reputation.blocked_ips.clear()
        self.total_requests = 0
        self.blocked_requests = 0
        self.start_time = time.time()
        logger.info("Reset complete")
