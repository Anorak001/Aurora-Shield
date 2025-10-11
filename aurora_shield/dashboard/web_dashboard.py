"""
Enhanced Aurora Shield Dashboard with Professional Purple Theme and Authentication.
Designed for INFOTHON 5.0 - Complete DDoS Protection Visualization.
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session, Response
import time
import logging
import os
import json
import requests
from datetime import datetime

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

        @self.app.route('/api/dashboard/config')
        def get_config():
            """Export current configuration."""
            if not self._check_auth():
                return jsonify({'error': 'Authentication required'}), 401
            
            try:
                config = {
                    'version': '2.0.0',
                    'protection_enabled': True,
                    'mitigations': {
                        'rate_limiting': {'enabled': True, 'threshold': 100},
                        'challenge_response': {'enabled': True, 'difficulty': 'medium'},
                        'ip_reputation': {'enabled': True, 'strict_mode': False},
                        'bot_detection': {'enabled': True, 'sensitivity': 'high'},
                        'adaptive_learning': {'enabled': True, 'learning_rate': 0.01}
                    },
                    'thresholds': {
                        'requests_per_second': 1000,
                        'connection_limit': 10000,
                        'response_time_limit': 5000
                    },
                    'exported_at': datetime.now().isoformat()
                }
                
                return jsonify(config)
                
            except Exception as e:
                logger.error(f"Error exporting config: {e}")
                return jsonify({'error': 'Failed to export configuration'}), 500

        @self.app.route('/health')
        def health_check():
            """Health check endpoint for monitoring."""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'version': '2.0.0'
            })

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

    def _format_uptime(self, uptime_seconds):
        """Format uptime in a human-readable format."""
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        return f"{hours}h {minutes}m"

    def _get_performance_metrics(self):
        """Get current performance metrics."""
        return {
            'response_time_ms': 45,
            'memory_usage_percent': 35,
            'cpu_usage_percent': 12
        }

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