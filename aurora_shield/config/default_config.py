"""
Default configuration for Aurora Shield.
"""
import os

DEFAULT_CONFIG = {
    'anomaly_detector': {
        'request_window': 60,  # seconds
        'rate_threshold': 100,  # requests per window
    },
    'rate_limiter': {
        'rate': 10,  # tokens per second
        'burst': 20,  # max tokens
    },
    'ip_reputation': {
        'initial_score': 100,
    },
    'challenge_response': {
        'challenge_timeout': 300,  # seconds
    },
    'recovery_manager': {
        'servers': ['primary'],
        'max_capacity': 5,
    },
    'attack_simulator': {
        'default_duration': 60,
    },
    'elk': {
        'es_host': 'localhost:9200',
        'index_prefix': 'aurora-shield',
    },
    'prometheus': {
        'port': 9090,
    },
    'gateway': {
        'host': '0.0.0.0',
        'port': 5000,
    },
    'dashboard': {
        'host': '0.0.0.0',
        'port': int(os.environ.get('PORT', 8080)),  # Render uses PORT env var
    }
}
