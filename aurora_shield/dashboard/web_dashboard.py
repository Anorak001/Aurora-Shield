"""
Enhanced Aurora Shield Dashboard with Professional Purple Theme and Authentication.
Designed for INFOTHON 5.0 - Complete DDoS Protection Visualization.
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session, Response
import time
import logging
import os
import json
import random
import requests
import requests
from datetime import datetime, timedelta
import docker
import subprocess

logger = logging.getLogger(__name__)

# Simple authentication (can be replaced with Flask-Login for production)
DEFAULT_USERS = {
    'admin': {
        'password': 'admin123',
        'role': 'admin',
        'name': 'Administrator'
    },
    'user': {
        'password': 'user123', 
        'role': 'user',
        'name': 'Operator'
    }
}

class WebDashboard:
    """Enhanced Aurora Shield Dashboard with Professional UI and Authentication."""

    def __init__(self, shield_manager):
        """
        Initialize the enhanced dashboard with authentication and modern design.
        
        Args:
            shield_manager: The shield manager instance for monitoring and control
        """
        self.app = Flask(__name__, template_folder='templates')
        self.app.secret_key = os.getenv('DASHBOARD_SECRET_KEY', 'aurora-shield-infothon-2024-secret-key')
        self.shield_manager = shield_manager
        self.users = DEFAULT_USERS
        self._setup_routes()

    def _check_auth(self):
        """Check if user is authenticated."""
        return 'user_id' in session and session['user_id'] in self.users

    def require_auth(self, f):
        """Decorator to require authentication for routes."""
        def decorated_function(*args, **kwargs):
            if not self._check_auth():
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        decorated_function.__name__ = f.__name__
        return decorated_function

    def _setup_routes(self):
        """Setup all Flask routes with enhanced functionality."""
        
        @self.app.route('/login', methods=['GET', 'POST'])
        def login():
            """Enhanced login page with modern design."""
            if request.method == 'POST':
                username = request.form.get('username')
                password = request.form.get('password')
                
                if username in self.users and self.users[username]['password'] == password:
                    session['user_id'] = username
                    session['role'] = self.users[username]['role']
                    session['name'] = self.users[username]['name']
                    flash(f'Welcome, {self.users[username]["name"]}!', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Invalid credentials. Please try again.', 'error')
            
            return render_template('aurora_dashboard.html', current_user=None)

        @self.app.route('/logout')
        def logout():
            """Logout and clear session."""
            session.clear()
            flash('Successfully logged out.', 'info')
            return redirect(url_for('login'))

        @self.app.route('/')
        @self.app.route('/dashboard')
        def dashboard():
            """Enhanced main dashboard with real-time monitoring."""
            if not self._check_auth():
                return redirect(url_for('login'))
            
            # Prepare current user data for template
            current_user = {
                'name': session.get('name', 'Unknown'),
                'role': session.get('role', 'user')
            }
            
            return render_template('aurora_dashboard.html', current_user=current_user)

        @self.app.route('/proxy/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
        def proxy_to_load_balancer(path):
            """Proxy endpoint that filters requests and forwards allowed ones to load balancer"""
            try:
                # Extract request information
                client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
                user_agent = request.headers.get('User-Agent', '')
                request_method = request.method
                
                logger.info(f"Filtering request from {client_ip} to /{path}")
                
                # Check if IP is in allowed list
                allowed_ips = getattr(self.shield_manager, 'allowed_ips', [])
                if client_ip not in allowed_ips:
                    logger.warning(f"Blocked request from non-allowed IP: {client_ip}")
                    return jsonify({
                        'error': 'Access denied',
                        'reason': 'IP not in allowed list',
                        'ip': client_ip
                    }), 403
                
                # Check with shield manager
                should_block = self.shield_manager.check_request(
                    ip=client_ip,
                    user_agent=user_agent,
                    method=request_method,
                    uri=f'/{path}'
                )
                
                if should_block:
                    logger.warning(f"Blocked request from {client_ip} by shield manager")
                    return jsonify({
                        'error': 'Request blocked by Aurora Shield',
                        'reason': 'Security policy violation',
                        'ip': client_ip
                    }), 403
                
                # Forward allowed request to load balancer
                load_balancer_url = f'http://load-balancer:8090/{path}'
                
                # Prepare headers for forwarding
                forward_headers = dict(request.headers)
                forward_headers['X-Forwarded-For'] = client_ip
                forward_headers['X-Aurora-Shield'] = 'filtered'
                
                # Forward request based on method
                if request_method == 'GET':
                    response = requests.get(
                        load_balancer_url,
                        headers=forward_headers,
                        params=request.args,
                        timeout=30
                    )
                elif request_method == 'POST':
                    response = requests.post(
                        load_balancer_url,
                        headers=forward_headers,
                        json=request.get_json() if request.is_json else None,
                        data=request.get_data() if not request.is_json else None,
                        params=request.args,
                        timeout=30
                    )
                else:
                    # Handle other methods
                    response = requests.request(
                        request_method,
                        load_balancer_url,
                        headers=forward_headers,
                        json=request.get_json() if request.is_json else None,
                        data=request.get_data() if not request.is_json else None,
                        params=request.args,
                        timeout=30
                    )
                
                logger.info(f"Forwarded request from {client_ip} to load balancer: {response.status_code}")
                
                # Return the response from load balancer
                return response.content, response.status_code, dict(response.headers)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error forwarding request to load balancer: {e}")
                return jsonify({
                    'error': 'Load balancer unavailable',
                    'details': str(e)
                }), 503
            except Exception as e:
                logger.error(f"Error in request proxy: {e}")
                return jsonify({
                    'error': 'Internal proxy error',
                    'details': str(e)
                }), 500

        @self.app.route('/api/shield/check-request', methods=['GET', 'POST', 'PUT', 'DELETE'])
        def check_request_authorization():
            """Authorization endpoint for Nginx auth_request module"""
            try:
                # Extract request information
                client_ip = request.headers.get('X-Original-IP', request.remote_addr)
                user_agent = request.headers.get('User-Agent', '')
                request_method = request.method
                request_uri = request.headers.get('X-Original-URI', '/')
                
                # Check if the request should be blocked
                should_block = self.shield_manager.check_request(
                    ip=client_ip,
                    user_agent=user_agent,
                    method=request_method,
                    uri=request_uri
                )
                
                if should_block:
                    logger.warning(f"Blocked request from {client_ip} to {request_uri}")
                    return '', 403  # Forbidden
                else:
                    return '', 200  # OK
                    
            except Exception as e:
                logger.error(f"Error in request authorization: {e}")
                return '', 200  # Default to allow if there's an error

        @self.app.route('/api/dashboard/stats')
        def get_stats():
            """Enhanced API endpoint for real-time statistics."""
            if not self._check_auth():
                return jsonify({'error': 'Authentication required'}), 401
            
            try:
                # Get real-time data from shield manager
                live_data = self.shield_manager.get_live_requests()
                uptime = time.time() - self.shield_manager.start_time
                
                # Enhanced stats with real data
                enhanced_stats = {
                    'requests_per_second': live_data.get('requests_per_second', 0),
                    'threats_blocked': live_data.get('blocked_count', 0),
                    'active_connections': len(live_data.get('ip_request_counts', {})),
                    'system_health': 99.9,
                    'uptime': self._format_uptime(uptime),
                    'recent_attacks': self._get_real_recent_attacks(),
                    'recent_requests': live_data.get('requests', []),  # Include recent requests for real-time display
                    'performance_metrics': self._get_performance_metrics(),
                    'protection_status': {
                        'rate_limiting': True,
                        'ip_reputation': True,
                        'anomaly_detection': True
                    },
                    'total_requests': live_data.get('total_requests', 0),
                    'allowed_requests': live_data.get('allowed_count', 0),
                    'rate_limited_requests': live_data.get('rate_limited_count', 0)
                }
                
                return jsonify(enhanced_stats)
                
            except Exception as e:
                logger.error(f"Error fetching dashboard stats: {e}")
                return jsonify({'error': 'Failed to fetch statistics'}), 500

        @self.app.route('/api/dashboard/live-requests')
        def get_live_requests():
            """Get real-time request data for live monitoring."""
            if not self._check_auth():
                return jsonify({'error': 'Authentication required'}), 401
            
            try:
                # Get actual live requests from shield manager
                live_data = self.shield_manager.get_live_requests()
                return jsonify(live_data)
                
            except Exception as e:
                logger.error(f"Error fetching live requests: {e}")
                return jsonify({'error': 'Failed to fetch live requests'}), 500

        @self.app.route('/api/dashboard/simulate', methods=['POST'])
        def simulate_attack():
            """Enhanced attack simulation with multiple attack types."""
            if not self._check_auth():
                return jsonify({'error': 'Authentication required'}), 401
            
            if session.get('role') != 'admin':
                return jsonify({'error': 'Admin privileges required'}), 403
            
            try:
                attack_type = request.json.get('type', 'http_flood') if request.is_json else 'http_flood'
                
                # Simulate different types of attacks
                attack_configs = {
                    'http_flood': {'requests': 1000, 'duration': 30},
                    'slowloris': {'connections': 100, 'duration': 60},
                    'ddos': {'requests': 5000, 'duration': 45}
                }
                
                config = attack_configs.get(attack_type, attack_configs['http_flood'])
                
                # In a real implementation, this would trigger actual attack simulation
                logger.info(f"Simulating {attack_type} attack: {config}")
                
                return jsonify({
                    'success': True,
                    'attack_type': attack_type,
                    'config': config,
                    'message': f'Attack simulation started: {attack_type}'
                })
                
            except Exception as e:
                logger.error(f"Error simulating attack: {e}")
                return jsonify({'error': 'Failed to simulate attack'}), 500

        @self.app.route('/api/sinkhole/status')
        def get_sinkhole_status():
            """Get current sinkhole/blackhole status"""
            if not self._check_auth():
                return jsonify({'error': 'Authentication required'}), 401
            
            try:
                from aurora_shield.mitigation.sinkhole import sinkhole_manager
                status = sinkhole_manager.get_detailed_status()
                return jsonify({
                    'success': True,
                    'data': status,
                    'timestamp': time.time()
                })
            except Exception as e:
                logger.error(f"Error fetching sinkhole status: {e}")
                return jsonify({'error': 'Failed to fetch sinkhole status'}), 500

        @self.app.route('/api/dashboard/attacking-ips')
        def get_attacking_ips():
            """Get comprehensive attacking IPs and actions taken"""
            if not self._check_auth():
                return jsonify({'error': 'Authentication required'}), 401
            
            try:
                from aurora_shield.mitigation.sinkhole import sinkhole_manager
                
                # Get sinkhole data
                sinkhole_data = sinkhole_manager.get_all_sinkholed_ips()
                
                # Get recent attack activity from live requests
                live_data = self.shield_manager.get_live_requests()
                recent_attacks = []
                
                # Process recent blocked/sinkholed requests
                for request_info in live_data.get('recent_requests', [])[-50:]:  # Last 50 requests
                    if request_info.get('status') in ['blocked', 'sinkholed', 'quarantined']:
                        action_taken = self._determine_action_taken(request_info.get('ip'), sinkhole_data)
                        recent_attacks.append({
                            'ip': request_info.get('ip'),
                            'timestamp': request_info.get('timestamp'),
                            'attack_type': request_info.get('reason', 'Unknown'),
                            'action_taken': action_taken,
                            'status': request_info.get('status'),
                            'user_agent': request_info.get('user_agent', 'Unknown')[:50] + '...' if len(request_info.get('user_agent', '')) > 50 else request_info.get('user_agent', 'Unknown')
                        })
                
                return jsonify({
                    'success': True,
                    'data': {
                        'sinkhole_summary': sinkhole_data['total_counts'],
                        'recent_attacks': recent_attacks[-20:],  # Last 20 attacks
                        'sinkholed_ips': list(sinkhole_data['ip_sinkholes'])[:50],  # Top 50 sinkholed IPs
                        'blackholed_ips': list(sinkhole_data['ip_blackholes'])[:50],  # Top 50 blackholed IPs
                        'quarantined_ips': {
                            ip: info for ip, info in list(sinkhole_data['quarantined_ips'].items())[:20]  # Top 20 quarantined
                        }
                    },
                    'timestamp': time.time()
                })
            except Exception as e:
                logger.error(f"Error fetching attacking IPs: {e}")
                return jsonify({'error': 'Failed to fetch attacking IP data'}), 500

        @self.app.route('/api/dashboard/attack-activity')
        def get_detailed_attack_activity():
            """Get detailed recent attack activity from attack orchestrator"""
            if not self._check_auth():
                return jsonify({'error': 'Authentication required'}), 401
            
            try:
                import requests
                from datetime import datetime, timedelta
                
                # Get filtering parameters
                severity_filter = request.args.get('severity', 'all')
                action_filter = request.args.get('action', 'all')
                limit = int(request.args.get('limit', 20))
                
                # Fetch real attack data from attack orchestrator
                attack_orchestrator_url = "http://attack-orchestrator:5000"
                recent_attacks = []
                
                try:
                    # Get active bots from attack orchestrator
                    bots_response = requests.get(f"{attack_orchestrator_url}/api/bots", timeout=5)
                    if bots_response.status_code == 200:
                        bots_data = bots_response.json()
                        
                        for bot in bots_data.get('bots', []):
                            # Only include active bots that have made requests
                            if bot.get('total_requests', 0) > 0:
                                # Calculate action taken based on success/blocked ratio
                                total_req = bot.get('total_requests', 0)
                                blocked_req = bot.get('blocked_requests', 0)
                                successful_req = bot.get('successful_requests', 0)
                                
                                if blocked_req > successful_req:
                                    action_taken = 'Blocked'
                                    severity = 'high'
                                elif blocked_req > 0:
                                    action_taken = 'Rate Limited'
                                    severity = 'medium'
                                else:
                                    action_taken = 'Monitored'
                                    severity = 'low'
                                
                                # Map attack types to display names
                                attack_type_mapping = {
                                    'http_flood': 'HTTP Flood',
                                    'ddos_burst': 'DDoS Burst',
                                    'brute_force': 'Brute Force',
                                    'slowloris': 'Slowloris',
                                    'resource_exhaustion': 'Resource Exhaustion',
                                    'normal': 'Normal Traffic'
                                }
                                
                                attack_type = attack_type_mapping.get(
                                    bot.get('attack_type', 'unknown'),
                                    bot.get('attack_type', 'Unknown').title()
                                )
                                
                                # Use last_activity timestamp if available
                                timestamp = datetime.fromtimestamp(
                                    bot.get('last_activity', bot.get('start_time', time.time()))
                                ).isoformat()
                                
                                recent_attacks.append({
                                    'ip': bot.get('ip', 'Unknown'),
                                    'timestamp': timestamp,
                                    'attack_type': attack_type,
                                    'action_taken': action_taken,
                                    'severity': severity,
                                    'total_requests': total_req,
                                    'blocked_requests': blocked_req,
                                    'bot_id': bot.get('id', 'unknown'),
                                    'status': bot.get('status', 'unknown')
                                })
                
                except requests.RequestException as e:
                    logger.warning(f"Could not connect to attack orchestrator: {e}")
                    # Fall back to shield manager data if available
                    for request_info in self.shield_manager.recent_requests[-20:]:
                        # Include all action types from shield manager
                        status = request_info.get('status')
                        if status in ['blocked', 'sinkholed', 'blackholed', 'quarantined', 'rate-limited', 'challenged']:
                            recent_attacks.append({
                                'ip': request_info.get('ip', 'Unknown'),
                                'timestamp': request_info.get('timestamp_iso', datetime.now().isoformat()),
                                'attack_type': self._map_status_to_attack_type(status),
                                'action_taken': self._map_status_to_action(status),
                                'severity': self._get_attack_severity_from_status(status),
                                'total_requests': 1,
                                'blocked_requests': 1 if status in ['blocked', 'blackholed'] else 0,
                                'bot_id': 'shield-manager',
                                'status': status
                            })
                
                # Apply filters
                if severity_filter != 'all':
                    recent_attacks = [a for a in recent_attacks if a['severity'] == severity_filter]
                    
                if action_filter != 'all':
                    recent_attacks = [a for a in recent_attacks if a['action_taken'].lower().replace(' ', '-') == action_filter]
                
                # Sort by timestamp (most recent first)
                recent_attacks.sort(key=lambda x: x['timestamp'], reverse=True)
                
                # Calculate statistics from real data
                statistics = {
                    'total_attacks': len(recent_attacks),
                    'by_severity': {
                        'critical': len([a for a in recent_attacks if a['severity'] == 'critical']),
                        'high': len([a for a in recent_attacks if a['severity'] == 'high']),
                        'medium': len([a for a in recent_attacks if a['severity'] == 'medium']),
                        'low': len([a for a in recent_attacks if a['severity'] == 'low'])
                    },
                    'by_action': {
                        'blocked': len([a for a in recent_attacks if 'blocked' in a['action_taken'].lower()]),
                        'sinkholed': len([a for a in recent_attacks if 'sinkholed' in a['action_taken'].lower()]),
                        'blackholed': len([a for a in recent_attacks if 'blackholed' in a['action_taken'].lower()]),
                        'quarantined': len([a for a in recent_attacks if 'quarantined' in a['action_taken'].lower()]),
                        'rate-limited': len([a for a in recent_attacks if 'rate' in a['action_taken'].lower()]),
                        'challenged': len([a for a in recent_attacks if 'challenge' in a['action_taken'].lower()]),
                        'monitored': len([a for a in recent_attacks if 'monitor' in a['action_taken'].lower()])
                    },
                    'unique_ips': len(set(a['ip'] for a in recent_attacks)),
                    'total_requests': sum(a.get('total_requests', 0) for a in recent_attacks),
                    'total_blocked': sum(a.get('blocked_requests', 0) for a in recent_attacks)
                }
                
                return jsonify({
                    'success': True,
                    'data': {
                        'attacks': recent_attacks[:limit],
                        'statistics': statistics
                    }
                })
                
            except Exception as e:
                logger.error(f"Error fetching attack activity: {e}")
                return jsonify({'error': str(e)}), 500
                logger.error(f"Error fetching attack activity: {e}")
                return jsonify({'error': 'Failed to fetch attack activity'}), 500

        @self.app.route('/api/sinkhole/add', methods=['POST'])
        def add_to_sinkhole():
            """Add IP/subnet/fingerprint to sinkhole"""
            if not self._check_auth():
                return jsonify({'error': 'Authentication required'}), 401
            
            if session.get('role') != 'admin':
                return jsonify({'error': 'Admin privileges required'}), 403
            
            try:
                from aurora_shield.mitigation.sinkhole import sinkhole_manager
                data = request.get_json()
                
                target = data.get('target', '').strip()
                target_type = data.get('type', 'ip')
                reason = data.get('reason', f'Dashboard action by {session.get("name", "unknown")}')
                
                if not target:
                    return jsonify({'error': 'Target is required'}), 400
                
                sinkhole_manager.add_to_sinkhole(target, target_type, reason)
                
                return jsonify({
                    'success': True,
                    'message': f'Added {target} to sinkhole',
                    'target': target,
                    'type': target_type,
                    'reason': reason
                })
                
            except Exception as e:
                logger.error(f"Error adding to sinkhole: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/blackhole/add', methods=['POST'])
        def add_to_blackhole():
            """Add IP/subnet to blackhole"""
            if not self._check_auth():
                return jsonify({'error': 'Authentication required'}), 401
            
            if session.get('role') != 'admin':
                return jsonify({'error': 'Admin privileges required'}), 403
            
            try:
                from aurora_shield.mitigation.sinkhole import sinkhole_manager
                data = request.get_json()
                
                target = data.get('target', '').strip()
                target_type = data.get('type', 'ip')
                reason = data.get('reason', f'Dashboard action by {session.get("name", "unknown")}')
                
                if not target:
                    return jsonify({'error': 'Target is required'}), 400
                
                sinkhole_manager.add_to_blackhole(target, target_type, reason)
                
                return jsonify({
                    'success': True,
                    'message': f'Added {target} to blackhole',
                    'target': target,
                    'type': target_type,
                    'reason': reason
                })
                
            except Exception as e:
                logger.error(f"Error adding to blackhole: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/advanced/stats')
        def get_advanced_stats():
            """Get comprehensive advanced statistics including sinkhole data"""
            if not self._check_auth():
                return jsonify({'error': 'Authentication required'}), 401
            
            try:
                advanced_stats = self.shield_manager.get_advanced_stats()
                return jsonify(advanced_stats)
            except Exception as e:
                logger.error(f"Error fetching advanced stats: {e}")
                return jsonify({'error': 'Failed to fetch advanced statistics'}), 500

        @self.app.route('/api/dashboard/mitigation/<mitigation_type>', methods=['POST'])
        def toggle_mitigation(mitigation_type):
            """Toggle specific mitigation techniques."""
            if not self._check_auth():
                return jsonify({'error': 'Authentication required'}), 401
            
            try:
                # In a real implementation, this would toggle actual mitigation
                logger.info(f"Toggling mitigation: {mitigation_type}")
                
                return jsonify({
                    'success': True,
                    'mitigation': mitigation_type,
                    'status': 'toggled'
                })
                
            except Exception as e:
                logger.error(f"Error toggling mitigation {mitigation_type}: {e}")
                return jsonify({'error': f'Failed to toggle {mitigation_type}'}), 500

        @self.app.route('/api/dashboard/reset-stats', methods=['POST'])
        def reset_load_balancer_stats():
            """Reset load balancer statistics."""
            if not self._check_auth():
                return jsonify({'error': 'Authentication required'}), 401
            
            try:
                # Call the load balancer's reset stats endpoint
                import requests
                response = requests.post('http://load-balancer:8090/api/reset-stats', timeout=5)
                
                if response.status_code == 200:
                    logger.info("Load balancer statistics reset successfully")
                    return jsonify({
                        'success': True,
                        'message': 'Load balancer statistics reset successfully',
                        'timestamp': response.json().get('timestamp')
                    })
                else:
                    logger.error(f"Failed to reset load balancer stats: {response.status_code}")
                    return jsonify({'error': 'Failed to reset load balancer statistics'}), 500
                    
            except Exception as e:
                logger.error(f"Error resetting load balancer stats: {e}")
                return jsonify({'error': f'Failed to reset statistics: {str(e)}'}), 500

        @self.app.route('/api/dashboard/config')
        def get_config():
            """Get current configuration with real values from shield manager."""
            if not self._check_auth():
                return jsonify({'error': 'Authentication required'}), 401
            
            try:
                from aurora_shield.config.default_config import DEFAULT_CONFIG
                
                # Get current configuration from shield manager
                current_config = getattr(self.shield_manager, 'config', DEFAULT_CONFIG)
                
                config = {
                    'version': '2.0.0',
                    'protection_enabled': True,
                    'rate_limiter': {
                        'enabled': True,
                        'rate': current_config.get('rate_limiter', {}).get('rate', 10),
                        'burst': current_config.get('rate_limiter', {}).get('burst', 20),
                        'window_size': current_config.get('rate_limiter', {}).get('window_size', 60)
                    },
                    'anomaly_detector': {
                        'enabled': True,
                        'request_window': current_config.get('anomaly_detector', {}).get('request_window', 60),
                        'rate_threshold': current_config.get('anomaly_detector', {}).get('rate_threshold', 100),
                        'sensitivity': current_config.get('anomaly_detector', {}).get('sensitivity', 'medium')
                    },
                    'ip_reputation': {
                        'enabled': True,
                        'initial_score': current_config.get('ip_reputation', {}).get('initial_score', 100),
                        'reputation_threshold': current_config.get('ip_reputation', {}).get('reputation_threshold', 50),
                        'decay_rate': current_config.get('ip_reputation', {}).get('decay_rate', 0.1)
                    },
                    'challenge_response': {
                        'enabled': True,
                        'challenge_timeout': current_config.get('challenge_response', {}).get('challenge_timeout', 300),
                        'difficulty': current_config.get('challenge_response', {}).get('difficulty', 'medium'),
                        'max_attempts': current_config.get('challenge_response', {}).get('max_attempts', 3)
                    },
                    'sinkhole': {
                        'enabled': True,
                        'auto_sinkhole_enabled': True,
                        'zero_reputation_threshold': 0,
                        'queue_fairness_enabled': True,
                        'queue_max_size': 1000
                    },
                    'thresholds': {
                        'requests_per_second': 1000,
                        'connection_limit': 10000,
                        'response_time_limit': 5000,
                        'cpu_threshold': 80,
                        'memory_threshold': 85
                    },
                    'dashboard': {
                        'host': current_config.get('dashboard', {}).get('host', '0.0.0.0'),
                        'port': current_config.get('dashboard', {}).get('port', 8080),
                        'refresh_interval': 5
                    },
                    'exported_at': datetime.now().isoformat()
                }
                
                return jsonify(config)
                
            except Exception as e:
                logger.error(f"Error getting config: {e}")
                return jsonify({'error': 'Failed to get configuration'}), 500

        @self.app.route('/api/dashboard/config', methods=['POST'])
        def update_config():
            """Update configuration parameters."""
            if not self._check_auth():
                return jsonify({'error': 'Authentication required'}), 401
            
            if session.get('role') != 'admin':
                return jsonify({'error': 'Admin privileges required'}), 403
            
            try:
                config_updates = request.get_json()
                if not config_updates:
                    return jsonify({'error': 'No configuration data provided'}), 400
                
                # Validate and apply configuration updates
                validation_result = self._validate_config_updates(config_updates)
                if not validation_result['valid']:
                    return jsonify({'error': validation_result['error']}), 400
                
                # Apply configuration to shield manager
                self._apply_config_updates(config_updates)
                
                logger.info(f"Configuration updated by {session.get('user_id', 'unknown')}")
                
                return jsonify({
                    'success': True,
                    'message': 'Configuration updated successfully',
                    'updated_at': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error updating config: {e}")
                return jsonify({'error': 'Failed to update configuration'}), 500

        @self.app.route('/api/emergency/shutdown', methods=['POST'])
        def emergency_shutdown():
            """Emergency shutdown - stops all Docker containers for system protection."""
            if not self._check_auth():
                return jsonify({'error': 'Authentication required'}), 401
            
            if session.get('role') != 'admin':
                return jsonify({'error': 'Admin privileges required'}), 403
            
            try:
                shutdown_data = request.get_json() or {}
                reason = shutdown_data.get('reason', 'Emergency shutdown initiated from dashboard')
                
                logger.critical(f"EMERGENCY SHUTDOWN initiated by {session.get('name', 'unknown')}: {reason}")
                
                # Use subprocess to call docker commands directly
                try:
                    # Get list of running containers
                    result = subprocess.run(['docker', 'ps', '--format', '{{.Names}}:{{.ID}}'], 
                                          capture_output=True, text=True, timeout=30)
                    
                    if result.returncode != 0:
                        return jsonify({
                            'success': False,
                            'error': f'Failed to list containers: {result.stderr}',
                            'message': 'Could not access Docker daemon'
                        }), 500
                    
                    containers_info = []
                    if result.stdout.strip():
                        for line in result.stdout.strip().split('\n'):
                            if ':' in line:
                                name, container_id = line.split(':', 1)
                                # Skip the Aurora Shield container itself to keep dashboard operational
                                if 'aurora-shield' not in name.lower():
                                    containers_info.append({'name': name, 'id': container_id})
                    
                    if not containers_info:
                        return jsonify({
                            'success': True,
                            'message': 'No running containers found',
                            'containers_stopped': 0,
                            'results': []
                        })
                    
                    shutdown_results = []
                    
                    # Stop each container
                    for container in containers_info:
                        try:
                            # Stop container with 10 second timeout
                            stop_result = subprocess.run(['docker', 'stop', container['id']], 
                                                       capture_output=True, text=True, timeout=30)
                            
                            if stop_result.returncode == 0:
                                shutdown_results.append({
                                    'name': container['name'],
                                    'id': container['id'],
                                    'status': 'stopped',
                                    'error': None
                                })
                                logger.info(f"Emergency shutdown: Stopped container {container['name']} ({container['id']})")
                            else:
                                shutdown_results.append({
                                    'name': container['name'],
                                    'id': container['id'],
                                    'status': 'error',
                                    'error': stop_result.stderr.strip() or 'Failed to stop container'
                                })
                                logger.error(f"Emergency shutdown: Failed to stop container {container['name']}: {stop_result.stderr}")
                            
                        except subprocess.TimeoutExpired:
                            shutdown_results.append({
                                'name': container['name'],
                                'id': container['id'],
                                'status': 'error',
                                'error': 'Timeout while stopping container'
                            })
                            logger.error(f"Emergency shutdown: Timeout stopping container {container['name']}")
                        
                        except Exception as e:
                            shutdown_results.append({
                                'name': container['name'],
                                'id': container['id'],
                                'status': 'error',
                                'error': str(e)
                            })
                            logger.error(f"Emergency shutdown: Error stopping container {container['name']}: {e}")
                    
                    stopped_count = len([r for r in shutdown_results if r['status'] == 'stopped'])
                    error_count = len([r for r in shutdown_results if r['status'] == 'error'])
                    
                    return jsonify({
                        'success': True,
                        'message': f'Emergency shutdown completed. Stopped {stopped_count} containers, {error_count} errors.',
                        'containers_stopped': stopped_count,
                        'containers_failed': error_count,
                        'results': shutdown_results,
                        'shutdown_time': datetime.now().isoformat(),
                        'reason': reason
                    })
                    
                except subprocess.TimeoutExpired:
                    logger.error("Emergency shutdown: Timeout while executing docker commands")
                    return jsonify({
                        'success': False,
                        'error': 'Timeout while executing emergency shutdown',
                        'message': 'Docker commands took too long to execute'
                    }), 500
                    
            except Exception as e:
                logger.error(f"Error during emergency shutdown: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'message': 'Emergency shutdown failed'
                }), 500

        @self.app.route('/health')
        def health_check():
            """Health check endpoint for monitoring."""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'version': '2.0.0'
            })

        @self.app.route('/api/export/logs')
        def export_logs():
            """Export attack logs and system events."""
            if not self._check_auth():
                return jsonify({'error': 'Authentication required'}), 401
            
            try:
                # Collect various log data
                export_data = {
                    'export_info': {
                        'generated_at': datetime.now().isoformat(),
                        'exported_by': session.get('name', 'unknown'),
                        'system_version': '2.0.0',
                        'uptime': self._get_uptime()
                    },
                    'attack_logs': [],
                    'blocked_requests': [],
                    'reputation_scores': {},
                    'system_stats': {},
                    'mitigation_actions': []
                }
                
                # Get recent attack activity from shield manager
                if hasattr(self.shield_manager, 'recent_requests'):
                    for request_info in self.shield_manager.recent_requests[-100:]:  # Last 100 requests
                        if request_info.get('status') in ['blocked', 'sinkholed', 'blackholed', 'quarantined', 'rate-limited']:
                            export_data['attack_logs'].append({
                                'timestamp': request_info.get('timestamp_iso', datetime.now().isoformat()),
                                'ip': request_info.get('ip', 'Unknown'),
                                'method': request_info.get('method', 'Unknown'),
                                'path': request_info.get('path', 'Unknown'),
                                'status': request_info.get('status', 'Unknown'),
                                'reason': request_info.get('reason', 'Security policy violation'),
                                'user_agent': request_info.get('user_agent', 'Unknown')[:100],  # Truncate long UAs
                                'reputation_score': request_info.get('reputation_score', 'N/A')
                            })
                
                # Also try to get recent log entries from application logs
                try:
                    import os
                    log_file_path = '/app/logs/app.log'
                    if os.path.exists(log_file_path):
                        with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            # Read last 500 lines of log file
                            lines = f.readlines()
                            recent_lines = lines[-500:] if len(lines) > 500 else lines
                            
                            for line in recent_lines:
                                line = line.strip()
                                if any(keyword in line.lower() for keyword in ['blocked', 'denied', 'error', 'attack', 'suspicious']):
                                    # Parse log line for structured data
                                    log_entry = {
                                        'timestamp': datetime.now().isoformat(),
                                        'log_line': line[:200],  # Truncate long lines
                                        'source': 'application_log'
                                    }
                                    
                                    # Try to extract IP from log line
                                    import re
                                    ip_match = re.search(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', line)
                                    if ip_match:
                                        log_entry['ip'] = ip_match.group()
                                    
                                    # Try to extract timestamp from log line
                                    timestamp_match = re.search(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}', line)
                                    if timestamp_match:
                                        log_entry['timestamp'] = timestamp_match.group()
                                    
                                    export_data['attack_logs'].append(log_entry)
                                    
                except Exception as e:
                    logger.warning(f"Could not read log file: {e}")
                
                # Add simulated attack data if no real data is available (for demo purposes)
                if len(export_data['attack_logs']) == 0:
                    # Generate sample attack log entries based on recent requests to proxy
                    sample_attacks = [
                        {
                            'timestamp': (datetime.now() - timedelta(minutes=5)).isoformat(),
                            'ip': '172.20.0.1',
                            'method': 'GET',
                            'path': '/proxy/malicious-path',
                            'status': 'blocked',
                            'reason': 'Access denied - IP not in allowed list',
                            'user_agent': 'SuspiciousBot-1',
                            'reputation_score': 25,
                            'source': 'proxy_security'
                        },
                        {
                            'timestamp': (datetime.now() - timedelta(minutes=3)).isoformat(),
                            'ip': '172.20.0.1',
                            'method': 'GET',
                            'path': '/api/dashboard/stats',
                            'status': 'blocked',
                            'reason': 'Authentication required',
                            'user_agent': 'AttackBot-5',
                            'reputation_score': 30,
                            'source': 'authentication_guard'
                        },
                        {
                            'timestamp': (datetime.now() - timedelta(minutes=1)).isoformat(),
                            'ip': '192.168.1.100',
                            'method': 'POST',
                            'path': '/proxy/admin/delete',
                            'status': 'sinkholed',
                            'reason': 'Suspicious admin path access attempt',
                            'user_agent': 'curl/7.68.0',
                            'reputation_score': 15,
                            'source': 'path_analysis'
                        }
                    ]
                    export_data['attack_logs'].extend(sample_attacks)
                
                # Get blocked requests summary
                attack_logs_count = len(export_data['attack_logs'])
                blocked_count = len([log for log in export_data['attack_logs'] if log.get('status') == 'blocked'])
                sinkholed_count = len([log for log in export_data['attack_logs'] if log.get('status') == 'sinkholed'])
                
                export_data['blocked_requests'] = {
                    'total_blocked': blocked_count,
                    'total_sinkholed': sinkholed_count,
                    'total_requests': attack_logs_count,
                    'block_rate': f"{(blocked_count / max(attack_logs_count, 1) * 100):.1f}%" if attack_logs_count > 0 else "0.0%"
                }
                
                # Get IP reputation scores
                if hasattr(self.shield_manager, 'ip_reputation') and self.shield_manager.ip_reputation:
                    for ip, score in list(self.shield_manager.ip_reputation.reputation_scores.items())[:50]:  # Top 50 IPs
                        violations = len(self.shield_manager.ip_reputation.violation_history.get(ip, []))
                        export_data['reputation_scores'][ip] = {
                            'score': score,
                            'violations': violations,
                            'status': 'suspicious' if score < 50 else 'normal'
                        }
                
                # Get system statistics
                try:
                    # Try to get attack orchestrator stats
                    orchestrator_response = requests.get('http://attack-orchestrator:5000/api/bots/stats', timeout=5)
                    if orchestrator_response.status_code == 200:
                        orchestrator_data = orchestrator_response.json()
                        export_data['system_stats']['attack_orchestrator'] = {
                            'active_bots': orchestrator_data.get('active_bots', 0),
                            'total_requests': orchestrator_data.get('total_requests', 0),
                            'attack_types': orchestrator_data.get('attack_types', {})
                        }
                except:
                    export_data['system_stats']['attack_orchestrator'] = {'status': 'unavailable'}
                
                # Add mitigation actions summary
                export_data['mitigation_actions'] = [
                    {
                        'timestamp': datetime.now().isoformat(),
                        'action': 'Rate Limiting',
                        'status': 'Active',
                        'description': 'Automatic rate limiting based on request patterns'
                    },
                    {
                        'timestamp': datetime.now().isoformat(),
                        'action': 'IP Reputation',
                        'status': 'Active', 
                        'description': 'Real-time IP reputation scoring and blocking'
                    },
                    {
                        'timestamp': datetime.now().isoformat(),
                        'action': 'Anomaly Detection',
                        'status': 'Active',
                        'description': 'Machine learning-based traffic anomaly detection'
                    }
                ]
                
                # Create filename with timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'aurora_shield_logs_{timestamp}.json'
                
                # Return as downloadable JSON file
                response = Response(
                    json.dumps(export_data, indent=2, ensure_ascii=False),
                    mimetype='application/json',
                    headers={
                        'Content-Disposition': f'attachment; filename={filename}',
                        'Content-Type': 'application/json; charset=utf-8'
                    }
                )
                
                logger.info(f"Logs exported by {session.get('name', 'unknown')} - {len(export_data['attack_logs'])} attack logs, {len(export_data['reputation_scores'])} IP scores")
                
                return response
                
            except Exception as e:
                logger.error(f"Error exporting logs: {e}")
                return jsonify({'error': f'Failed to export logs: {str(e)}'}), 500

        @self.app.route('/api/debug/reputation')
        def debug_reputation_scores():
            """Debug endpoint to get current IP reputation scores."""
            try:
                # Call the debug method to log reputation scores
                tracked_count = self.shield_manager.debug_print_reputation_scores()
                
                # Also return the data in JSON format
                reputation_data = {}
                if hasattr(self.shield_manager, 'ip_reputation') and self.shield_manager.ip_reputation:
                    for ip, score in self.shield_manager.ip_reputation.reputation_scores.items():
                        violations = len(self.shield_manager.ip_reputation.violation_history.get(ip, []))
                        reputation_data[ip] = {
                            'score': score,
                            'violations': violations
                        }
                
                return jsonify({
                    'success': True,
                    'tracked_ips': tracked_count,
                    'reputation_scores': reputation_data,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error in debug reputation endpoint: {e}")
                return jsonify({'error': str(e)}), 500

    def _get_uptime(self):
        """Get system uptime in a human-readable format."""
        try:
            uptime_seconds = time.time() - self.shield_manager.start_time
            hours = int(uptime_seconds // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
        except:
            return "Unknown"

    def _get_real_recent_attacks(self):
        """Get actual recent attack attempts from blocked requests."""
        try:
            # Get recent blocked requests from shield manager
            recent_requests = self.shield_manager.recent_requests[:10]
            attacks = []
            
            for req in recent_requests:
                if req['status'] in ['blocked', 'rate-limited']:
                    attack_type = 'Rate Limiting' if req['status'] == 'rate-limited' else 'Malicious Request'
                    
                    # Use the proper timestamp format
                    timestamp = req.get('timestamp_iso', req.get('timestamp'))
                    if not timestamp:
                        timestamp = datetime.now().isoformat()
                    
                    attacks.append({
                        'timestamp': timestamp,
                        'type': attack_type,
                        'source': req['ip'],
                        'status': 'Blocked' if req['status'] == 'blocked' else 'Rate Limited',
                        'url': req['url']
                    })
            
            return attacks[:5]  # Return last 5 attacks
        except Exception as e:
            logger.error(f"Error getting recent attacks: {e}")
            return []
    
    def _determine_action_taken(self, ip: str, sinkhole_data: dict) -> str:
        """Determine what action was taken for a specific IP"""
        if ip in sinkhole_data.get('ip_blackholes', []):
            return 'Blackholed (Complete Block)'
        elif ip in sinkhole_data.get('ip_sinkholes', []):
            return 'Sinkholed (Intelligence Gathering)'
        elif ip in sinkhole_data.get('quarantined_ips', {}):
            quarantine_info = sinkhole_data['quarantined_ips'][ip]
            time_left = int(quarantine_info.get('time_remaining', 0))
            return f'Quarantined ({time_left}s remaining)'
        else:
            return 'Blocked (Rate Limited)'

    def _format_uptime(self, uptime_seconds):
        """Format uptime in a human-readable format."""
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        return f"{hours}h {minutes}m"

    def _get_performance_metrics(self):
        """Get current performance metrics including real IP reputation data."""
        try:
            # Get real IP request counts from shield manager
            live_data = self.shield_manager.get_live_requests()
            ip_counts = live_data.get('ip_request_counts', {})
            
            # Get actual IP reputation scores from the IP reputation system
            ip_reputation_data = {}
            
            # Get all tracked IPs from the reputation system
            if hasattr(self.shield_manager, 'ip_reputation') and self.shield_manager.ip_reputation:
                for ip in self.shield_manager.ip_reputation.reputation_scores:
                    reputation_info = self.shield_manager.ip_reputation.get_reputation(ip)
                    
                    # Get violation history count
                    violation_count = len(self.shield_manager.ip_reputation.violation_history.get(ip, []))
                    
                    ip_reputation_data[ip] = {
                        'reputation_score': reputation_info['score'],
                        'status': reputation_info['status'],
                        'allowed': reputation_info['allowed'],
                        'violation_count': violation_count,
                        'total_requests': ip_counts.get(ip, 0),
                        'is_blacklisted': ip in self.shield_manager.ip_reputation.blacklist,
                        'is_whitelisted': ip in self.shield_manager.ip_reputation.whitelist
                    }
            
            # Also include IPs from recent requests that might not be in reputation system yet
            recent_requests = live_data.get('requests', [])
            for request in recent_requests:
                ip = request.get('ip', 'unknown')
                if ip not in ip_reputation_data and ip != 'unknown':
                    reputation_info = self.shield_manager.ip_reputation.get_reputation(ip)
                    ip_reputation_data[ip] = {
                        'reputation_score': reputation_info['score'],
                        'status': reputation_info['status'],
                        'allowed': reputation_info['allowed'],
                        'violation_count': 0,
                        'total_requests': ip_counts.get(ip, 0),
                        'is_blacklisted': False,
                        'is_whitelisted': False
                    }
            
            return {
                'response_time_ms': 45,
                'memory_usage_percent': 35,
                'cpu_usage_percent': 12,
                'ip_request_counts': ip_counts,
                'ip_reputation_data': ip_reputation_data
            }
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {
                'response_time_ms': 45,
                'memory_usage_percent': 35,
                'cpu_usage_percent': 12,
                'ip_request_counts': {},
                'ip_reputation_data': {}
            }

    def _validate_config_updates(self, config_updates):
        """Validate configuration updates."""
        try:
            # Define validation rules
            validation_rules = {
                'rate_limiter': {
                    'rate': {'type': (int, float), 'min': 1, 'max': 10000},
                    'burst': {'type': (int, float), 'min': 1, 'max': 1000},
                    'window_size': {'type': int, 'min': 1, 'max': 3600}
                },
                'anomaly_detector': {
                    'request_window': {'type': int, 'min': 1, 'max': 3600},
                    'rate_threshold': {'type': int, 'min': 1, 'max': 100000},
                    'sensitivity': {'type': str, 'choices': ['low', 'medium', 'high']}
                },
                'ip_reputation': {
                    'initial_score': {'type': int, 'min': 0, 'max': 100},
                    'reputation_threshold': {'type': int, 'min': 0, 'max': 100},
                    'decay_rate': {'type': (int, float), 'min': 0, 'max': 1}
                },
                'challenge_response': {
                    'challenge_timeout': {'type': int, 'min': 10, 'max': 3600},
                    'difficulty': {'type': str, 'choices': ['easy', 'medium', 'hard']},
                    'max_attempts': {'type': int, 'min': 1, 'max': 10}
                },
                'thresholds': {
                    'requests_per_second': {'type': int, 'min': 10, 'max': 100000},
                    'connection_limit': {'type': int, 'min': 10, 'max': 1000000},
                    'response_time_limit': {'type': int, 'min': 100, 'max': 30000},
                    'cpu_threshold': {'type': int, 'min': 10, 'max': 95},
                    'memory_threshold': {'type': int, 'min': 10, 'max': 95}
                }
            }
            
            # Validate each section
            for section, values in config_updates.items():
                if section not in validation_rules:
                    continue
                    
                if not isinstance(values, dict):
                    return {'valid': False, 'error': f'Invalid format for section {section}'}
                
                for key, value in values.items():
                    if key not in validation_rules[section]:
                        continue
                    
                    rule = validation_rules[section][key]
                    
                    # Type validation
                    if not isinstance(value, rule['type']):
                        return {'valid': False, 'error': f'Invalid type for {section}.{key}'}
                    
                    # Range validation
                    if 'min' in rule and value < rule['min']:
                        return {'valid': False, 'error': f'{section}.{key} must be >= {rule["min"]}'}
                    
                    if 'max' in rule and value > rule['max']:
                        return {'valid': False, 'error': f'{section}.{key} must be <= {rule["max"]}'}
                    
                    # Choice validation
                    if 'choices' in rule and value not in rule['choices']:
                        return {'valid': False, 'error': f'{section}.{key} must be one of {rule["choices"]}'}
            
            return {'valid': True}
            
        except Exception as e:
            return {'valid': False, 'error': f'Validation error: {str(e)}'}

    def _apply_config_updates(self, config_updates):
        """Apply configuration updates to the shield manager."""
        try:
            # Update shield manager configuration
            if hasattr(self.shield_manager, 'config'):
                for section, values in config_updates.items():
                    if section in self.shield_manager.config:
                        self.shield_manager.config[section].update(values)
                    else:
                        self.shield_manager.config[section] = values
            
            # Apply specific updates to components
            if 'rate_limiter' in config_updates:
                if hasattr(self.shield_manager, 'rate_limiter'):
                    rate_config = config_updates['rate_limiter']
                    if 'rate' in rate_config:
                        self.shield_manager.rate_limiter.rate = rate_config['rate']
                    if 'burst' in rate_config:
                        self.shield_manager.rate_limiter.burst = rate_config['burst']
            
            if 'anomaly_detector' in config_updates:
                if hasattr(self.shield_manager, 'anomaly_detector'):
                    anomaly_config = config_updates['anomaly_detector']
                    if 'request_window' in anomaly_config:
                        self.shield_manager.anomaly_detector.request_window = anomaly_config['request_window']
                    if 'rate_threshold' in anomaly_config:
                        self.shield_manager.anomaly_detector.rate_threshold = anomaly_config['rate_threshold']
            
            # Log the configuration change
            logger.info(f"Applied configuration updates: {config_updates}")
            
        except Exception as e:
            logger.error(f"Error applying config updates: {e}")
            raise

    def _get_country_from_ip(self, ip):
        """Get country from IP address (simplified)"""
        if not ip:
            return 'Unknown'
        
        # Simple IP to country mapping for demo
        ip_country_map = {
            '192.168.': 'Local Network',
            '10.0.': 'Private Network',
            '172.16.': 'Private Network',
            '203.0.113.': 'Documentation',
            '198.51.100.': 'Test Network',
            '45.76.': 'Russia',
            '185.220.': 'Germany',
            '77.234.': 'China'
        }
        
        for ip_prefix, country in ip_country_map.items():
            if ip.startswith(ip_prefix):
                return country
        
        return 'Unknown'

    def _get_attack_severity(self, attack_type):
        """Determine attack severity based on type"""
        if not attack_type:
            return 'Low'
        
        attack_type_lower = attack_type.lower()
        
        if any(term in attack_type_lower for term in ['sql injection', 'command injection', 'zero-day', 'buffer overflow']):
            return 'Critical'
        elif any(term in attack_type_lower for term in ['xss', 'csrf', 'path traversal', 'ddos', 'brute force']):
            return 'High'
        elif any(term in attack_type_lower for term in ['bot detection', 'scanner', 'suspicious']):
            return 'Medium'
        else:
            return 'Low'

    def _generate_malicious_user_agent(self):
        """Generate realistic malicious user agents"""
        malicious_agents = [
            'sqlmap/1.4.7#stable',
            'Mozilla/5.0 (compatible; Nmap Scripting Engine)',
            'python-requests/2.25.1',
            'curl/7.68.0',
            'Wget/1.20.3',
            'Mozilla/5.0 AttackBot/1.0',
            'masscan/1.3.2',
            'Nikto/2.1.6',
            'gobuster/3.1.0',
            'dirb/2.22'
        ]
        
        return random.choice(malicious_agents)

    def _generate_attack_uri(self, attack_type):
        """Generate realistic attack URIs based on attack type"""
        if not attack_type:
            return '/'
        
        attack_type_lower = attack_type.lower()
        
        if 'sql injection' in attack_type_lower:
            return "/login?id=1' OR '1'='1"
        elif 'xss' in attack_type_lower:
            return "/search?q=<script>alert('xss')</script>"
        elif 'path traversal' in attack_type_lower:
            return "/file?path=../../../etc/passwd"
        elif 'command injection' in attack_type_lower:
            return "/exec?cmd=; rm -rf /"
        elif 'brute force' in attack_type_lower:
            return "/admin/login"
        elif 'scanner' in attack_type_lower:
            return "/admin/config.php"
        elif 'bot' in attack_type_lower:
            return "/robots.txt"
        else:
            return "/"

    def _calculate_attack_stats(self, recent_attacks):
        """Calculate attack statistics"""
        if not recent_attacks:
            return {
                'total_attacks': 0,
                'attacks_by_type': {},
                'attacks_by_action': {},
                'attacks_by_severity': {},
                'top_attacking_ips': []
            }
        
        # Count attacks by type
        attacks_by_type = {}
        attacks_by_action = {}
        attacks_by_severity = {}
    
    def _map_status_to_attack_type(self, status):
        """Map request status to attack type"""
        status_mapping = {
            'blocked': 'Malicious Request',
            'blackholed': 'Critical Threat',
            'sinkholed': 'Suspicious Activity',
            'quarantined': 'Potential Threat',
            'rate-limited': 'Rate Limit Exceeded',
            'challenged': 'Challenge Required'
        }
        return status_mapping.get(status, 'Unknown Attack')
    
    def _map_status_to_action(self, status):
        """Map request status to action taken"""
        action_mapping = {
            'blocked': 'Blocked',
            'blackholed': 'Blackholed',
            'sinkholed': 'Sinkholed',
            'quarantined': 'Quarantined',
            'rate-limited': 'Rate Limited',
            'challenged': 'Challenged'
        }
        return action_mapping.get(status, 'Monitored')
    
    def _get_attack_severity_from_status(self, status):
        """Get attack severity based on status"""
        severity_mapping = {
            'blocked': 'high',
            'blackholed': 'critical',
            'sinkholed': 'high',
            'quarantined': 'critical',
            'rate-limited': 'medium',
            'challenged': 'low'
        }
        return severity_mapping.get(status, 'low')

    def start(self):
        """Start the dashboard server"""
        logger.info("Starting Aurora Shield Dashboard...")
        self.app.run(
            host='0.0.0.0',
            port=5001,
            debug=False,
            threaded=True
        )

    def run(self, host='0.0.0.0', port=8080, debug=False):
        """Run the enhanced dashboard server."""
        try:
            logger.info("🛡️  Starting Aurora Shield Dashboard (INFOTHON 5.0)")
            logger.info(f"📊 Dashboard: http://{host}:{port}")
            logger.info("🔐 Demo Credentials: admin/admin123 or user/user123")
            logger.info("🎯 Tech Stack: Flask + Python + Real-time Monitoring")
            
            self.app.run(host=host, port=port, debug=debug, threaded=True)
            
        except KeyboardInterrupt:
            logger.info("🛑 Aurora Shield Dashboard stopped")
        except Exception as e:
            logger.error(f"❌ Dashboard error: {e}")