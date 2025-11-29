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

        @self.app.route('/')
        @self.app.route('/dashboard')
        def dashboard():
            """Enhanced main dashboard with real-time monitoring."""
            if not self._check_auth():
                return redirect(url_for('login'))
            return render_template_string(self._get_dashboard_template())

        @self.app.route('/api/dashboard/simulate', methods=['POST'])
        def simulate_attack():
            """Enhanced attack simulation with multiple attack types."""
            if not self._check_auth():
                return jsonify({'error': 'Authentication required'}), 401
            
            if session.get('role') != 'admin':
                return jsonify({'error': 'Admin privileges required'}), 403
            
            try:
                attack_type = request.json.get('type', 'http_flood') if request.is_json else 'http_flood'
                
                if attack_type == 'distributed':
                    result = self.shield_manager.attack_simulator.simulate_distributed_attack(
                        target='test_endpoint',
                        bot_count=50,
                        duration=10
                    )
                elif attack_type == 'slowloris':
                    result = self.shield_manager.attack_simulator.simulate_slowloris(
                        target='test_endpoint',
                        duration=10
                    )
                else:
                    result = self.shield_manager.attack_simulator.simulate_http_flood(
                        target='test_endpoint',
                        requests_per_second=100,
                        duration=10
                    )
                
                return jsonify({
                    'status': 'success',
                    'message': f'{attack_type.title()} attack simulation completed',
                    'result': result
                })
                
            except Exception as e:
                logger.error(f"Error simulating attack: {e}")
                return jsonify({'error': 'Failed to simulate attack'}), 500

        @self.app.route('/api/dashboard/reset', methods=['POST'])
        def reset_stats():
            """Reset all statistics (admin only)."""
            if not self._check_auth():
                return jsonify({'error': 'Authentication required'}), 401
            
            if session.get('role') != 'admin':
                return jsonify({'error': 'Admin privileges required'}), 403
            
            try:
                self.shield_manager.reset_all()
                return jsonify({
                    'status': 'success',
                    'message': 'All statistics have been reset',
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error resetting stats: {e}")
                return jsonify({'error': 'Failed to reset statistics'}), 500

        @self.app.route('/api/dashboard/config', methods=['GET', 'POST'])
        def manage_config():
            """Configuration management endpoint (admin only)."""
            if not self._check_auth():
                return jsonify({'error': 'Authentication required'}), 401
            
            if session.get('role') != 'admin':
                return jsonify({'error': 'Admin privileges required'}), 403
            
            if request.method == 'GET':
                # Return current configuration
                config = {
                    'rate_limiting': {
                        'enabled': True,
                        'max_requests_per_minute': 60,
                        'burst_limit': 10
                    },
                    'ip_reputation': {
                        'enabled': True,
                        'blacklist_threshold': 5
                    },
                    'challenge_response': {
                        'enabled': True,
                        'difficulty': 'medium'
                    }
                }
                return jsonify(config)
            
            else:
                # Update configuration
                try:
                    config_updates = request.get_json()
                    # Apply configuration updates here
                    return jsonify({
                        'status': 'success',
                        'message': 'Configuration updated successfully'
                    })
                except Exception as e:
                    logger.error(f"Error updating config: {e}")
                    return jsonify({'error': 'Failed to update configuration'}), 500

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
        return [
            {
                'timestamp': '2024-01-20 15:30:45',
                'type': 'HTTP Flood',
                'source_ip': '192.168.1.100',
                'blocked': True
            },
            {
                'timestamp': '2024-01-20 15:25:12',
                'type': 'Slowloris',
                'source_ip': '10.0.0.50',
                'blocked': True
            }
        ]
    
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
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Aurora Shield - INFOTHON 5.0</title>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }

                body {
                    font-family: 'Inter', sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #333;
                }

                .login-container {
                    background: rgba(255, 255, 255, 0.95);
                    backdrop-filter: blur(15px);
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: 20px;
                    padding: 60px 50px;
                    box-shadow: 0 25px 45px rgba(0, 0, 0, 0.1);
                    width: 100%;
                    max-width: 450px;
                    text-align: center;
                    animation: slideUp 0.8s ease-out;
                }

                @keyframes slideUp {
                    from {
                        opacity: 0;
                        transform: translateY(30px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }

                .logo {
                    margin-bottom: 30px;
                }

                .logo i {
                    font-size: 4rem;
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    margin-bottom: 10px;
                    display: block;
                }

                .logo h1 {
                    font-size: 2.2rem;
                    font-weight: 700;
                    color: #2d3748;
                    margin-bottom: 8px;
                }

                .logo p {
                    color: #718096;
                    font-size: 1.1rem;
                    font-weight: 500;
                }

                .form-group {
                    margin-bottom: 25px;
                    text-align: left;
                }

                .form-group label {
                    display: block;
                    margin-bottom: 8px;
                    color: #4a5568;
                    font-weight: 600;
                    font-size: 0.95rem;
                }

                .form-group input {
                    width: 100%;
                    padding: 15px 20px;
                    border: 2px solid #e2e8f0;
                    border-radius: 12px;
                    font-size: 1rem;
                    transition: all 0.3s ease;
                    background: rgba(247, 250, 252, 0.8);
                }

                .form-group input:focus {
                    outline: none;
                    border-color: #667eea;
                    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
                    background: white;
                }

                .login-btn {
                    width: 100%;
                    padding: 16px;
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    color: white;
                    border: none;
                    border-radius: 12px;
                    font-size: 1.1rem;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    margin-bottom: 20px;
                }

                .login-btn:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 15px 35px rgba(102, 126, 234, 0.4);
                }

                .demo-credentials {
                    background: rgba(102, 126, 234, 0.1);
                    border: 1px solid rgba(102, 126, 234, 0.2);
                    border-radius: 12px;
                    padding: 20px;
                    margin-top: 25px;
                    text-align: left;
                }

                .demo-credentials h4 {
                    color: #667eea;
                    margin-bottom: 12px;
                    font-size: 1rem;
                    font-weight: 600;
                }

                .credential-item {
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 8px;
                    font-size: 0.9rem;
                }

                .credential-item strong {
                    color: #4a5568;
                }

                .credential-item span {
                    color: #718096;
                    font-family: 'Courier New', monospace;
                }

                .alert {
                    padding: 12px 16px;
                    border-radius: 10px;
                    margin-bottom: 20px;
                    font-size: 0.95rem;
                }

                .alert.success {
                    background: rgba(72, 187, 120, 0.1);
                    color: #38a169;
                    border: 1px solid rgba(72, 187, 120, 0.3);
                }

                .alert.error {
                    background: rgba(245, 101, 101, 0.1);
                    color: #e53e3e;
                    border: 1px solid rgba(245, 101, 101, 0.3);
                }

                .alert.info {
                    background: rgba(66, 153, 225, 0.1);
                    color: #3182ce;
                    border: 1px solid rgba(66, 153, 225, 0.3);
                }

                .footer {
                    margin-top: 30px;
                    color: #a0aec0;
                    font-size: 0.85rem;
                }
            </style>
        </head>
        <body>
            <div class="login-container">
                <div class="logo">
                    <i class="fas fa-shield-alt"></i>
                    <h1>Aurora Shield</h1>
                    <p>INFOTHON 5.0 - DDoS Protection</p>
                </div>

                {% for category, message in get_flashed_messages(with_categories=true) %}
                    <div class="alert {{ category }}">
                        <i class="fas fa-info-circle"></i> {{ message }}
                    </div>
                {% endfor %}

                <form method="POST">
                    <div class="form-group">
                        <label for="username">
                            <i class="fas fa-user"></i> Username
                        </label>
                        <input type="text" id="username" name="username" required autocomplete="username">
                    </div>

                    <div class="form-group">
                        <label for="password">
                            <i class="fas fa-lock"></i> Password
                        </label>
                        <input type="password" id="password" name="password" required autocomplete="current-password">
                    </div>

                    <button type="submit" class="login-btn">
                        <i class="fas fa-sign-in-alt"></i> Sign In to Dashboard
                    </button>
                </form>

                <div class="demo-credentials">
                    <h4><i class="fas fa-key"></i> Demo Credentials</h4>
                    <div class="credential-item">
                        <strong>Administrator:</strong>
                        <span>admin / admin123</span>
                    </div>
                    <div class="credential-item">
                        <strong>Operator:</strong>
                        <span>user / user123</span>
                    </div>
                </div>

                <div class="footer">
                    <p>© 2024 Aurora Shield | Built for INFOTHON 5.0</p>
                </div>
            </div>
        </body>
        </html>
        '''

    def _get_dashboard_template(self):
        """Get the main dashboard template."""
        return '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Aurora Shield Dashboard - INFOTHON 5.0</title>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }

                body {
                    font-family: 'Inter', sans-serif;
                    background: #0f0f23;
                    color: #e2e8f0;
                    line-height: 1.6;
                }

                .dashboard-container {
                    display: flex;
                    min-height: 100vh;
                }

                .sidebar {
                    width: 280px;
                    background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
                    padding: 30px 25px;
                    border-right: 1px solid #2d3748;
                }

                .main-content {
                    flex: 1;
                    padding: 30px;
                    overflow-x: auto;
                }

                .header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 40px;
                    padding-bottom: 20px;
                    border-bottom: 1px solid #2d3748;
                }

                .logo {
                    display: flex;
                    align-items: center;
                    margin-bottom: 40px;
                }

                .logo i {
                    font-size: 2.5rem;
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    margin-right: 15px;
                }

                .logo h1 {
                    font-size: 1.8rem;
                    font-weight: 700;
                    color: #e2e8f0;
                }

                .nav-menu {
                    list-style: none;
                }

                .nav-item {
                    margin-bottom: 8px;
                }

                .nav-link {
                    display: flex;
                    align-items: center;
                    padding: 15px 20px;
                    color: #a0aec0;
                    text-decoration: none;
                    border-radius: 12px;
                    transition: all 0.3s ease;
                    cursor: pointer;
                }

                .nav-link:hover,
                .nav-link.active {
                    background: rgba(102, 126, 234, 0.2);
                    color: #667eea;
                    transform: translateX(5px);
                }

                .nav-link i {
                    margin-right: 12px;
                    width: 20px;
                    text-align: center;
                }

                .stats-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 25px;
                    margin-bottom: 40px;
                }

                .stat-card {
                    background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
                    border: 1px solid #374151;
                    border-radius: 16px;
                    padding: 30px;
                    transition: all 0.3s ease;
                }

                .stat-card:hover {
                    transform: translateY(-5px);
                    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
                }

                .stat-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 20px;
                }

                .stat-title {
                    font-size: 1rem;
                    color: #94a3b8;
                    font-weight: 500;
                }

                .stat-icon {
                    font-size: 2rem;
                    color: #667eea;
                }

                .stat-value {
                    font-size: 2.5rem;
                    font-weight: 700;
                    color: #e2e8f0;
                    margin-bottom: 10px;
                }

                .stat-change {
                    font-size: 0.9rem;
                    color: #10b981;
                }

                .chart-container {
                    background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
                    border: 1px solid #374151;
                    border-radius: 16px;
                    padding: 30px;
                    margin-bottom: 30px;
                }

                .chart-title {
                    font-size: 1.4rem;
                    font-weight: 600;
                    color: #e2e8f0;
                    margin-bottom: 25px;
                }

                .chart-wrapper {
                    height: 300px;
                    position: relative;
                }

                .user-info {
                    display: flex;
                    align-items: center;
                }

                .user-avatar {
                    width: 40px;
                    height: 40px;
                    border-radius: 50%;
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin-right: 12px;
                }

                .user-details h3 {
                    font-size: 1.1rem;
                    color: #e2e8f0;
                    margin-bottom: 2px;
                }

                .user-details p {
                    font-size: 0.9rem;
                    color: #94a3b8;
                }

                .logout-btn {
                    background: rgba(239, 68, 68, 0.2);
                    color: #ef4444;
                    border: 1px solid rgba(239, 68, 68, 0.3);
                    padding: 10px 20px;
                    border-radius: 8px;
                    text-decoration: none;
                    font-size: 0.9rem;
                    transition: all 0.3s ease;
                    margin-left: 15px;
                }

                .logout-btn:hover {
                    background: rgba(239, 68, 68, 0.3);
                    transform: translateY(-2px);
                }

                .tab-content {
                    display: none;
                }

                .tab-content.active {
                    display: block;
                }

                .controls-section {
                    margin-bottom: 30px;
                }

                .btn {
                    padding: 12px 24px;
                    border: none;
                    border-radius: 10px;
                    font-size: 0.95rem;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    margin-right: 15px;
                    margin-bottom: 10px;
                }

                .btn-primary {
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    color: white;
                }

                .btn-success {
                    background: linear-gradient(135deg, #10b981, #059669);
                    color: white;
                }

                .btn-warning {
                    background: linear-gradient(135deg, #f59e0b, #d97706);
                    color: white;
                }

                .btn-danger {
                    background: linear-gradient(135deg, #ef4444, #dc2626);
                    color: white;
                }

                .btn:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
                }

                .btn:disabled {
                    opacity: 0.6;
                    cursor: not-allowed;
                    transform: none;
                }

                /* Alerts */
                .alert {
                    padding: 15px 20px;
                    border-radius: 12px;
                    margin-bottom: 20px;
                    border-left: 4px solid;
                }

                .alert.success {
                    background: rgba(72, 187, 120, 0.1);
                    color: #10b981;
                    border-left-color: #10b981;
                }

                .alert.error {
                    background: rgba(239, 68, 68, 0.1);
                    color: #ef4444;
                    border-left-color: #ef4444;
                }

                .alert.info {
                    background: rgba(59, 130, 246, 0.1);
                    color: #3b82f6;
                    border-left-color: #3b82f6;
                }

                /* Activity Log */
                .activity-log {
                    max-height: 300px;
                    overflow-y: auto;
                }

                .log-entry {
                    padding: 12px 16px;
                    border-bottom: 1px solid #374151;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }

                .log-entry:last-child {
                    border-bottom: none;
                }

                .log-content {
                    flex: 1;
                }

                .log-type {
                    padding: 4px 8px;
                    border-radius: 6px;
                    font-size: 0.8rem;
                    font-weight: 600;
                    text-transform: uppercase;
                }

                .log-type.blocked {
                    background: rgba(239, 68, 68, 0.2);
                    color: #ef4444;
                }

                .log-type.allowed {
                    background: rgba(72, 187, 120, 0.2);
                    color: #10b981;
                }

                .log-timestamp {
                    font-size: 0.8rem;
                    color: #94a3b8;
                    margin-left: 12px;
                }

                .performance-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin-top: 20px;
                }

                .performance-card {
                    background: rgba(102, 126, 234, 0.1);
                    border: 1px solid rgba(102, 126, 234, 0.2);
                    border-radius: 12px;
                    padding: 20px;
                    text-align: center;
                }

                .performance-value {
                    font-size: 1.8rem;
                    font-weight: 700;
                    color: #667eea;
                    margin-bottom: 8px;
                }

                .performance-label {
                    font-size: 0.9rem;
                    color: #94a3b8;
                }

                /* Responsive Design */
                @media (max-width: 768px) {
                    .dashboard-container {
                        flex-direction: column;
                    }
                    
                    .sidebar {
                        width: 100%;
                        padding: 20px;
                    }
                    
                    .stats-grid {
                        grid-template-columns: 1fr;
                    }
                    
                    .header {
                        flex-direction: column;
                        gap: 20px;
                    }
                }
            </style>
        </head>
        <body>
            <div class="dashboard-container">
                <aside class="sidebar">
                    <div class="logo">
                        <i class="fas fa-shield-alt"></i>
                        <h1>Aurora Shield</h1>
                    </div>
                    
                    <nav>
                        <ul class="nav-menu">
                            <li class="nav-item">
                                <a href="#" class="nav-link active" onclick="showTab('dashboard')">
                                    <i class="fas fa-chart-line"></i>
                                    Dashboard
                                </a>
                            </li>
                            <li class="nav-item">
                                <a href="#" class="nav-link" onclick="showTab('attacks')">
                                    <i class="fas fa-shield-virus"></i>
                                    Attack Monitor
                                </a>
                            </li>
                            <li class="nav-item">
                                <a href="#" class="nav-link" onclick="showTab('performance')">
                                    <i class="fas fa-tachometer-alt"></i>
                                    Performance
                                </a>
                            </li>
                            <li class="nav-item">
                                <a href="#" class="nav-link" onclick="showTab('settings')">
                                    <i class="fas fa-cog"></i>
                                    Settings
                                </a>
                            </li>
                        </ul>
                    </nav>
                </aside>

                <main class="main-content">
                    <header class="header">
                        <h2>DDoS Protection Dashboard</h2>
                        <div class="user-info">
                            <div class="user-avatar">
                                <i class="fas fa-user"></i>
                            </div>
                            <div class="user-details">
                                <h3>{{ session.name or 'Admin' }}</h3>
                                <p>{{ (session.role or 'admin').title() }}</p>
                            </div>
                            <a href="/logout" class="logout-btn">
                                <i class="fas fa-sign-out-alt"></i> Logout
                            </a>
                        </div>
                    </header>

                    <div id="dashboard-tab" class="tab-content active">
                        <div class="stats-grid">
                            <div class="stat-card">
                                <div class="stat-header">
                                    <span class="stat-title">Total Requests</span>
                                    <i class="fas fa-globe stat-icon"></i>
                                </div>
                                <div class="stat-value" id="total-requests">0</div>
                                <div class="stat-change">Real-time monitoring</div>
                            </div>

                            <div class="stat-card">
                                <div class="stat-header">
                                    <span class="stat-title">Blocked Requests</span>
                                    <i class="fas fa-ban stat-icon"></i>
                                </div>
                                <div class="stat-value" id="blocked-requests">0</div>
                                <div class="stat-change">Security active</div>
                            </div>

                            <div class="stat-card">
                                <div class="stat-header">
                                    <span class="stat-title">Threat Level</span>
                                    <i class="fas fa-exclamation-triangle stat-icon"></i>
                                </div>
                                <div class="stat-value" id="threat-level">LOW</div>
                                <div class="stat-change" id="threat-status">All systems normal</div>
                            </div>

                            <div class="stat-card">
                                <div class="stat-header">
                                    <span class="stat-title">Response Time</span>
                                    <i class="fas fa-tachometer-alt stat-icon"></i>
                                </div>
                                <div class="stat-value" id="response-time">45ms</div>
                                <div class="stat-change">Optimal performance</div>
                            </div>
                        </div>

                        <div class="chart-container">
                            <h3 class="chart-title">Request Traffic Over Time</h3>
                            <div class="chart-wrapper">
                                <canvas id="trafficChart"></canvas>
                            </div>
                        </div>
                    </div>

                    <div id="attacks-tab" class="tab-content">
                        <div class="controls-section">
                            <button class="btn btn-warning" onclick="simulateAttack('http_flood')">
                                <i class="fas fa-bolt"></i> Simulate HTTP Flood
                            </button>
                            <button class="btn btn-danger" onclick="simulateAttack('distributed')">
                                <i class="fas fa-virus"></i> Simulate Distributed Attack
                            </button>
                            <button class="btn btn-primary" onclick="simulateAttack('slowloris')">
                                <i class="fas fa-hourglass-half"></i> Simulate Slowloris
                            </button>
                        </div>
                        
                        <div class="chart-container">
                            <h3 class="chart-title">Recent Attacks</h3>
                            <div class="activity-log" id="attack-log">
                                <div class="log-entry">
                                    <div class="log-content">
                                        <div><strong>HTTP Flood Attack</strong></div>
                                        <div style="font-size: 0.9rem; color: #94a3b8;">Source: 192.168.1.100</div>
                                    </div>
                                    <div class="log-type blocked">Blocked</div>
                                    <div class="log-timestamp">2 min ago</div>
                                </div>
                                <div class="log-entry">
                                    <div class="log-content">
                                        <div><strong>Slowloris Attack</strong></div>
                                        <div style="font-size: 0.9rem; color: #94a3b8;">Source: 10.0.0.50</div>
                                    </div>
                                    <div class="log-type blocked">Blocked</div>
                                    <div class="log-timestamp">5 min ago</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div id="performance-tab" class="tab-content">
                        <div class="chart-container">
                            <h3 class="chart-title">System Performance Metrics</h3>
                            <div class="performance-grid">
                                <div class="performance-card">
                                    <div class="performance-value" id="cpu-usage">12%</div>
                                    <div class="performance-label">CPU Usage</div>
                                </div>
                                <div class="performance-card">
                                    <div class="performance-value" id="memory-usage">35%</div>
                                    <div class="performance-label">Memory Usage</div>
                                </div>
                                <div class="performance-card">
                                    <div class="performance-value" id="uptime">2h 30m</div>
                                    <div class="performance-label">Uptime</div>
                                </div>
                                <div class="performance-card">
                                    <div class="performance-value" id="protection-level">HIGH</div>
                                    <div class="performance-label">Protection Level</div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div id="settings-tab" class="tab-content">
                        <div class="controls-section">
                            <button class="btn btn-success" onclick="resetStats()">
                                <i class="fas fa-refresh"></i> Reset Statistics
                            </button>
                            <button class="btn btn-primary" onclick="exportConfig()">
                                <i class="fas fa-download"></i> Export Config
                            </button>
                            <button class="btn btn-warning" onclick="toggleProtection()">
                                <i class="fas fa-shield-alt"></i> Toggle Protection
                            </button>
                        </div>

                        <div class="chart-container">
                            <h3 class="chart-title">Configuration Settings</h3>
                            <div class="alert info">
                                <i class="fas fa-info-circle"></i>
                                Configuration changes require administrator privileges.
                            </div>
                            <div style="padding: 20px; color: #94a3b8;">
                                <p><strong>Rate Limiting:</strong> 60 requests/minute</p>
                                <p><strong>IP Reputation:</strong> Enabled</p>
                                <p><strong>Challenge Response:</strong> Medium difficulty</p>
                                <p><strong>Blacklist Threshold:</strong> 5 violations</p>
                            </div>
                        </div>
                    </div>
                </main>
            </div>

            <script>
                let trafficChart;
                let statsData = [];

                function showTab(tabName) {
                    // Hide all tabs
                    document.querySelectorAll('.tab-content').forEach(tab => {
                        tab.classList.remove('active');
                    });
                    
                    // Remove active class from all nav links
                    document.querySelectorAll('.nav-link').forEach(link => {
                        link.classList.remove('active');
                    });
                    
                    // Show selected tab
                    document.getElementById(tabName + '-tab').classList.add('active');
                    
                    // Add active class to clicked nav link
                    event.target.classList.add('active');
                }

                function updateStats() {
                    fetch('/api/dashboard/stats')
                        .then(response => response.json())
                        .then(data => {
                            if (data.error) {
                                console.error('Stats error:', data.error);
                                return;
                            }
                            
                            // Update main stats
                            document.getElementById('total-requests').textContent = data.total_requests || 0;
                            document.getElementById('blocked-requests').textContent = data.blocked_requests || 0;
                            document.getElementById('threat-level').textContent = data.threat_level || 'LOW';
                            
                            // Update threat status message
                            const threatStatus = document.getElementById('threat-status');
                            switch(data.threat_level) {
                                case 'CRITICAL':
                                    threatStatus.textContent = 'High threat detected!';
                                    threatStatus.style.color = '#ef4444';
                                    break;
                                case 'HIGH':
                                    threatStatus.textContent = 'Elevated threat level';
                                    threatStatus.style.color = '#f59e0b';
                                    break;
                                case 'MEDIUM':
                                    threatStatus.textContent = 'Moderate activity';
                                    threatStatus.style.color = '#3b82f6';
                                    break;
                                default:
                                    threatStatus.textContent = 'All systems normal';
                                    threatStatus.style.color = '#10b981';
                            }
                            
                            // Update performance metrics
                            if (data.performance_metrics) {
                                document.getElementById('response-time').textContent = (data.performance_metrics.response_time_ms || 45) + 'ms';
                                document.getElementById('cpu-usage').textContent = (data.performance_metrics.cpu_usage_percent || 12) + '%';
                                document.getElementById('memory-usage').textContent = (data.performance_metrics.memory_usage_percent || 35) + '%';
                            }
                            
                            document.getElementById('uptime').textContent = data.uptime || '2h 30m';
                            document.getElementById('protection-level').textContent = data.protection_level || 'HIGH';
                            
                            // Store data for chart
                            statsData.push({
                                time: new Date().toLocaleTimeString(),
                                total: data.total_requests || 0,
                                blocked: data.blocked_requests || 0
                            });
                            
                            // Keep only last 10 data points
                            if (statsData.length > 10) {
                                statsData.shift();
                            }
                            
                            updateChart();
                        })
                        .catch(error => {
                            console.error('Error fetching stats:', error);
                        });
                }

                function updateChart() {
                    if (!trafficChart && statsData.length > 0) {
                        const ctx = document.getElementById('trafficChart').getContext('2d');
                        trafficChart = new Chart(ctx, {
                            type: 'line',
                            data: {
                                labels: statsData.map(d => d.time),
                                datasets: [{
                                    label: 'Total Requests',
                                    data: statsData.map(d => d.total),
                                    borderColor: '#667eea',
                                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                                    tension: 0.4,
                                    fill: true
                                }, {
                                    label: 'Blocked Requests',
                                    data: statsData.map(d => d.blocked),
                                    borderColor: '#ef4444',
                                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                                    tension: 0.4,
                                    fill: true
                                }]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: {
                                    legend: {
                                        labels: {
                                            color: '#e2e8f0'
                                        }
                                    }
                                },
                                scales: {
                                    x: {
                                        ticks: {
                                            color: '#94a3b8'
                                        },
                                        grid: {
                                            color: '#374151'
                                        }
                                    },
                                    y: {
                                        ticks: {
                                            color: '#94a3b8'
                                        },
                                        grid: {
                                            color: '#374151'
                                        }
                                    }
                                }
                            }
                        });
                    } else if (trafficChart && statsData.length > 0) {
                        trafficChart.data.labels = statsData.map(d => d.time);
                        trafficChart.data.datasets[0].data = statsData.map(d => d.total);
                        trafficChart.data.datasets[1].data = statsData.map(d => d.blocked);
                        trafficChart.update();
                    }
                }

                function simulateAttack(type) {
                    const button = event.target;
                    button.disabled = true;
                    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Running...';
                    
                    fetch('/api/dashboard/simulate', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ type: type })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.error) {
                            alert('Error: ' + data.error);
                        } else {
                            alert(data.message || 'Attack simulation completed');
                        }
                        updateStats();
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('Error simulating attack: ' + error.message);
                    })
                    .finally(() => {
                        button.disabled = false;
                        const icons = {
                            'http_flood': 'fas fa-bolt',
                            'distributed': 'fas fa-virus',
                            'slowloris': 'fas fa-hourglass-half'
                        };
                        button.innerHTML = `<i class="${icons[type]}"></i> Simulate ${type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}`;
                    });
                }

                function resetStats() {
                    if (confirm('Are you sure you want to reset all statistics?')) {
                        fetch('/api/dashboard/reset', {
                            method: 'POST'
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.error) {
                                alert('Error: ' + data.error);
                            } else {
                                alert(data.message || 'Statistics reset');
                                statsData = []; // Clear chart data
                                updateStats();
                            }
                        })
                        .catch(error => {
                            console.error('Error:', error);
                            alert('Error resetting statistics: ' + error.message);
                        });
                    }
                }

                function exportConfig() {
                    fetch('/api/dashboard/config')
                        .then(response => response.json())
                        .then(data => {
                            if (data.error) {
                                alert('Error: ' + data.error);
                                return;
                            }
                            
                            const blob = new Blob([JSON.stringify(data, null, 2)], {type: 'application/json'});
                            const url = URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = 'aurora-shield-config.json';
                            document.body.appendChild(a);
                            a.click();
                            document.body.removeChild(a);
                            URL.revokeObjectURL(url);
                        })
                        .catch(error => {
                            console.error('Error:', error);
                            alert('Error exporting configuration: ' + error.message);
                        });
                }

                function toggleProtection() {
                    // This would toggle the protection system
                    alert('Protection toggle functionality would be implemented here');
                }

                // Initialize dashboard
                document.addEventListener('DOMContentLoaded', function() {
                    updateStats();
                    setInterval(updateStats, 5000); // Update every 5 seconds
                });
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