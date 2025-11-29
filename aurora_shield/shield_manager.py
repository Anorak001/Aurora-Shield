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
        path = request_data.get('path', request_data.get('uri', '/'))  # Handle both 'path' and 'uri'
        
        # LEGITIMATE USER BYPASS: Check for legitimate bot patterns
        # This allows our legitimate bots to bypass all protection layers while still being counted
        if self._is_legitimate_user(user_agent, path, ip_address):
            self.allowed_requests += 1
            self.prometheus_integration.record_request(200, 0.1)
            self._log_request_realtime(request_data, 'allowed', 'Legitimate user bypass')
            
            # Still log to ELK but mark as legitimate
            self.elk_integration.log_event('request_allowed', {
                'ip': ip_address,
                'reason': 'legitimate_user_bypass',
                'user_agent': user_agent,
                'path': path
            })
            
            return {
                'allowed': True,
                'ip': ip_address,
                'reason': 'Legitimate user bypass',
                'layer': 'bypass'
            }
        
        # Layer 0: Sinkhole/Blackhole Check (only for already flagged IPs)
        sinkhole_check = sinkhole_manager.check_request(ip_address, fingerprint, user_agent)
        
        # Only process if already in blackhole/sinkhole/quarantine lists
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

        # Layer 1: IP Reputation Check - Smart Response Based on Score
        reputation = self.ip_reputation.get_reputation(ip_address)
        if not reputation['allowed']:
            self.blocked_requests += 1
            
            # Smart response based on reputation score and attack pattern
            score = reputation['score']
            violation_type = self._classify_attack_type(request_data, reputation)
            
            # Record violation with appropriate severity
            severity = self._calculate_violation_severity(violation_type, score)
            self.ip_reputation.record_violation(ip_address, violation_type, severity=severity)
            
            # Decide response based on attack type and score
            response = self._determine_response_strategy(ip_address, violation_type, score, severity)
            
            if response['action'] == 'blackhole':
                sinkhole_manager.add_to_blackhole(ip_address, 'ip', response['reason'])
                self.blackholed_requests += 1
                self._log_request_realtime(request_data, 'blackholed', response['reason'])
                return {
                    'allowed': False,
                    'reason': response['reason'],
                    'layer': 'blackhole_escalation',
                    'action': 'drop'
                }
            elif response['action'] == 'sinkhole':
                sinkhole_manager.add_to_sinkhole(ip_address, 'ip', response['reason'])
                self.sinkholed_requests += 1
                self._log_request_realtime(request_data, 'sinkholed', response['reason'])
                return {
                    'allowed': False,
                    'reason': response['reason'],
                    'layer': 'sinkhole_escalation',
                    'action': 'sinkhole'
                }
            else:
                # Standard IP reputation block
                self.elk_integration.log_event('request_blocked', {
                    'ip': ip_address,
                    'reason': 'ip_reputation',
                    'score': score,
                    'violation_type': violation_type
                })
                self._log_request_realtime(request_data, 'blocked', f'IP reputation: {violation_type} (score: {score})')
                return {
                    'allowed': False,
                    'reason': f'IP reputation: {violation_type} (score: {score})',
                    'layer': 'ip_reputation'
                }
        
        # Layer 2: Advanced Multi-Key Rate Limiting with Smart Response
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
            
            # Smart response for rate limiting violations
            violation_type = self._classify_rate_limit_violation(block_reason, request_data)
            severity = self._calculate_rate_limit_severity(block_reason, block_context)
            
            self.ip_reputation.record_violation(ip_address, violation_type, severity=severity)
            
            # Determine if this should escalate to sinkhole/blackhole
            if severity >= 25:  # High severity rate limiting violations
                sinkhole_manager.process_violation(ip_address, violation_type, severity=severity)
            
            self._log_request_realtime(request_data, 'rate-limited', f'Advanced limiting: {block_reason}')
            
            return {
                'allowed': False,
                'reason': f'Rate limited: {violation_type} ({block_reason})',
                'layer': 'advanced_rate_limiter',
                'context': block_context,
                'violation_type': violation_type,
                'severity': severity
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
        
        # Layer 4: Anomaly Detection (Rule-Based) with Smart Response
        anomaly_check = self.anomaly_detector.check_request(ip_address)
        if not anomaly_check['allowed']:
            self.blocked_requests += 1
            
            # Classify anomaly type for better response
            anomaly_type = self._classify_anomaly_type(request_data, anomaly_check)
            severity = self._calculate_anomaly_severity(anomaly_type, anomaly_check)
            
            self.elk_integration.log_attack({
                'ip': ip_address,
                'type': anomaly_type,
                'count': anomaly_check.get('count', 0),
                'severity': severity
            })
            self.prometheus_integration.record_attack(anomaly_type)
            self.ip_reputation.record_violation(ip_address, anomaly_type, severity=severity)
            
            # Determine response strategy for anomalies
            if severity >= 30:  # High severity anomalies
                response = self._determine_response_strategy(ip_address, anomaly_type, 0, severity)
                if response['action'] == 'sinkhole':
                    sinkhole_manager.add_to_sinkhole(ip_address, 'ip', response['reason'])
                    self._log_request_realtime(request_data, 'sinkholed', response['reason'])
                elif response['action'] == 'blackhole':
                    sinkhole_manager.add_to_blackhole(ip_address, 'ip', response['reason'])
                    self._log_request_realtime(request_data, 'blackholed', response['reason'])
                else:
                    self._log_request_realtime(request_data, 'blocked', f'Anomaly: {anomaly_type}')
            else:
                self._log_request_realtime(request_data, 'blocked', f'Anomaly: {anomaly_type}')
            
            return {
                'allowed': False,
                'reason': f'Anomaly detected: {anomaly_type}',
                'layer': 'anomaly_detector',
                'anomaly_type': anomaly_type,
                'severity': severity
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
    
    def _classify_attack_type(self, request_data, reputation):
        """
        Classify the type of attack based on request characteristics and reputation data.
        
        Args:
            request_data (dict): Request information
            reputation (dict): IP reputation data
            
        Returns:
            str: Attack type classification
        """
        user_agent = request_data.get('user_agent', '').lower()
        path = request_data.get('path', request_data.get('uri', '/'))
        method = request_data.get('method', 'GET')
        
        # Analyze attack patterns
        if any(bot in user_agent for bot in ['bot', 'crawler', 'scanner', 'nikto', 'nessus']):
            return 'automated_scanner'
        elif 'curl' in user_agent or 'wget' in user_agent:
            return 'command_line_tool'
        elif any(sql in path.lower() for sql in ['union', 'select', 'drop', 'insert', 'update']):
            return 'sql_injection'
        elif any(xss in path.lower() for xss in ['<script', 'javascript:', 'onload=']):
            return 'xss_attempt'
        elif any(lfi in path.lower() for lfi in ['../../../', 'etc/passwd', 'windows/system32']):
            return 'directory_traversal'
        elif method == 'POST' and reputation['score'] < 20:
            return 'brute_force'
        elif reputation['score'] == 0:
            return 'zero_reputation'
        elif reputation['score'] < 30:
            return 'low_reputation'
        else:
            return 'generic_malicious'
    
    def _calculate_violation_severity(self, violation_type, reputation_score):
        """
        Calculate violation severity based on attack type and reputation score.
        
        Args:
            violation_type (str): Type of attack/violation
            reputation_score (int): Current reputation score
            
        Returns:
            int: Severity score (1-50)
        """
        # Base severity by attack type
        severity_map = {
            'sql_injection': 30,
            'xss_attempt': 25,
            'directory_traversal': 25,
            'brute_force': 20,
            'automated_scanner': 15,
            'command_line_tool': 10,
            'zero_reputation': 25,
            'low_reputation': 10,
            'generic_malicious': 5
        }
        
        base_severity = severity_map.get(violation_type, 5)
        
        # Adjust severity based on reputation score (lower score = higher severity)
        if reputation_score == 0:
            base_severity += 10
        elif reputation_score < 20:
            base_severity += 5
        
        return min(50, base_severity)
    
    def _determine_response_strategy(self, ip_address, violation_type, reputation_score, severity):
        """
        Determine the appropriate response strategy based on attack characteristics.
        
        Args:
            ip_address (str): Attacker IP
            violation_type (str): Type of attack
            reputation_score (int): Current reputation score
            severity (int): Violation severity
            
        Returns:
            dict: Response strategy with action and reason
        """
        # High-value intelligence targets (sinkhole for analysis)
        intelligence_worthy = [
            'sql_injection', 'xss_attempt', 'directory_traversal', 
            'automated_scanner', 'zero_reputation'
        ]
        
        # Volume/noise attacks (block immediately)
        volume_attacks = [
            'brute_force', 'command_line_tool'
        ]
        
        # Extremely dangerous (blackhole immediately)
        if severity >= 40 or reputation_score == 0 and violation_type in ['sql_injection', 'directory_traversal']:
            return {
                'action': 'blackhole',
                'reason': f'Critical threat: {violation_type} (severity: {severity})'
            }
        
        # Intelligence gathering (sinkhole for analysis)
        elif violation_type in intelligence_worthy and severity >= 20:
            return {
                'action': 'sinkhole',
                'reason': f'Intelligence gathering: {violation_type} (severity: {severity})'
            }
        
        # Volume attacks (standard block)
        elif violation_type in volume_attacks or severity < 15:
            return {
                'action': 'block',
                'reason': f'Volume attack blocked: {violation_type} (severity: {severity})'
            }
        
        # Default to standard block
        else:
            return {
                'action': 'block',
                'reason': f'Malicious activity blocked: {violation_type} (severity: {severity})'
            }
    
    def _classify_rate_limit_violation(self, block_reason, request_data):
        """
        Classify rate limiting violations for better categorization.
        
        Args:
            block_reason (str): Reason from advanced rate limiter
            request_data (dict): Request information
            
        Returns:
            str: Classified violation type
        """
        user_agent = request_data.get('user_agent', '').lower()
        
        # Map rate limit reasons to attack types
        if block_reason == 'suspicious_behavior':
            if 'bot' in user_agent or 'crawler' in user_agent:
                return 'automated_flooding'
            else:
                return 'behavioral_anomaly'
        elif block_reason == 'fingerprint_rate_limit':
            return 'fingerprint_flooding'
        elif block_reason == 'subnet_rate_limit':
            return 'distributed_attack'
        elif block_reason == 'ip_rate_limit':
            return 'ip_flooding'
        elif block_reason == 'global_rate_limit':
            return 'volume_attack'
        else:
            return f'rate_limit_{block_reason}'
    
    def _calculate_rate_limit_severity(self, block_reason, block_context):
        """
        Calculate severity for rate limiting violations.
        
        Args:
            block_reason (str): Reason from rate limiter
            block_context (dict): Additional context from rate limiter
            
        Returns:
            int: Severity score
        """
        # Base severity by block type
        severity_map = {
            'suspicious_behavior': 20,
            'fingerprint_rate_limit': 15,
            'subnet_rate_limit': 12,
            'ip_rate_limit': 8,
            'global_rate_limit': 5,
            'fair_queue_delay': 3
        }
        
        base_severity = severity_map.get(block_reason, 5)
        
        # Adjust based on context if available
        if block_context and isinstance(block_context, dict):
            if block_context.get('rate_exceeded_by', 0) > 10:  # Heavily exceeded
                base_severity += 5
            if block_context.get('repeated_violations', 0) > 3:  # Repeat offender
                base_severity += 7
        
        return min(50, base_severity)
    
    def _classify_anomaly_type(self, request_data, anomaly_check):
        """
        Classify the type of anomaly detected.
        
        Args:
            request_data (dict): Request information
            anomaly_check (dict): Anomaly detection result
            
        Returns:
            str: Anomaly type classification
        """
        user_agent = request_data.get('user_agent', '').lower()
        path = request_data.get('path', request_data.get('uri', '/'))
        method = request_data.get('method', 'GET')
        count = anomaly_check.get('count', 0)
        
        # Classify based on patterns
        if count > 100:
            return 'high_frequency_anomaly'
        elif any(scanner in user_agent for scanner in ['nikto', 'nessus', 'sqlmap', 'burp']):
            return 'security_scanner'
        elif method in ['PUT', 'DELETE', 'PATCH']:
            return 'unusual_method_anomaly'
        elif len(path) > 200:
            return 'suspicious_path_anomaly'
        elif count > 50:
            return 'medium_frequency_anomaly'
        else:
            return 'behavioral_anomaly'
    
    def _calculate_anomaly_severity(self, anomaly_type, anomaly_check):
        """
        Calculate severity for anomaly violations.
        
        Args:
            anomaly_type (str): Type of anomaly
            anomaly_check (dict): Anomaly detection result
            
        Returns:
            int: Severity score
        """
        count = anomaly_check.get('count', 0)
        
        # Base severity by anomaly type
        severity_map = {
            'security_scanner': 35,
            'high_frequency_anomaly': 30,
            'suspicious_path_anomaly': 25,
            'unusual_method_anomaly': 20,
            'medium_frequency_anomaly': 15,
            'behavioral_anomaly': 10
        }
        
        base_severity = severity_map.get(anomaly_type, 10)
        
        # Adjust based on frequency
        if count > 200:
            base_severity += 15
        elif count > 100:
            base_severity += 10
        elif count > 50:
            base_severity += 5
        
        return min(50, base_severity)
    
    def _is_legitimate_user(self, user_agent, path, ip_address):
        """
        Detect legitimate users that should bypass all protection layers.
        
        Args:
            user_agent (str): User agent string
            path (str): Request path
            ip_address (str): Client IP address
            
        Returns:
            bool: True if this appears to be a legitimate user that should bypass protections
        """
        # Check for legitimate browser patterns with common paths
        legitimate_indicators = [
            # Our legitimate bot user agent patterns
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]
        
        # Common legitimate paths that normal users access
        legitimate_paths = [
            '/', '/index.html', '/favicon.ico', '/robots.txt', 
            '/sitemap.xml', '/health.html', '/health'
        ]
        
        # Check if user agent matches legitimate patterns
        for indicator in legitimate_indicators:
            if indicator in user_agent:
                # Check if accessing legitimate paths
                for legit_path in legitimate_paths:
                    if legit_path in path:
                        logger.info(f"LEGITIMATE USER DETECTED: IP {ip_address}, UA: {user_agent[:50]}..., Path: {path}")
                        return True
        
        return False
    
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
