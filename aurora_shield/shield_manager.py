"""
Main Aurora Shield manager that coordinates all components.
"""

import logging
import time
from datetime import datetime
from aurora_shield.core.anomaly_detector import AnomalyDetector
from aurora_shield.mitigation.rate_limiter import RateLimiter
from aurora_shield.mitigation.advanced_limits import advanced_limiter
from aurora_shield.mitigation.sinkhole import sinkhole_manager, start_sinkhole_cleanup_thread
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
        
        # Start sinkhole cleanup thread
        start_sinkhole_cleanup_thread()
        
        # Request tracking
        self.total_requests = 0
        self.blocked_requests = 0
        self.allowed_requests = 0
        self.rate_limited_requests = 0
        self.sinkholed_requests = 0
        self.blackholed_requests = 0
        self.start_time = time.time()
        
        # Real-time request monitoring
        self.recent_requests = []  # Keep last 100 requests
        self.requests_per_second = 0
        self.last_request_time = time.time()
        self.request_count_last_second = 0
        self.ip_request_counts = {}  # For rate limiting visualization
        
        logger.info("Aurora Shield initialized successfully")
    
    def process_request(self, request_data):
        """
        Process an incoming request through all protection layers.
        
        Args:
            request_data (dict): Request information
            
        Returns:
            dict: Decision with allowed status and details
        """
        # DEBUG: Log every request to verify code execution
        logger.info(f"SHIELD_DEBUG: Processing request from {request_data.get('ip')} - Total reputation scores tracked: {len(self.ip_reputation.reputation_scores)}")
        
        self.total_requests += 1
        ip_address = request_data.get('ip')
        user_agent = request_data.get('user_agent', '')
        fingerprint = request_data.get('fingerprint', '')
        
        # Layer 0: Sinkhole/Blackhole Check (highest priority)
        sinkhole_check = sinkhole_manager.check_request(ip_address, fingerprint, user_agent)
        
        if sinkhole_check['action'] == 'blackhole':
            self.blocked_requests += 1
            self.blackholed_requests += 1
            
            # Record IP reputation violation for blackholed requests
            self.ip_reputation.record_violation(ip_address, 'blackholed_request', severity=30)
            
            self.elk_integration.log_event('request_blackholed', {
                'ip': ip_address,
                'reason': sinkhole_check['reason']
            })
            self._log_request_realtime(request_data, 'blackholed', f"Blackholed: {sinkhole_check['reason']}")
            return {
                'allowed': False,
                'reason': f"Blackholed: {sinkhole_check['reason']}",
                'layer': 'blackhole',
                'action': 'drop'
            }
        
        if sinkhole_check['action'] == 'sinkhole':
            self.sinkholed_requests += 1
            
            # Record IP reputation violation for sinkholed requests
            self.ip_reputation.record_violation(ip_address, 'sinkholed_request', severity=15)
            
            self.elk_integration.log_event('request_sinkholed', {
                'ip': ip_address,
                'reason': sinkhole_check['reason'],
                'response_type': sinkhole_check['response']['type']
            })
            self._log_request_realtime(request_data, 'sinkholed', f"Sinkholed: {sinkhole_check['reason']}")
            return {
                'allowed': False,
                'reason': f"Sinkholed: {sinkhole_check['reason']}",
                'layer': 'sinkhole',
                'action': 'sinkhole',
                'sinkhole_response': sinkhole_check['response']
            }
        
        if sinkhole_check['action'] == 'quarantine':
            self.blocked_requests += 1
            
            # Record IP reputation violation for quarantined requests  
            self.ip_reputation.record_violation(ip_address, 'quarantined_request', severity=25)
            
            self.elk_integration.log_event('request_quarantined', {
                'ip': ip_address,
                'reason': sinkhole_check['reason'],
                'until': sinkhole_check['until']
            })
            self._log_request_realtime(request_data, 'quarantined', f"Quarantined: {sinkhole_check['reason']}")
            return {
                'allowed': False,
                'reason': f"Quarantined: {sinkhole_check['reason']}",
                'layer': 'quarantine',
                'action': 'quarantine',
                'quarantine_response': sinkhole_check['response']
            }
        
        # Layer 1: IP Reputation Check
        reputation = self.ip_reputation.get_reputation(ip_address)
        if not reputation['allowed']:
            self.blocked_requests += 1
            
            # Auto-sinkhole IPs with zero reputation for intelligence gathering
            if reputation['score'] <= 0:
                sinkhole_manager.auto_sinkhole_zero_reputation(ip_address)
            
            # Record violation for potential sinkhole escalation
            sinkhole_manager.process_violation(ip_address, 'ip_reputation', severity=reputation.get('severity', 5))
            
            # Implement queue fairness to prevent legitimate request starvation
            sinkhole_manager.implement_queue_fairness()
            
            self.elk_integration.log_event('request_blocked', {
                'ip': ip_address,
                'reason': 'ip_reputation',
                'score': reputation['score']
            })
            self._log_request_realtime(request_data, 'blocked', f'IP reputation too low (score: {reputation["score"]})')
            return {
                'allowed': False,
                'reason': f'IP reputation too low (score: {reputation["score"]})',
                'layer': 'ip_reputation'
            }
        
        # Layer 2: Advanced Multi-Key Rate Limiting
        advanced_check = advanced_limiter.check_request({
            'ip': ip_address,
            'user_agent': request_data.get('user_agent', ''),
            'path': request_data.get('path', '/'),
            'headers': request_data.get('headers', {}),
            'timestamp': time.time()
        })
        
        if not advanced_check[0]:  # advanced_check returns (allowed, reason, context)
            self.blocked_requests += 1
            self.rate_limited_requests += 1
            
            block_reason = advanced_check[1]
            block_context = advanced_check[2]
            
            self.elk_integration.log_event('request_blocked', {
                'ip': ip_address,
                'reason': f'advanced_{block_reason}',
                'context': block_context
            })
            
            # Increase reputation violation based on block type and record for sinkhole
            severity_map = {
                'global_rate_limit': 3,
                'ip_rate_limit': 5,
                'subnet_rate_limit': 8,
                'fingerprint_rate_limit': 10,
                'suspicious_behavior': 15,
                'fair_queue_delay': 2
            }
            severity = severity_map.get(block_reason, 5)
            self.ip_reputation.record_violation(ip_address, f'advanced_{block_reason}', severity=severity)
            
            # Record violation for sinkhole escalation
            sinkhole_manager.process_violation(ip_address, f'advanced_{block_reason}', severity=severity)
            
            self._log_request_realtime(request_data, 'rate-limited', f'Advanced limiting: {block_reason}')
            
            return {
                'allowed': False,
                'reason': f'Advanced rate limiting: {block_reason}',
                'layer': 'advanced_rate_limiter',
                'context': block_context
            }
        
        # Layer 3: Basic Rate Limiting (backup/legacy)
        rate_check = self.rate_limiter.allow_request(ip_address)
        if not rate_check['allowed']:
            self.blocked_requests += 1
            self.rate_limited_requests += 1
            self.elk_integration.log_event('request_blocked', {
                'ip': ip_address,
                'reason': 'basic_rate_limit'
            })
            self.ip_reputation.record_violation(ip_address, 'basic_rate_limit', severity=5)
            self._log_request_realtime(request_data, 'rate-limited', 'Basic rate limit exceeded')
            return {
                'allowed': False,
                'reason': 'Basic rate limit exceeded',
                'layer': 'basic_rate_limiter'
            }
        
        # Layer 4: Anomaly Detection (Rule-Based)
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
            self._log_request_realtime(request_data, 'blocked', 'Anomaly detected')
            return {
                'allowed': False,
                'reason': 'Anomaly detected',
                'layer': 'anomaly_detector'
            }
        
        # All checks passed
        self.allowed_requests += 1
        self.prometheus_integration.record_request(200, 0.1)
        
        # Log request for real-time monitoring
        self._log_request_realtime(request_data, 'allowed', 'Request allowed')
        
        return {
            'allowed': True,
            'ip': ip_address
        }
    
    def _log_request_realtime(self, request_data, status, reason=''):
        """Log request for real-time monitoring dashboard."""
        current_time = time.time()
        ip_address = request_data.get('ip', 'unknown')
        
        # Update requests per second calculation
        if current_time - self.last_request_time < 1:
            self.request_count_last_second += 1
        else:
            self.requests_per_second = self.request_count_last_second
            self.request_count_last_second = 1
            self.last_request_time = current_time
        
        # Update IP request counts for rate limiting visualization
        if ip_address not in self.ip_request_counts:
            self.ip_request_counts[ip_address] = 0
        self.ip_request_counts[ip_address] += 1
        
        # Log the request with timestamp
        request_log = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],  # Include milliseconds
            'timestamp_display': datetime.now().strftime('%H:%M:%S.%f')[:-3],  # For display
            'timestamp_iso': datetime.now().isoformat(),  # ISO format for JavaScript
            'ip': ip_address,
            'method': request_data.get('method', 'GET'),
            'url': request_data.get('uri', '/'),
            'user_agent': request_data.get('user_agent', ''),
            'status': status,
            'reason': reason
        }
        
        # Keep only last 100 requests for real-time display
        self.recent_requests.insert(0, request_log)
        if len(self.recent_requests) > 100:
            self.recent_requests = self.recent_requests[:100]
    
    def get_live_requests(self):
        """Get recent requests for live monitoring."""
        return {
            'requests': self.recent_requests[:20],  # Last 20 requests
            'requests_per_second': self.requests_per_second,
            'total_requests': self.total_requests,
            'blocked_count': self.blocked_requests,
            'allowed_count': self.allowed_requests,
            'rate_limited_count': self.rate_limited_requests,
            'ip_request_counts': dict(sorted(self.ip_request_counts.items(), 
                                           key=lambda x: x[1], reverse=True)[:10])
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
    
    def get_advanced_stats(self):
        """Get comprehensive statistics including advanced rate limiter and sinkhole data."""
        basic_stats = self.get_all_stats()
        advanced_stats = advanced_limiter.get_statistics()
        advanced_status = advanced_limiter.get_detailed_status()
        sinkhole_stats = sinkhole_manager.get_statistics()
        sinkhole_status = sinkhole_manager.get_detailed_status()
        
        # Calculate overall system metrics
        uptime = time.time() - self.start_time
        request_rate = self.total_requests / max(uptime, 1)
        block_rate = self.blocked_requests / max(self.total_requests, 1) * 100
        
        return {
            'overview': {
                'uptime_seconds': int(uptime),
                'total_requests': self.total_requests,
                'allowed_requests': self.allowed_requests,
                'blocked_requests': self.blocked_requests,
                'sinkholed_requests': self.sinkholed_requests,
                'blackholed_requests': self.blackholed_requests,
                'request_rate': round(request_rate, 2),
                'block_rate': round(block_rate, 2),
                'system_health': self._calculate_system_health()
            },
            'basic_protection': basic_stats,
            'advanced_protection': {
                'statistics': advanced_stats,
                'status': advanced_status,
                'active_limits': {
                    'per_ip': len([ip for ip, queue in advanced_limiter.per_ip_limits.items() if queue]),
                    'per_subnet': len([subnet for subnet, queue in advanced_limiter.per_subnet_limits.items() if queue]),
                    'per_fingerprint': len([fp for fp, queue in advanced_limiter.per_fingerprint_limits.items() if queue])
                }
            },
            'sinkhole_protection': {
                'statistics': sinkhole_stats,
                'status': sinkhole_status,
                'active_sinkholes': {
                    'total_ips': sinkhole_stats['counts']['sinkholed_ips'],
                    'total_subnets': sinkhole_stats['counts']['sinkholed_subnets'],
                    'total_blackholed': sinkhole_stats['counts']['blackholed_ips'],
                    'quarantined': sinkhole_stats['counts']['quarantined_ips']
                }
            },
            'real_time': {
                'requests_per_second': self.requests_per_second,
                'recent_requests': self.recent_requests[-20:] if self.recent_requests else [],
                'ip_activity': dict(list(self.ip_request_counts.items())[:10])  # Top 10 active IPs
            },
            'timestamp': time.time()
        }
    
    def _calculate_system_health(self):
        """Calculate overall system health score (0-100)."""
        health_factors = []
        
        # Request processing health (errors vs success)
        if self.total_requests > 0:
            success_rate = (self.allowed_requests / self.total_requests) * 100
            # Inverse block rate for health (more blocks = potential under attack)
            block_rate = (self.blocked_requests / self.total_requests) * 100
            
            # Good blocking (protecting) vs overwhelming attacks
            if block_rate < 50:  # Normal protective blocking
                health_factors.append(min(100, success_rate + (block_rate * 0.5)))
            else:  # High block rate indicates heavy attack
                health_factors.append(max(50, 100 - (block_rate - 50)))
        else:
            health_factors.append(100)  # No traffic = healthy
        
        # Component availability health
        try:
            # Test each component briefly
            component_health = 100
            if not self.rate_limiter:
                component_health -= 20
            if not self.ip_reputation:
                component_health -= 20
            if not self.anomaly_detector:
                component_health -= 20
            
            health_factors.append(component_health)
        except:
            health_factors.append(80)  # Some component issues
        
        # Memory/performance health (simplified)
        try:
            # Check if we're tracking too many IPs (memory concern)
            active_ips = len(self.ip_request_counts)
            if active_ips < 1000:
                health_factors.append(100)
            elif active_ips < 5000:
                health_factors.append(80)
            else:
                health_factors.append(60)  # Heavy load
        except:
            health_factors.append(90)
        
        return round(sum(health_factors) / len(health_factors), 1)

    def get_stats(self):
        """Get simplified statistics for dashboard."""
        all_stats = self.get_all_stats()
        return {
            'requests_per_second': self.total_requests / max((time.time() - self.start_time), 1),
            'threats_blocked': self.blocked_requests,
            'active_connections': all_stats.get('monitored_ips', 0),
            'system_health': self._calculate_system_health(),
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
            return not result.get('allowed', True)  # Return True if should block
            
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
    
    def debug_print_reputation_scores(self):
        """Debug method to print current reputation scores."""
        logger.info("=== DEBUG: Current IP Reputation Scores ===")
        if hasattr(self, 'ip_reputation') and self.ip_reputation:
            scores = self.ip_reputation.reputation_scores
            logger.info(f"Total tracked IPs: {len(scores)}")
            for ip, score in scores.items():
                violations = len(self.ip_reputation.violation_history.get(ip, []))
                logger.info(f"IP {ip}: Score={score}, Violations={violations}")
        else:
            logger.info("IP Reputation system not available")
        logger.info("=== END DEBUG REPUTATION SCORES ===")
        return len(self.ip_reputation.reputation_scores) if hasattr(self, 'ip_reputation') and self.ip_reputation else 0
