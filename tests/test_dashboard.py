"""
Minimal WebDashboard for testing auth route registration
"""

from flask import Flask, jsonify, request
import time
import logging

logger = logging.getLogger(__name__)

class WebDashboard:
    def __init__(self, shield_manager):
        self.app = Flask(__name__)
        self.app.secret_key = 'test-key'
        self.shield_manager = shield_manager
        self._setup_routes()
        
    def _setup_routes(self):
        print("Setting up routes...")
        
        @self.app.route('/test')
        def test():
            return "Test route works"
            
        @self.app.route('/api/shield/check-request', methods=['GET', 'POST', 'PUT', 'DELETE'])
        def check_request_authorization():
            """Auth endpoint for nginx"""
            try:
                client_ip = request.headers.get('X-Original-Remote-Addr', request.remote_addr)
                original_uri = request.headers.get('X-Original-URI', '/')
                original_method = request.headers.get('X-Original-Method', 'GET')
                user_agent = request.headers.get('User-Agent', '')
                
                request_data = {
                    'ip': client_ip,
                    'path': original_uri,
                    'method': original_method,
                    'user_agent': user_agent,
                    'timestamp': time.time()
                }
                
                shield_response = self.shield_manager.process_request(request_data)
                
                if shield_response.get('allowed', False):
                    return '', 200
                else:
                    return jsonify({
                        'error': 'Access denied by Aurora Shield',
                        'reason': shield_response.get('reason', 'Security violation detected'),
                        'blocked_by': 'Aurora Shield'
                    }), 403
                    
            except Exception as e:
                logger.error(f"Error in request authorization check: {e}")
                return '', 200
                
        print("Routes setup complete")
        
    def run(self, host='0.0.0.0', port=8080, debug=False):
        self.app.run(host=host, port=port, debug=debug, threaded=True)