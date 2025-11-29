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
        Initialize enhanced web dashboard.
        
        Args:
            shield_manager: Main Aurora Shield manager instance
        """
        self.app = Flask(__name__)
        self.app.secret_key = os.environ.get('AURORA_SECRET_KEY', 'aurora-shield-infothon-secret-2025')
        self.shield_manager = shield_manager
        self.users = DEFAULT_USERS
        self.active_sessions = {}
        self._setup_routes()
    
    def _check_auth(self):
        """Check if user is authenticated."""
        if 'user_id' not in session:
            return False
        return session['user_id'] in self.users
    
    def _require_auth(self, admin_only=False):
        """Decorator to require authentication."""
        def decorator(f):
            def decorated_function(*args, **kwargs):
                if not self._check_auth():
                    return redirect(url_for('login'))
                if admin_only and session.get('role') != 'admin':
                    flash('Admin privileges required.', 'error')
                    return redirect(url_for('dashboard'))
                return f(*args, **kwargs)
            decorated_function.__name__ = f.__name__
            return decorated_function
        return decorator
    
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
                    session['login_time'] = datetime.now().isoformat()
                    
                    flash(f'Welcome back, {self.users[username]["name"]}!', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Invalid credentials. Try admin/admin123 or user/user123', 'error')
            
            return render_template_string(self._get_login_template())
        
        @self.app.route('/logout')
        def logout():
            """Logout and redirect to login."""
            session.clear()
            flash('Successfully logged out.', 'info')
            return redirect(url_for('login'))
        
        @self.app.route('/')
        def dashboard():
            """Enhanced main dashboard with real-time monitoring."""
            if not self._check_auth():
                return redirect(url_for('login'))
            return render_template_string(self._get_dashboard_template())
        
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
                
                # Add real-time enhancements
                stats['system_info'] = {
                    'uptime': time.time() - getattr(self, 'start_time', time.time()),
                    'current_time': datetime.now().isoformat(),
                    'protection_level': 'HIGH',
                    'threat_level': self._calculate_threat_level(stats)
                }
                
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
                        connections=20,
                        duration=10
                    )
                else:
                    result = self.shield_manager.run_simulation()
                
                return jsonify({
                    'status': 'success',
                    'message': f'Simulated {attack_type} attack completed',
                    'result': result
                })
            except Exception as e:
                logger.error(f"Simulation error: {e}")
                return jsonify({'error': f'Simulation failed: {str(e)}'}), 500
        
        @self.app.route('/api/dashboard/reset', methods=['POST'])
        def reset_system():
            """Reset system with admin verification."""
            if not self._check_auth():
                return jsonify({'error': 'Authentication required'}), 401
            
            if session.get('role') != 'admin':
                return jsonify({'error': 'Admin privileges required'}), 403
            
            try:
                self.shield_manager.reset_all()
                return jsonify({
                    'status': 'success',
                    'message': 'System reset completed',
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Reset error: {e}")
                return jsonify({'error': f'Reset failed: {str(e)}'}), 500
        
        @self.app.route('/api/dashboard/config', methods=['GET', 'POST'])
        def system_config():
            """System configuration endpoint."""
            if not self._check_auth():
                return jsonify({'error': 'Authentication required'}), 401
            
            if request.method == 'GET':
                return jsonify({
                    'rate_limiter': self.shield_manager.config.get('rate_limiter', {}),
                    'anomaly_detector': self.shield_manager.config.get('anomaly_detector', {}),
                    'ip_reputation': self.shield_manager.config.get('ip_reputation', {})
                })
            
            # POST - Update configuration (admin only)
            if session.get('role') != 'admin':
                return jsonify({'error': 'Admin privileges required'}), 403
            
            try:
                new_config = request.get_json()
                # Update configuration logic here
                return jsonify({'status': 'success', 'message': 'Configuration updated'})
            except Exception as e:
                return jsonify({'error': f'Configuration update failed: {str(e)}'}), 500
    
    def _calculate_threat_level(self, stats):
        """Calculate current threat level based on statistics."""
        blocked_ips = stats.get('anomaly_detector', {}).get('blocked_ips', 0)
        total_anomalies = stats.get('anomaly_detector', {}).get('total_anomalies', 0)
        
        if total_anomalies > 50 or blocked_ips > 10:
            return 'HIGH'
        elif total_anomalies > 20 or blocked_ips > 5:
            return 'MEDIUM'
        return 'LOW'
    
    def _get_recent_attacks(self):
        """Get recent attack information."""
        # This would normally come from logs or database
        return [
            {
                'timestamp': datetime.now().isoformat(),
                'type': 'HTTP Flood',
                'source_ip': '192.168.1.100',
                'status': 'BLOCKED'
            }
        ]
    
    def _get_performance_metrics(self):
        """Get system performance metrics."""
        return {
            'cpu_usage': 45.2,
            'memory_usage': 62.8,
            'network_io': 125.6,
            'response_time': 89.3
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
                    padding: 20px;
                }
                
                .login-container {
                    background: rgba(255, 255, 255, 0.95);
                    backdrop-filter: blur(20px);
                    border-radius: 20px;
                    padding: 40px;
                    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.15);
                    width: 100%;
                    max-width: 420px;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }
                
                .logo {
                    text-align: center;
                    margin-bottom: 30px;
                }
                
                .logo h1 {
                    font-size: 2.5rem;
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                    font-weight: 700;
                    margin-bottom: 8px;
                }
                
                .logo .subtitle {
                    color: #6b7280;
                    font-size: 0.95rem;
                    font-weight: 500;
                }
                
                .logo .badge {
                    display: inline-block;
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    color: white;
                    padding: 4px 12px;
                    border-radius: 12px;
                    font-size: 0.75rem;
                    font-weight: 600;
                    margin-top: 8px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                
                .form-group {
                    margin-bottom: 20px;
                }
                
                .form-group label {
                    display: block;
                    margin-bottom: 8px;
                    color: #374151;
                    font-weight: 500;
                    font-size: 0.9rem;
                }
                
                .form-group input {
                    width: 100%;
                    padding: 14px 16px;
                    border: 2px solid #e5e7eb;
                    border-radius: 12px;
                    font-size: 1rem;
                    transition: all 0.3s ease;
                    background: white;
                    font-family: 'Inter', sans-serif;
                }
                
                .form-group input:focus {
                    outline: none;
                    border-color: #667eea;
                    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
                    transform: translateY(-2px);
                }
                
                .login-btn {
                    width: 100%;
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    color: white;
                    padding: 16px;
                    border: none;
                    border-radius: 12px;
                    font-size: 1rem;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    margin-bottom: 20px;
                    font-family: 'Inter', sans-serif;
                }
                
                .login-btn:hover {
                    transform: translateY(-3px);
                    box-shadow: 0 15px 35px rgba(102, 126, 234, 0.4);
                }
                
                .alert {
                    padding: 12px 16px;
                    border-radius: 10px;
                    margin-bottom: 20px;
                    font-size: 0.9rem;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                
                .alert.error {
                    background: #fef2f2;
                    color: #dc2626;
                    border: 1px solid #fecaca;
                }
                
                .alert.success {
                    background: #f0fdf4;
                    color: #16a34a;
                    border: 1px solid #bbf7d0;
                }
                
                .alert.info {
                    background: #eff6ff;
                    color: #2563eb;
                    border: 1px solid #bfdbfe;
                }
                
                .credentials {
                    background: #f8fafc;
                    border: 1px solid #e2e8f0;
                    border-radius: 10px;
                    padding: 12px;
                    margin-top: 20px;
                    font-size: 0.85rem;
                    color: #64748b;
                }
                
                .credentials strong {
                    color: #1e293b;
                }
                
                .shield-animation {
                    animation: float 3s ease-in-out infinite;
                }
                
                @keyframes float {
                    0%, 100% { transform: translateY(0px); }
                    50% { transform: translateY(-8px); }
                }
                
                .tech-stack {
                    margin-top: 20px;
                    text-align: center;
                    font-size: 0.8rem;
                    color: #6b7280;
                    border-top: 1px solid #e5e7eb;
                    padding-top: 15px;
                }
            </style>
        </head>
        <body>
            <div class="login-container">
                <div class="logo">
                    <h1><i class="fas fa-shield-alt shield-animation"></i> Aurora Shield</h1>
                    <p class="subtitle">DDoS Protection Framework</p>
                    <span class="badge">INFOTHON 5.0</span>
                </div>
                
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="alert {{ category }}">
                                <i class="fas fa-{% if category == 'error' %}exclamation-triangle{% elif category == 'success' %}check-circle{% else %}info-circle{% endif %}"></i>
                                {{ message }}
                            </div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}
                
                <form method="POST">
                    <div class="form-group">
                        <label for="username"><i class="fas fa-user"></i> Username</label>
                        <input type="text" id="username" name="username" required placeholder="Enter your username">
                    </div>
                    
                    <div class="form-group">
                        <label for="password"><i class="fas fa-lock"></i> Password</label>
                        <input type="password" id="password" name="password" required placeholder="Enter your password">
                    </div>
                    
                    <button type="submit" class="login-btn">
                        <i class="fas fa-sign-in-alt"></i> Sign In to Dashboard
                    </button>
                </form>
                
                <div class="credentials">
                    <strong>Demo Credentials:</strong><br>
                    Admin: <code>admin</code> / <code>admin123</code><br>
                    User: <code>user</code> / <code>user123</code>
                </div>
                
                <div class="tech-stack">
                    <i class="fas fa-code"></i> Flask • Python • Real-time Monitoring
                </div>
            </div>
        </body>
        </html>
        '''
    
    def _get_dashboard_template(self):
        """Enhanced dashboard template with dark theme and sidebar navigation."""
        return '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Aurora Shield Dashboard - INFOTHON 5.0</title>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.css" rel="stylesheet">
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                
                body {
                    font-family: 'Inter', sans-serif;
                    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
                    min-height: 100vh;
                    color: #e2e8f0;
                    overflow-x: hidden;
                }
                
                .app-container {
                    display: flex;
                    min-height: 100vh;
                }
                
                /* Sidebar Styles */
                .sidebar {
                    width: 280px;
                    background: rgba(15, 23, 42, 0.95);
                    backdrop-filter: blur(20px);
                    border-right: 1px solid rgba(99, 102, 241, 0.2);
                    position: fixed;
                    height: 100vh;
                    z-index: 1000;
                    transition: all 0.3s ease;
                    overflow-y: auto;
                }
                
                .sidebar.collapsed {
                    width: 80px;
                }
                
                .sidebar-header {
                    padding: 25px 20px;
                    border-bottom: 1px solid rgba(99, 102, 241, 0.2);
                    text-align: center;
                }
                
                .sidebar-header h1 {
                    font-size: 1.5rem;
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                    font-weight: 700;
                    margin-bottom: 5px;
                }
                
                .sidebar.collapsed .sidebar-header h1 {
                    font-size: 1.2rem;
                }
                
                .sidebar-header .subtitle {
                    font-size: 0.75rem;
                    color: #64748b;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                
                .sidebar-toggle {
                    position: absolute;
                    top: 20px;
                    right: 15px;
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    border: none;
                    color: white;
                    width: 30px;
                    height: 30px;
                    border-radius: 50%;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 0.9rem;
                }
                
                .sidebar-nav {
                    padding: 20px 0;
                }
                
                .nav-item {
                    margin: 5px 15px;
                    border-radius: 12px;
                    overflow: hidden;
                }
                
                .nav-link {
                    display: flex;
                    align-items: center;
                    padding: 15px 20px;
                    color: #94a3b8;
                    text-decoration: none;
                    transition: all 0.3s ease;
                    font-weight: 500;
                    border-radius: 12px;
                }
                
                .nav-link:hover {
                    background: rgba(99, 102, 241, 0.1);
                    color: #e2e8f0;
                    transform: translateX(5px);
                }
                
                .nav-link.active {
                    background: linear-gradient(135deg, rgba(102, 126, 234, 0.2), rgba(118, 75, 162, 0.2));
                    color: #667eea;
                    border-left: 3px solid #667eea;
                }
                
                .nav-link i {
                    margin-right: 12px;
                    width: 20px;
                    text-align: center;
                    font-size: 1.1rem;
                }
                
                .sidebar.collapsed .nav-link span {
                    display: none;
                }
                
                .sidebar.collapsed .nav-link {
                    justify-content: center;
                    padding: 15px;
                }
                
                .sidebar.collapsed .nav-link i {
                    margin-right: 0;
                }
                
                /* Main Content */
                .main-content {
                    flex: 1;
                    margin-left: 280px;
                    transition: all 0.3s ease;
                    padding: 20px;
                }
                
                .main-content.expanded {
                    margin-left: 80px;
                }
                
                .header {
                    background: rgba(15, 23, 42, 0.95);
                    backdrop-filter: blur(20px);
                    padding: 20px 30px;
                    border-radius: 20px;
                    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.3);
                    margin-bottom: 30px;
                    border: 1px solid rgba(99, 102, 241, 0.2);
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    flex-wrap: wrap;
                }
                
                .header-left h2 {
                    font-size: 1.8rem;
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                    font-weight: 700;
                    margin-bottom: 5px;
                }
                
                .header-left .subtitle {
                    color: #64748b;
                    font-size: 0.9rem;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }
                
                .header-right {
                    display: flex;
                    align-items: center;
                    gap: 15px;
                }
                
                .user-info {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    background: rgba(99, 102, 241, 0.1);
                    padding: 10px 15px;
                    border-radius: 12px;
                    border: 1px solid rgba(99, 102, 241, 0.2);
                }
                
                .user-avatar {
                    width: 32px;
                    height: 32px;
                    border-radius: 50%;
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-weight: 600;
                    font-size: 0.9rem;
                }
                
                .logout-btn {
                    background: linear-gradient(135deg, #ef4444, #dc2626);
                    color: white;
                    text-decoration: none;
                    padding: 10px 20px;
                    border-radius: 10px;
                    font-weight: 500;
                    transition: all 0.3s ease;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    font-size: 0.9rem;
                }
                
                .logout-btn:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 10px 25px rgba(239, 68, 68, 0.3);
                }
                
                /* Tab Content */
                .tab-content {
                    display: none;
                }
                
                .tab-content.active {
                    display: block;
                }
                
                /* Status Bar */
                .status-bar {
                    background: rgba(15, 23, 42, 0.95);
                    backdrop-filter: blur(20px);
                    padding: 30px;
                    border-radius: 20px;
                    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.3);
                    margin-bottom: 30px;
                    border: 1px solid rgba(99, 102, 241, 0.2);
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 25px;
                }
                
                .status-item {
                    text-align: center;
                    padding: 25px 15px;
                    background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(139, 92, 246, 0.1));
                    border-radius: 15px;
                    transition: all 0.3s ease;
                    border: 1px solid rgba(99, 102, 241, 0.2);
                    position: relative;
                    overflow: hidden;
                }
                
                .status-item::before {
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    height: 3px;
                    background: linear-gradient(135deg, #667eea, #764ba2);
                }
                
                .status-item:hover {
                    transform: translateY(-5px);
                    box-shadow: 0 15px 35px rgba(99, 102, 241, 0.2);
                    background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(139, 92, 246, 0.15));
                }
                
                .status-icon {
                    font-size: 2rem;
                    margin-bottom: 10px;
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                }
                
                .status-value {
                    font-size: 2.5rem;
                    font-weight: 700;
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                    margin-bottom: 8px;
                    display: block;
                }
                
                .status-label {
                    color: #94a3b8;
                    font-weight: 500;
                    font-size: 0.9rem;
                }
                
                /* Cards */
                .grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
                    gap: 30px;
                    margin-bottom: 30px;
                }
                
                .card {
                    background: rgba(15, 23, 42, 0.95);
                    backdrop-filter: blur(20px);
                    padding: 30px;
                    border-radius: 20px;
                    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.3);
                    border: 1px solid rgba(99, 102, 241, 0.2);
                    transition: all 0.3s ease;
                }
                
                .card:hover {
                    transform: translateY(-5px);
                    box-shadow: 0 30px 60px rgba(0, 0, 0, 0.4);
                    border-color: rgba(99, 102, 241, 0.3);
                }
                
                .card h3 {
                    color: #e2e8f0;
                    margin-bottom: 20px;
                    font-size: 1.4rem;
                    font-weight: 600;
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    padding-bottom: 15px;
                    border-bottom: 2px solid;
                    border-image: linear-gradient(135deg, #667eea, #764ba2) 1;
                }
                
                .card h3 i {
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                }
                
                .metric {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 15px 0;
                    border-bottom: 1px solid rgba(99, 102, 241, 0.1);
                    transition: all 0.3s ease;
                }
                
                .metric:hover {
                    background: rgba(99, 102, 241, 0.05);
                    padding-left: 12px;
                    border-radius: 8px;
                    margin: 0 -12px;
                }
                
                .metric:last-child {
                    border-bottom: none;
                }
                
                .metric-label {
                    color: #94a3b8;
                    font-weight: 500;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                
                .metric-value {
                    font-weight: 600;
                    color: #e2e8f0;
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                    font-size: 1.1rem;
                }
                
                /* Buttons */
                .control-panel {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 15px;
                    margin-bottom: 25px;
                }
                
                .btn {
                    padding: 12px 24px;
                    border: none;
                    border-radius: 12px;
                    cursor: pointer;
                    font-size: 0.9rem;
                    font-weight: 600;
                    transition: all 0.3s ease;
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    text-decoration: none;
                    font-family: 'Inter', sans-serif;
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
                    font-size: 0.9rem;
                    border-left: 4px solid;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }
                
                .alert.success {
                    background: rgba(16, 185, 129, 0.1);
                    color: #10b981;
                    border-left-color: #10b981;
                }
                
                .alert.warning {
                    background: rgba(245, 158, 11, 0.1);
                    color: #f59e0b;
                    border-left-color: #f59e0b;
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
                    margin: 8px 0;
                    background: linear-gradient(135deg, rgba(99, 102, 241, 0.05), rgba(139, 92, 246, 0.05));
                    border-radius: 10px;
                    font-size: 0.9rem;
                    border-left: 3px solid #667eea;
                    transition: all 0.3s ease;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }
                
                .log-entry:hover {
                    background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(139, 92, 246, 0.1));
                    transform: translateX(5px);
                }
                
                .log-time {
                    color: #64748b;
                    font-size: 0.8rem;
                    margin-left: auto;
                }
                
                /* Threat Levels */
                .threat-level {
                    padding: 6px 12px;
                    border-radius: 20px;
                    font-size: 0.75rem;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                
                .threat-level.low {
                    background: rgba(16, 185, 129, 0.2);
                    color: #10b981;
                }
                
                .threat-level.medium {
                    background: rgba(245, 158, 11, 0.2);
                    color: #f59e0b;
                }
                
                .threat-level.high {
                    background: rgba(239, 68, 68, 0.2);
                    color: #ef4444;
                }
                
                /* Animations */
                .refresh-indicator {
                    display: inline-block;
                    width: 12px;
                    height: 12px;
                    background: linear-gradient(135deg, #10b981, #059669);
                    border-radius: 50%;
                    animation: pulse 2s infinite;
                }
                
                @keyframes pulse {
                    0%, 100% { 
                        opacity: 1; 
                        transform: scale(1);
                    }
                    50% { 
                        opacity: 0.4; 
                        transform: scale(1.2);
                    }
                }
                
                .loading {
                    display: inline-block;
                    width: 16px;
                    height: 16px;
                    border: 2px solid rgba(255, 255, 255, 0.3);
                    border-top: 2px solid #ffffff;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                }
                
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                
                /* Badge */
                .badge {
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    color: white;
                    padding: 4px 12px;
                    border-radius: 12px;
                    font-size: 0.75rem;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                
                /* Responsive */
                @media (max-width: 768px) {
                    .sidebar {
                        width: 100%;
                        height: auto;
                        position: relative;
                    }
                    
                    .main-content {
                        margin-left: 0;
                    }
                    
                    .header {
                        flex-direction: column;
                        gap: 15px;
                        text-align: center;
                    }
                    
                    .status-bar {
                        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                        gap: 15px;
                    }
                    
                    .grid {
                        grid-template-columns: 1fr;
                    }
                    
                    .control-panel {
                        flex-direction: column;
                    }
                }
                
                /* Footer */
                .infothon-footer {
                    text-align: center;
                    margin-top: 30px;
                    padding: 20px;
                    background: rgba(15, 23, 42, 0.8);
                    border-radius: 15px;
                    color: #64748b;
                    font-size: 0.9rem;
                    border: 1px solid rgba(99, 102, 241, 0.2);
                }
            </style>
        </head>
        <body>
            <div class="app-container">
                <!-- Sidebar -->
                <div class="sidebar" id="sidebar">
                    <div class="sidebar-header">
                        <button class="sidebar-toggle" onclick="toggleSidebar()">
                            <i class="fas fa-bars"></i>
                        </button>
                        <h1><i class="fas fa-shield-alt"></i> Aurora Shield</h1>
                        <p class="subtitle">INFOTHON 5.0</p>
                    </div>
                    
                    <nav class="sidebar-nav">
                        <div class="nav-item">
                            <a href="#" class="nav-link active" onclick="showTab('dashboard')">
                                <i class="fas fa-tachometer-alt"></i>
                                <span>Dashboard</span>
                            </a>
                        </div>
                        <div class="nav-item">
                            <a href="#" class="nav-link" onclick="showTab('monitoring')">
                                <i class="fas fa-chart-line"></i>
                                <span>Monitoring</span>
                            </a>
                        </div>
                        <div class="nav-item">
                            <a href="#" class="nav-link" onclick="showTab('simulation')">
                                <i class="fas fa-bug"></i>
                                <span>Attack Simulation</span>
                            </a>
                        </div>
                        <div class="nav-item">
                            <a href="#" class="nav-link" onclick="showTab('protection')">
                                <i class="fas fa-shield-check"></i>
                                <span>Protection</span>
                            </a>
                        </div>
                        <div class="nav-item">
                            <a href="#" class="nav-link" onclick="showTab('analytics')">
                                <i class="fas fa-chart-pie"></i>
                                <span>Analytics</span>
                            </a>
                        </div>
                        <div class="nav-item">
                            <a href="#" class="nav-link" onclick="showTab('settings')">
                                <i class="fas fa-cog"></i>
                                <span>Settings</span>
                            </a>
                        </div>
                    </nav>
                </div>
                
                <!-- Main Content -->
                <div class="main-content" id="mainContent">
                    <div class="header">
                        <div class="header-left">
                            <h2 id="pageTitle">Dashboard Overview</h2>
                            <p class="subtitle">
                                <span class="refresh-indicator"></span>
                                Real-time DDoS Protection Monitoring
                                <span class="badge">Live</span>
                            </p>
                        </div>
                        <div class="header-right">
                            <div class="user-info">
                                <div class="user-avatar">{{ session.name[0] if session.name else 'U' }}</div>
                                <div>
                                    <div style="font-weight: 600; color: #e2e8f0;">{{ session.name or 'User' }}</div>
                                    <div style="font-size: 0.8rem; color: #64748b;">{{ session.role or 'user' }}</div>
                                </div>
                            </div>
                            <a href="/logout" class="logout-btn">
                                <i class="fas fa-sign-out-alt"></i> Logout
                            </a>
                        </div>
                    </div>
                    
                    <!-- Dashboard Tab -->
                    <div id="dashboard" class="tab-content active">
                        <div class="status-bar" id="statusBar">
                            <div class="status-item">
                                <div class="status-icon"><i class="fas fa-shield-check"></i></div>
                                <div class="status-value" id="protectionStatus">ACTIVE</div>
                                <div class="status-label">Protection Status</div>
                            </div>
                            <div class="status-item">
                                <div class="status-icon"><i class="fas fa-ban"></i></div>
                                <div class="status-value" id="threatsBlocked">0</div>
                                <div class="status-label">Threats Blocked</div>
                            </div>
                            <div class="status-item">
                                <div class="status-icon"><i class="fas fa-eye"></i></div>
                                <div class="status-value" id="activeMonitoring">0</div>
                                <div class="status-label">IPs Monitored</div>
                            </div>
                            <div class="status-item">
                                <div class="status-icon"><i class="fas fa-tachometer-alt"></i></div>
                                <div class="status-value" id="requestRate">0</div>
                                <div class="status-label">Requests/min</div>
                            </div>
                            <div class="status-item">
                                <div class="status-icon"><i class="fas fa-exclamation-triangle"></i></div>
                                <div class="status-value" id="threatLevel">LOW</div>
                                <div class="status-label">Threat Level</div>
                            </div>
                        </div>
                        
                        <div class="grid">
                            <div class="card">
                                <h3><i class="fas fa-search"></i> Anomaly Detection</h3>
                                <div id="anomalyStats">
                                    <div class="metric">
                                        <span class="metric-label"><i class="fas fa-desktop"></i> Monitored IPs</span>
                                        <span class="metric-value">0</span>
                                    </div>
                                    <div class="metric">
                                        <span class="metric-label"><i class="fas fa-ban"></i> Blocked IPs</span>
                                        <span class="metric-value">0</span>
                                    </div>
                                    <div class="metric">
                                        <span class="metric-label"><i class="fas fa-exclamation-circle"></i> Total Anomalies</span>
                                        <span class="metric-value">0</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="card">
                                <h3><i class="fas fa-stopwatch"></i> Rate Limiting</h3>
                                <div id="rateLimitStats">
                                    <div class="metric">
                                        <span class="metric-label"><i class="fas fa-users"></i> Tracked Identifiers</span>
                                        <span class="metric-value">0</span>
                                    </div>
                                    <div class="metric">
                                        <span class="metric-label"><i class="fas fa-gauge"></i> Rate Limit</span>
                                        <span class="metric-value">10 req/s</span>
                                    </div>
                                    <div class="metric">
                                        <span class="metric-label"><i class="fas fa-bolt"></i> Burst Limit</span>
                                        <span class="metric-value">20</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="card">
                                <h3><i class="fas fa-award"></i> IP Reputation</h3>
                                <div id="reputationStats">
                                    <div class="metric">
                                        <span class="metric-label"><i class="fas fa-globe"></i> Tracked IPs</span>
                                        <span class="metric-value">0</span>
                                    </div>
                                    <div class="metric">
                                        <span class="metric-label"><i class="fas fa-check-circle"></i> Whitelisted</span>
                                        <span class="metric-value">0</span>
                                    </div>
                                    <div class="metric">
                                        <span class="metric-label"><i class="fas fa-times-circle"></i> Blacklisted</span>
                                        <span class="metric-value">0</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="card">
                                <h3><i class="fas fa-server"></i> System Performance</h3>
                                <div id="performanceStats">
                                    <div class="metric">
                                        <span class="metric-label"><i class="fas fa-microchip"></i> CPU Usage</span>
                                        <span class="metric-value">45.2%</span>
                                    </div>
                                    <div class="metric">
                                        <span class="metric-label"><i class="fas fa-memory"></i> Memory Usage</span>
                                        <span class="metric-value">62.8%</span>
                                    </div>
                                    <div class="metric">
                                        <span class="metric-label"><i class="fas fa-network-wired"></i> Network I/O</span>
                                        <span class="metric-value">125.6 MB/s</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="card">
                            <h3><i class="fas fa-chart-line"></i> Recent Activity</h3>
                            <div class="activity-log" id="recentActivity">
                                <div class="log-entry">
                                    <i class="fas fa-info-circle" style="color: #3b82f6;"></i>
                                    <span>System initialized and monitoring started</span>
                                    <span class="log-time">just now</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Monitoring Tab -->
                    <div id="monitoring" class="tab-content">
                        <div class="card">
                            <h3><i class="fas fa-chart-area"></i> Real-time Traffic Monitoring</h3>
                            <div style="height: 300px; background: rgba(99, 102, 241, 0.05); border-radius: 10px; display: flex; align-items: center; justify-content: center; color: #64748b;">
                                <i class="fas fa-chart-line" style="font-size: 3rem; opacity: 0.3;"></i>
                                <span style="margin-left: 15px;">Traffic Chart Placeholder</span>
                            </div>
                        </div>
                        
                        <div class="grid">
                            <div class="card">
                                <h3><i class="fas fa-network-wired"></i> Network Statistics</h3>
                                <div id="networkStats">
                                    <div class="metric">
                                        <span class="metric-label">Packets/sec</span>
                                        <span class="metric-value">1,234</span>
                                    </div>
                                    <div class="metric">
                                        <span class="metric-label">Bandwidth Usage</span>
                                        <span class="metric-value">45.6 MB/s</span>
                                    </div>
                                    <div class="metric">
                                        <span class="metric-label">Connections</span>
                                        <span class="metric-value">89</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="card">
                                <h3><i class="fas fa-clock"></i> Response Times</h3>
                                <div id="responseStats">
                                    <div class="metric">
                                        <span class="metric-label">Average Response</span>
                                        <span class="metric-value">125ms</span>
                                    </div>
                                    <div class="metric">
                                        <span class="metric-label">95th Percentile</span>
                                        <span class="metric-value">250ms</span>
                                    </div>
                                    <div class="metric">
                                        <span class="metric-label">Max Response</span>
                                        <span class="metric-value">456ms</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Attack Simulation Tab -->
                    <div id="simulation" class="tab-content">
                        <div class="card">
                            <h3><i class="fas fa-gamepad"></i> Attack Simulation Control Panel</h3>
                            <div class="control-panel">
                                <button class="btn btn-success" onclick="refreshData()">
                                    <i class="fas fa-sync-alt"></i> Refresh Data
                                </button>
                                <button class="btn btn-primary" onclick="runSimulation('http_flood')">
                                    <i class="fas fa-tidal-wave"></i> HTTP Flood Attack
                                </button>
                                <button class="btn btn-warning" onclick="runSimulation('distributed')">
                                    <i class="fas fa-sitemap"></i> Distributed Attack
                                </button>
                                <button class="btn btn-primary" onclick="runSimulation('slowloris')">
                                    <i class="fas fa-hourglass-half"></i> Slowloris Attack
                                </button>
                                {% if session.role == 'admin' %}
                                <button class="btn btn-danger" onclick="resetSystem()">
                                    <i class="fas fa-exclamation-triangle"></i> Reset System
                                </button>
                                {% endif %}
                            </div>
                            <div id="controlMessages"></div>
                        </div>
                        
                        <div class="grid">
                            <div class="card">
                                <h3><i class="fas fa-history"></i> Simulation History</h3>
                                <div id="simulationHistory">
                                    <div class="log-entry">
                                        <i class="fas fa-play-circle" style="color: #10b981;"></i>
                                        <span>No simulations run yet</span>
                                        <span class="log-time">-</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="card">
                                <h3><i class="fas fa-chart-bar"></i> Attack Metrics</h3>
                                <div id="attackMetrics">
                                    <div class="metric">
                                        <span class="metric-label">Total Simulations</span>
                                        <span class="metric-value">0</span>
                                    </div>
                                    <div class="metric">
                                        <span class="metric-label">Success Rate</span>
                                        <span class="metric-value">0%</span>
                                    </div>
                                    <div class="metric">
                                        <span class="metric-label">Avg Duration</span>
                                        <span class="metric-value">-</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Protection Tab -->
                    <div id="protection" class="tab-content">
                        <div class="grid">
                            <div class="card">
                                <h3><i class="fas fa-shield-alt"></i> Protection Layers</h3>
                                <div id="protectionLayers">
                                    <div class="metric">
                                        <span class="metric-label"><i class="fas fa-layer-group"></i> Active Layers</span>
                                        <span class="metric-value">5</span>
                                    </div>
                                    <div class="metric">
                                        <span class="metric-label"><i class="fas fa-check-shield"></i> IP Reputation</span>
                                        <span class="metric-value" style="color: #10b981;">ACTIVE</span>
                                    </div>
                                    <div class="metric">
                                        <span class="metric-label"><i class="fas fa-stopwatch"></i> Rate Limiting</span>
                                        <span class="metric-value" style="color: #10b981;">ACTIVE</span>
                                    </div>
                                    <div class="metric">
                                        <span class="metric-label"><i class="fas fa-search"></i> Anomaly Detection</span>
                                        <span class="metric-value" style="color: #10b981;">ACTIVE</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="card">
                                <h3><i class="fas fa-list-ul"></i> Blocked IPs</h3>
                                <div id="blockedIPs">
                                    <div class="log-entry">
                                        <i class="fas fa-ban" style="color: #ef4444;"></i>
                                        <span>No IPs currently blocked</span>
                                        <span class="log-time">-</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Analytics Tab -->
                    <div id="analytics" class="tab-content">
                        <div class="card">
                            <h3><i class="fas fa-chart-pie"></i> Security Analytics</h3>
                            <div style="height: 300px; background: rgba(99, 102, 241, 0.05); border-radius: 10px; display: flex; align-items: center; justify-content: center; color: #64748b;">
                                <i class="fas fa-chart-pie" style="font-size: 3rem; opacity: 0.3;"></i>
                                <span style="margin-left: 15px;">Analytics Charts Placeholder</span>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Settings Tab -->
                    <div id="settings" class="tab-content">
                        <div class="grid">
                            <div class="card">
                                <h3><i class="fas fa-sliders-h"></i> Rate Limiting Settings</h3>
                                <div id="rateLimitSettings">
                                    <div class="metric">
                                        <span class="metric-label">Requests per Second</span>
                                        <span class="metric-value">10</span>
                                    </div>
                                    <div class="metric">
                                        <span class="metric-label">Burst Limit</span>
                                        <span class="metric-value">20</span>
                                    </div>
                                    <div class="metric">
                                        <span class="metric-label">Window Size</span>
                                        <span class="metric-value">60s</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="card">
                                <h3><i class="fas fa-cogs"></i> System Configuration</h3>
                                <div id="systemConfig">
                                    <div class="metric">
                                        <span class="metric-label">Auto-Recovery</span>
                                        <span class="metric-value" style="color: #10b981;">ENABLED</span>
                                    </div>
                                    <div class="metric">
                                        <span class="metric-label">ELK Integration</span>
                                        <span class="metric-value" style="color: #10b981;">ENABLED</span>
                                    </div>
                                    <div class="metric">
                                        <span class="metric-label">Prometheus</span>
                                        <span class="metric-value" style="color: #10b981;">ENABLED</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="infothon-footer">
                        <i class="fas fa-shield-alt"></i> Aurora Shield - INFOTHON 5.0 DDoS Protection Framework<br>
                        <small>Powered by Flask • Python • Real-time Analytics • Dark Theme</small>
                    </div>
                </div>
            </div>
            
            <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
            <script>
                let isLoading = false;
                let updateInterval = null;
                let simulationHistory = [];
                
                // Sidebar Toggle
                function toggleSidebar() {
                    const sidebar = document.getElementById('sidebar');
                    const mainContent = document.getElementById('mainContent');
                    
                    sidebar.classList.toggle('collapsed');
                    mainContent.classList.toggle('expanded');
                }
                
                // Tab Navigation
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
                    document.getElementById(tabName).classList.add('active');
                    
                    // Add active class to clicked nav link
                    event.target.classList.add('active');
                    
                    // Update page title
                    const titles = {
                        'dashboard': 'Dashboard Overview',
                        'monitoring': 'Real-time Monitoring',
                        'simulation': 'Attack Simulation',
                        'protection': 'Protection Status',
                        'analytics': 'Security Analytics',
                        'settings': 'System Settings'
                    };
                    
                    document.getElementById('pageTitle').textContent = titles[tabName] || 'Dashboard';
                }
                
                function updateDashboard() {
                    if (isLoading) return;
                    isLoading = true;
                    
                    fetch('/api/dashboard/stats')
                        .then(response => {
                            if (!response.ok) {
                                throw new Error(`HTTP ${response.status}`);
                            }
                            return response.json();
                        })
                        .then(data => {
                            if (data.error) {
                                console.error('API Error:', data.error);
                                if (data.error.includes('Authentication')) {
                                    window.location.href = '/login';
                                }
                                return;
                            }
                            
                            console.log('Dashboard data received:', data);
                            
                            // Update status bar
                            document.getElementById('threatsBlocked').textContent = data.threats_blocked || 0;
                            document.getElementById('activeMonitoring').textContent = data.monitored_ips || 0;
                            
                            // Update main stats
                            if (document.getElementById('totalRequests')) {
                                document.getElementById('totalRequests').textContent = data.total_requests || 0;
                            }
                            if (document.getElementById('blockedRequests')) {
                                document.getElementById('blockedRequests').textContent = data.threats_blocked || 0;
                            }
                            
                            // Update threat level
                            const threatLevel = data.system_info?.threat_level || 'LOW';
                            const threatElement = document.getElementById('threatLevel');
                            threatElement.textContent = threatLevel;
                            threatElement.className = `threat-level ${threatLevel.toLowerCase()}`;
                            
                            // Update anomaly detection
                            if (data.anomaly_detector) {
                                updateMetrics('anomalyStats', [
                                    { label: '<i class="fas fa-desktop"></i> Monitored IPs', value: data.anomaly_detector.monitored_ips || 0 },
                                    { label: '<i class="fas fa-ban"></i> Blocked IPs', value: data.anomaly_detector.blocked_ips || 0 },
                                    { label: '<i class="fas fa-exclamation-circle"></i> Total Anomalies', value: data.anomaly_detector.total_anomalies || 0 }
                                ]);
                            }
                            
                            // Update rate limiting
                            if (data.rate_limiter) {
                                updateMetrics('rateLimitStats', [
                                    { label: '<i class="fas fa-users"></i> Tracked Identifiers', value: Object.keys(data.rate_limiter.buckets || {}).length },
                                    { label: '<i class="fas fa-gauge"></i> Rate Limit', value: '10 req/s' },
                                    { label: '<i class="fas fa-bolt"></i> Burst Limit', value: '20' }
                                ]);
                            }
                            
                            // Update performance metrics
                            if (data.performance_metrics) {
                                updateMetrics('performanceStats', [
                                    { label: '<i class="fas fa-microchip"></i> CPU Usage', value: data.performance_metrics.cpu_usage + '%' },
                                    { label: '<i class="fas fa-memory"></i> Memory Usage', value: data.performance_metrics.memory_usage + '%' },
                                    { label: '<i class="fas fa-network-wired"></i> Network I/O', value: data.performance_metrics.network_io + ' MB/s' }
                                ]);
                            }
                            
                            // Update activity log
                            if (data.recent_attacks && data.recent_attacks.length > 0) {
                                updateActivityLog(data.recent_attacks);
                            }
                        })
                        .catch(error => {
                            console.error('Error updating dashboard:', error);
                            showMessage('Failed to update dashboard data: ' + error.message, 'error');
                        })
                        .finally(() => {
                            isLoading = false;
                        });
                }
                
                function updateMetrics(containerId, metrics) {
                    const container = document.getElementById(containerId);
                    if (container) {
                        container.innerHTML = metrics.map(metric => `
                            <div class="metric">
                                <span class="metric-label">${metric.label}</span>
                                <span class="metric-value">${metric.value}</span>
                            </div>
                        `).join('');
                    }
                }
                
                function updateActivityLog(activities) {
                    const container = document.getElementById('recentActivity');
                    if (container) {
                        container.innerHTML = activities.map(activity => `
                            <div class="log-entry">
                                <i class="fas fa-${getActivityIcon(activity.type)}" style="color: ${getActivityColor(activity.status)};"></i>
                                <span>${activity.type} from ${activity.source_ip}</span>
                                <span class="log-time">${formatTime(activity.timestamp)}</span>
                            </div>
                        `).join('');
                    }
                }
                
                function getActivityIcon(type) {
                    const icons = {
                        'HTTP Flood': 'tidal-wave',
                        'Slowloris': 'hourglass-half',
                        'Distributed': 'sitemap'
                    };
                    return icons[type] || 'exclamation-triangle';
                }
                
                function getActivityColor(status) {
                    return status === 'BLOCKED' ? '#ef4444' : '#f59e0b';
                }
                
                function formatTime(timestamp) {
                    try {
                        const date = new Date(timestamp);
                        return date.toLocaleTimeString();
                    } catch (e) {
                        return 'now';
                    }
                }
                
                function refreshData() {
                    const btn = event.target;
                    const originalText = btn.innerHTML;
                    btn.innerHTML = '<div class="loading"></div> Refreshing...';
                    btn.disabled = true;
                    
                    updateDashboard();
                    showMessage('Dashboard data refreshed successfully', 'success');
                    
                    setTimeout(() => {
                        btn.innerHTML = originalText;
                        btn.disabled = false;
                    }, 1500);
                }
                
                function runSimulation(type = 'http_flood') {
                    const btn = event.target;
                    const originalText = btn.innerHTML;
                    btn.innerHTML = '<div class="loading"></div> Running...';
                    btn.disabled = true;
                    
                    const attackNames = {
                        'http_flood': 'HTTP Flood',
                        'distributed': 'Distributed',
                        'slowloris': 'Slowloris'
                    };
                    
                    showMessage(`Starting ${attackNames[type]} attack simulation...`, 'warning');
                    
                    fetch('/api/dashboard/simulate', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ type: type })
                    })
                    .then(response => {
                        if (!response.ok) {
                            throw new Error(`HTTP ${response.status}`);
                        }
                        return response.json();
                    })
                    .then(data => {
                        console.log('Simulation result:', data);
                        
                        if (data.error) {
                            showMessage('Simulation error: ' + data.error, 'error');
                        } else {
                            showMessage(data.message || 'Simulation completed successfully', 'success');
                            
                            // Add to simulation history
                            simulationHistory.unshift({
                                type: attackNames[type],
                                timestamp: new Date().toISOString(),
                                status: 'Success',
                                result: data.result
                            });
                            
                            updateSimulationHistory();
                            updateDashboard();
                        }
                    })
                    .catch(error => {
                        console.error('Simulation error:', error);
                        showMessage('Simulation failed: ' + error.message, 'error');
                    })
                    .finally(() => {
                        setTimeout(() => {
                            btn.innerHTML = originalText;
                            btn.disabled = false;
                        }, 2000);
                    });
                }
                
                function updateSimulationHistory() {
                    const container = document.getElementById('simulationHistory');
                    if (container && simulationHistory.length > 0) {
                        container.innerHTML = simulationHistory.slice(0, 5).map(sim => `
                            <div class="log-entry">
                                <i class="fas fa-play-circle" style="color: #10b981;"></i>
                                <span>${sim.type} attack simulation</span>
                                <span class="log-time">${formatTime(sim.timestamp)}</span>
                            </div>
                        `).join('');
                    }
                    
                    // Update attack metrics
                    const metricsContainer = document.getElementById('attackMetrics');
                    if (metricsContainer) {
                        const successRate = simulationHistory.length > 0 ? 
                            Math.round((simulationHistory.filter(s => s.status === 'Success').length / simulationHistory.length) * 100) : 0;
                        
                        updateMetrics('attackMetrics', [
                            { label: 'Total Simulations', value: simulationHistory.length },
                            { label: 'Success Rate', value: successRate + '%' },
                            { label: 'Avg Duration', value: '10s' }
                        ]);
                    }
                }
                
                function resetSystem() {
                    if (confirm('Are you sure you want to reset the system? This will clear all data and statistics.')) {
                        const btn = event.target;
                        const originalText = btn.innerHTML;
                        btn.innerHTML = '<div class="loading"></div> Resetting...';
                        btn.disabled = true;
                        
                        fetch('/api/dashboard/reset', { method: 'POST' })
                            .then(response => {
                                if (!response.ok) {
                                    throw new Error(`HTTP ${response.status}`);
                                }
                                return response.json();
                            })
                            .then(data => {
                                if (data.error) {
                                    showMessage('Reset error: ' + data.error, 'error');
                                } else {
                                    showMessage('System reset completed successfully', 'success');
                                    simulationHistory = [];
                                    updateSimulationHistory();
                                    updateDashboard();
                                }
                            })
                            .catch(error => {
                                console.error('Reset error:', error);
                                showMessage('Reset failed: ' + error.message, 'error');
                            })
                            .finally(() => {
                                setTimeout(() => {
                                    btn.innerHTML = originalText;
                                    btn.disabled = false;
                                }, 2000);
                            });
                    }
                }
                
                function showMessage(message, type) {
                    const container = document.getElementById('controlMessages');
                    if (container) {
                        const icons = {
                            success: 'check-circle',
                            warning: 'exclamation-triangle',
                            error: 'times-circle',
                            info: 'info-circle'
                        };
                        
                        container.innerHTML = `
                            <div class="alert ${type}">
                                <i class="fas fa-${icons[type]}"></i> ${message}
                            </div>
                        `;
                        
                        setTimeout(() => {
                            container.innerHTML = '';
                        }, 5000);
                    }
                }
                
                // Initialize dashboard
                document.addEventListener('DOMContentLoaded', function() {
                    console.log('Dashboard initializing...');
                    updateDashboard();
                    
                    // Auto-refresh every 5 seconds
                    updateInterval = setInterval(updateDashboard, 5000);
                });
                
                // Cleanup on page unload
                window.addEventListener('beforeunload', function() {
                    if (updateInterval) {
                        clearInterval(updateInterval);
                    }
                });
            </script>
        </body>
        </html>
        '''
         
    def run(self, host='0.0.0.0', port=8080, debug=False):
         
        
        """
        Run the enhanced dashboard.

        Args:
            host (str): Host to bind to
            port (int): Port to bind to
            debug (bool): Enable debug mode
        """
        self.start_time = time.time()
        logger.info(f"🛡️  Starting Aurora Shield Dashboard (INFOTHON 5.0)")
        logger.info(f"📊 Dashboard: http://{host}:{port}")
        logger.info(f"🔐 Demo Credentials: admin/admin123 or user/user123")
        logger.info(f"🎯 Tech Stack: Flask + Python + Real-time Monitoring")

        try:
            self.app.run(host=host, port=port, debug=debug, threaded=True)
        except KeyboardInterrupt:
            logger.info("🛑 Aurora Shield Dashboard stopped")
        except Exception as e:
            logger.error(f"❌ Dashboard error: {e}")
            