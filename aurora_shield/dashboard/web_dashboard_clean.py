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
