#!/usr/bin/env python3
"""
Load Balancer Service for Aurora Shield
"""

from flask import Flask, request, jsonify, render_template_string
import requests
import random
import logging
import time
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# CDN configuration with weights
CDN_SERVICES = {
    'primary': {
        'url': 'http://demo-webapp:80',
        'weight': 3,
        'status': 'active'
    },
    'secondary': {
        'url': 'http://demo-webapp-cdn2:80', 
        'weight': 2,
        'status': 'active'
    },
    'tertiary': {
        'url': 'http://demo-webapp-cdn3:80',
        'weight': 1,
        'status': 'active'
    }
}

# Load balancer stats
stats = {
    'requests_total': 0,
    'requests_by_cdn': {'primary': 0, 'secondary': 0, 'tertiary': 0},
    'errors': 0,
    'start_time': datetime.now()
}

def get_weighted_cdn():
    """Select CDN based on weights."""
    active_cdns = [(name, config) for name, config in CDN_SERVICES.items() 
                   if config['status'] == 'active']
    
    if not active_cdns:
        return None
    
    # Create weighted list
    weighted_list = []
    for name, config in active_cdns:
        weighted_list.extend([name] * config['weight'])
    
    return random.choice(weighted_list)

@app.route('/')
def home():
    """Load balancer status page."""
    uptime = datetime.now() - stats['start_time']
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Aurora Shield Load Balancer</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .header { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
            .status { display: flex; gap: 20px; margin: 20px 0; }
            .cdn-box { border: 1px solid #ddd; padding: 15px; border-radius: 5px; flex: 1; }
            .active { border-color: #27ae60; background-color: #f8fff8; }
            .inactive { border-color: #e74c3c; background-color: #fff8f8; }
            .stats { margin: 20px 0; }
            .actions { margin: 20px 0; }
            button { padding: 8px 15px; margin: 5px; border: none; border-radius: 3px; cursor: pointer; }
            .btn-primary { background-color: #3498db; color: white; }
            .btn-danger { background-color: #e74c3c; color: white; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🛡️ Aurora Shield Load Balancer</h1>
            <p>Multi-CDN Traffic Distribution System</p>
        </div>
        
        <div class="stats">
            <h3>📊 Statistics</h3>
            <p><strong>Uptime:</strong> {{ uptime }}</p>
            <p><strong>Total Requests:</strong> {{ stats.requests_total }}</p>
            <p><strong>Errors:</strong> {{ stats.errors }}</p>
        </div>
        
        <div class="status">
            {% for name, config in cdns.items() %}
            <div class="cdn-box {{ 'active' if config.status == 'active' else 'inactive' }}">
                <h4>{{ name|title }} CDN</h4>
                <p><strong>Status:</strong> {{ config.status|title }}</p>
                <p><strong>Weight:</strong> {{ config.weight }}</p>
                <p><strong>Requests:</strong> {{ stats.requests_by_cdn[name] }}</p>
                <p><strong>URL:</strong> {{ config.url }}</p>
            </div>
            {% endfor %}
        </div>
        
        <div class="actions">
            <h3>🎛️ Actions</h3>
            <a href="/cdn/"><button class="btn-primary">Test Load Balanced CDN</button></a>
            <a href="/cdn/primary/"><button class="btn-primary">Test Primary CDN</button></a>
            <a href="/cdn/secondary/"><button class="btn-primary">Test Secondary CDN</button></a>
            <a href="/cdn/tertiary/"><button class="btn-primary">Test Tertiary CDN</button></a>
        </div>
    </body>
    </html>
    """
    
    return render_template_string(html, 
                                cdns=CDN_SERVICES, 
                                stats=stats, 
                                uptime=str(uptime).split('.')[0])

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'load-balancer',
        'active_cdns': len([c for c in CDN_SERVICES.values() if c['status'] == 'active']),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/cdn/')
@app.route('/cdn')
def load_balanced():
    """Load balanced CDN access."""
    stats['requests_total'] += 1
    
    selected_cdn = get_weighted_cdn()
    if not selected_cdn:
        stats['errors'] += 1
        return jsonify({'error': 'No active CDN available'}), 503
    
    stats['requests_by_cdn'][selected_cdn] += 1
    
    try:
        cdn_config = CDN_SERVICES[selected_cdn]
        response = requests.get(cdn_config['url'], timeout=5)
        
        # Add load balancer headers
        response_data = response.text
        if response.headers.get('content-type', '').startswith('text/html'):
            response_data = response_data.replace(
                '<body>',
                f'<body><div style="background:#3498db;color:white;padding:10px;text-align:center;">🔀 Served by {selected_cdn.title()} CDN via Load Balancer</div>'
            )
        
        return response_data, response.status_code
        
    except requests.RequestException as e:
        logger.error(f"Error accessing {selected_cdn} CDN: {e}")
        stats['errors'] += 1
        # Mark CDN as inactive and try another
        CDN_SERVICES[selected_cdn]['status'] = 'inactive'
        return jsonify({'error': f'CDN {selected_cdn} unavailable'}), 503

@app.route('/cdn/<cdn_name>/')
@app.route('/cdn/<cdn_name>')
def direct_cdn(cdn_name):
    """Direct CDN access."""
    stats['requests_total'] += 1
    
    if cdn_name not in CDN_SERVICES:
        stats['errors'] += 1
        return jsonify({'error': f'CDN {cdn_name} not found'}), 404
    
    stats['requests_by_cdn'][cdn_name] += 1
    
    try:
        cdn_config = CDN_SERVICES[cdn_name]
        response = requests.get(cdn_config['url'], timeout=5)
        
        # Add load balancer headers
        response_data = response.text
        if response.headers.get('content-type', '').startswith('text/html'):
            response_data = response_data.replace(
                '<body>',
                f'<body><div style="background:#27ae60;color:white;padding:10px;text-align:center;">🎯 Direct access to {cdn_name.title()} CDN</div>'
            )
        
        return response_data, response.status_code
        
    except requests.RequestException as e:
        logger.error(f"Error accessing {cdn_name} CDN: {e}")
        stats['errors'] += 1
        return jsonify({'error': f'CDN {cdn_name} unavailable'}), 503

@app.route('/stats')
def get_stats():
    """Get load balancer statistics."""
    return jsonify({
        'stats': stats,
        'cdns': CDN_SERVICES,
        'uptime': str(datetime.now() - stats['start_time']).split('.')[0]
    })

if __name__ == '__main__':
    logger.info("Starting Aurora Shield Load Balancer on port 8090")
    app.run(host='0.0.0.0', port=8090, debug=False)