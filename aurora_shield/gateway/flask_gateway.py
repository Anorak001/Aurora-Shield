"""
Flask-based edge gateway with DDoS protection.
"""

from flask import Flask, request, jsonify, render_template_string
import time
import logging

logger = logging.getLogger(__name__)


class FlaskGateway:
    """Flask application with integrated DDoS protection."""
    
    def __init__(self, anomaly_detector, rate_limiter, ip_reputation, challenge_response):
        """
        Initialize Flask gateway.
        
        Args:
            anomaly_detector: Anomaly detection instance
            rate_limiter: Rate limiter instance
            ip_reputation: IP reputation instance
            challenge_response: Challenge-response instance
        """
        self.app = Flask(__name__)
        self.anomaly_detector = anomaly_detector
        self.rate_limiter = rate_limiter
        self.ip_reputation = ip_reputation
        self.challenge_response = challenge_response
        
        self._setup_routes()
        self._setup_middleware()
    
    def _setup_middleware(self):
        """Setup middleware for protection."""
        
        @self.app.before_request
        def check_protection():
            """Check all protection layers before processing request."""
            client_ip = request.remote_addr
            
            # Check IP reputation
            reputation = self.ip_reputation.get_reputation(client_ip)
            if not reputation['allowed']:
                logger.warning(f"Blocked request from {client_ip}: {reputation['status']}")
                return jsonify({
                    'error': 'Access denied',
                    'reason': reputation['status']
                }), 403
            
            # Check rate limiting
            rate_check = self.rate_limiter.allow_request(client_ip)
            if not rate_check['allowed']:
                logger.warning(f"Rate limit exceeded for {client_ip}")
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'retry_after': rate_check.get('retry_after', 60)
                }), 429
            
            # Check anomaly detection
            anomaly_check = self.anomaly_detector.check_request(client_ip)
            if not anomaly_check['allowed']:
                logger.warning(f"Anomaly detected from {client_ip}")
                self.ip_reputation.record_violation(client_ip, 'anomaly_detected', severity=20)
                return jsonify({
                    'error': 'Suspicious activity detected',
                    'reason': anomaly_check['reason']
                }), 403
            
            # All checks passed
            return None
    
    def _setup_routes(self):
        """Setup application routes."""
        
        @self.app.route('/')
        def index():
            """Main index page."""
            return jsonify({
                'service': 'Aurora Shield Gateway',
                'status': 'active',
                'version': '1.0.0'
            })
        
        @self.app.route('/health')
        def health():
            """Health check endpoint."""
            return jsonify({
                'status': 'healthy',
                'timestamp': time.time()
            })
        
        @self.app.route('/api/challenge', methods=['POST'])
        def get_challenge():
            """Request a challenge for verification."""
            client_ip = request.remote_addr
            challenge = self.challenge_response.generate_challenge(client_ip)
            return jsonify(challenge)
        
        @self.app.route('/api/verify', methods=['POST'])
        def verify_challenge():
            """Verify challenge response."""
            data = request.json
            result = self.challenge_response.verify_response(
                data.get('challenge_key'),
                data.get('response')
            )
            return jsonify(result)
        
        @self.app.route('/api/stats')
        def get_stats():
            """Get protection statistics."""
            return jsonify({
                'anomaly_detector': self.anomaly_detector.get_statistics(),
                'rate_limiter': self.rate_limiter.get_stats(),
                'ip_reputation': self.ip_reputation.get_stats(),
                'challenge_response': self.challenge_response.get_stats()
            })
        
        @self.app.route('/metrics')
        def metrics():
            """Prometheus metrics endpoint."""
            # This would return Prometheus formatted metrics
            return "# Aurora Shield Metrics\n", 200, {'Content-Type': 'text/plain'}
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """
        Run the Flask gateway.
        
        Args:
            host (str): Host to bind to
            port (int): Port to bind to
            debug (bool): Enable debug mode
        """
        logger.info(f"Starting Aurora Shield Gateway on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)
