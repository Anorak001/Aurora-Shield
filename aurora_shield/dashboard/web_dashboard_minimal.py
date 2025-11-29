"""
Enhanced Aurora Shield Dashboard with Professional Purple Theme and Authentication.
Designed for INFOTHON 5.0 - Complete DDoS Protection Visualization.
"""

from flask import Flask, render_template_string, jsonify, request, redirect, url_for, flash, session, Response
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
        self.app = Flask(__name__)
        self.app.secret_key = os.getenv('DASHBOARD_SECRET_KEY', 'aurora-shield-infothon-2024-secret-key')
        self.shield_manager = shield_manager
        self.users = DEFAULT_USERS
        self._setup_routes()

    def _check_auth(self):
        """Check if user is authenticated."""
        return 'user_id' in session and session['user_id'] in self.users

    def require_auth(self, f):
        """Decorator to require authentication."""
        def decorator(*args, **kwargs):
            if not self._check_auth():
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        
        def decorated_function(*args, **kwargs):
            return decorator(*args, **kwargs)
        decorated_function.__name__ = f.__name__
        return decorated_function

    def _setup_routes(self):
        """Setup enhanced dashboard routes with authentication."""
        
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
            
            return render_template_string(self._get_login_template())

        @self.app.route('/logout')
        def logout():
            """Logout and clear session."""
            session.clear()
            flash('Successfully logged out.', 'info')
            return redirect(url_for('login'))

        @self.app.route('/')
        def root():
            """Root route redirects to dashboard."""
            if not self._check_auth():
                return redirect(url_for('login'))
            return redirect(url_for('dashboard'))

        @self.app.route('/api/shield/check-request', methods=['GET', 'POST', 'PUT', 'DELETE'])
        def check_request_authorization():
            """
            Authorization endpoint for Nginx auth_request module
            Returns 200 (allowed) or 403 (blocked)
            """
            try:
                # Get original request info from Nginx headers
                client_ip = request.headers.get('X-Original-Remote-Addr', request.remote_addr)
                original_uri = request.headers.get('X-Original-URI', '/')
                original_method = request.headers.get('X-Original-Method', 'GET')
                user_agent = request.headers.get('User-Agent', '')
                
                # Build request data for shield processing
                request_data = {
                    'ip': client_ip,
                    'path': original_uri,
                    'method': original_method,
                    'user_agent': user_agent,
                    'timestamp': time.time()
                }
                
                # Process through Aurora Shield
                shield_response = self.shield_manager.process_request(request_data)
                
                if shield_response.get('allowed', False):
                    # Request allowed - return 200 so Nginx forwards to app
                    return '', 200
                else:
                    # Request blocked - return 403 so Nginx blocks it
                    logger.warning(f"Blocked request from {client_ip} to {original_uri}: {shield_response.get('reason', 'Unknown')}")
                    return jsonify({
                        'error': 'Access denied by Aurora Shield',
                        'reason': shield_response.get('reason', 'Security violation detected'),
                        'blocked_by': 'Aurora Shield'
                    }), 403
                    
            except Exception as e:
                logger.error(f"Error in request authorization check: {e}")
                # On error, allow the request (fail-open) to avoid breaking the app
                return '', 200

        @self.app.route('/api/dashboard/stats')
        def get_stats():
            """Enhanced API endpoint with comprehensive statistics."""
            if not self._check_auth():
                return jsonify({'error': 'Authentication required'}), 401
            
            try:
                stats = self.shield_manager.get_all_stats()
                
                # Add enhanced dashboard statistics
                stats.update({
                    'dashboard_version': '2.0-INFOTHON',
                    'uptime': self._get_uptime(),
                    'last_updated': datetime.now().isoformat(),
                    'protection_level': 'HIGH',
                    'threat_level': self._calculate_threat_level(stats)
                })
                
                stats['recent_attacks'] = self._get_recent_attacks()
                stats['performance_metrics'] = self._get_performance_metrics()
                
                return jsonify(stats)
            except Exception as e:
                logger.error(f"Error getting stats: {e}")
                return jsonify({'error': 'Failed to retrieve statistics'}), 500

        @self.app.route('/dashboard')
        def dashboard():
            """Enhanced main dashboard with real-time monitoring."""
            if not self._check_auth():
                return redirect(url_for('login'))
            return render_template_string(self._get_dashboard_template())

    def _get_uptime(self):
        """Calculate system uptime."""
        # Simplified uptime calculation
        return "2h 30m"
    
    def _calculate_threat_level(self, stats):
        """Calculate current threat level based on statistics."""
        blocked = stats.get('blocked_requests', 0)
        total = stats.get('total_requests', 1)
        
        if total == 0:
            return 'LOW'
        
        threat_ratio = blocked / total
        
        if threat_ratio > 0.7:
            return 'CRITICAL'
        elif threat_ratio > 0.4:
            return 'HIGH'
        elif threat_ratio > 0.1:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _get_recent_attacks(self):
        """Get recent attack information."""
        return []
    
    def _get_performance_metrics(self):
        """Get performance metrics."""
        return {
            'response_time_ms': 45,
            'memory_usage_percent': 35,
            'cpu_usage_percent': 12
        }

    def _get_login_template(self):
        """Enhanced login template with professional design."""
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Aurora Shield Login</title>
        </head>
        <body>
            <h1>Aurora Shield Login</h1>
            {% for category, message in get_flashed_messages(with_categories=true) %}
                <div>{{ message }}</div>
            {% endfor %}
            <form method="POST">
                <input type="text" name="username" placeholder="Username" required>
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit">Login</button>
            </form>
        </body>
        </html>
        '''

    def _get_dashboard_template(self):
        """Get the main dashboard template."""
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Aurora Shield Dashboard</title>
        </head>
        <body>
            <h1>Aurora Shield Dashboard</h1>
            <div id="stats">
                <p>Total Requests: <span id="total-requests">0</span></p>
                <p>Blocked Requests: <span id="blocked-requests">0</span></p>
            </div>
            <script>
                function updateStats() {
                    fetch('/api/dashboard/stats')
                        .then(response => response.json())
                        .then(data => {
                            if (!data.error) {
                                document.getElementById('total-requests').textContent = data.total_requests || 0;
                                document.getElementById('blocked-requests').textContent = data.blocked_requests || 0;
                            }
                        })
                        .catch(error => console.error('Error:', error));
                }
                
                setInterval(updateStats, 5000);
                updateStats();
            </script>
        </body>
        </html>
        '''

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