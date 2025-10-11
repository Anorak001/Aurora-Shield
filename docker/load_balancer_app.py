#!/usr/bin/env python3
"""
Load Balancer Service for Aurora Shield
"""

from flask import Flask, request, jsonify, render_template
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
    
    return render_template('load_balancer.html', 
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
    """Load balanced CDN access with Aurora Shield protection."""
    logger.info("=== CDN REQUEST RECEIVED ===")
    stats['requests_total'] += 1
    
    # Check with Aurora Shield first
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', '')
    logger.info(f"Processing CDN request from IP: {client_ip}")
    
    try:
        # Send request to Aurora Shield for authorization
        logger.info(f"Checking request with Aurora Shield for IP: {client_ip}")
        shield_response = requests.post(
            'http://aurora-shield:8080/api/shield/check-request',
            headers={
                'X-Original-IP': client_ip,
                'X-Original-URI': '/cdn/',
                'User-Agent': user_agent
            },
            timeout=2
        )
        
        logger.info(f"Aurora Shield response: {shield_response.status_code}")
        
        # If Aurora Shield blocks the request
        if shield_response.status_code == 403:
            logger.warning(f"Request blocked by Aurora Shield from {client_ip}")
            return jsonify({
                'error': 'Request blocked by Aurora Shield',
                'reason': 'Security policy violation'
            }), 403
            
    except requests.RequestException as e:
        logger.warning(f"Could not reach Aurora Shield: {e}, allowing request")
        # If Aurora Shield is unreachable, log but allow the request
    
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
                f'<body><div style="background:#3498db;color:white;padding:10px;text-align:center;">🔀 Served by {selected_cdn.title()} CDN via Load Balancer (Protected by Aurora Shield)</div>'
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
    """Direct CDN access with Aurora Shield protection."""
    stats['requests_total'] += 1
    
    if cdn_name not in CDN_SERVICES:
        stats['errors'] += 1
        return jsonify({'error': f'CDN {cdn_name} not found'}), 404
    
    # Check with Aurora Shield first
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', '')
    
    try:
        # Send request to Aurora Shield for authorization
        shield_response = requests.post(
            'http://aurora-shield:8080/api/shield/check-request',
            headers={
                'X-Original-IP': client_ip,
                'X-Original-URI': f'/cdn/{cdn_name}/',
                'User-Agent': user_agent
            },
            timeout=2
        )
        
        # If Aurora Shield blocks the request
        if shield_response.status_code == 403:
            logger.warning(f"Request blocked by Aurora Shield from {client_ip} for {cdn_name}")
            return jsonify({
                'error': 'Request blocked by Aurora Shield',
                'reason': 'Security policy violation'
            }), 403
            
    except requests.RequestException as e:
        logger.warning(f"Could not reach Aurora Shield: {e}, allowing request")
        # If Aurora Shield is unreachable, log but allow the request
    
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

@app.route('/api/cdn/restart', methods=['POST'])
def restart_cdn():
    """Restart a specific CDN service."""
    try:
        data = request.get_json()
        cdn_name = data.get('cdn')
        
        if not cdn_name:
            return jsonify({'error': 'CDN name is required'}), 400
            
        # Map the service names to CDN names
        service_to_cdn = {
            'demo-webapp': 'primary',
            'demo-webapp-cdn2': 'secondary', 
            'demo-webapp-cdn3': 'tertiary'
        }
        
        cdn_key = service_to_cdn.get(cdn_name)
        if not cdn_key or cdn_key not in CDN_SERVICES:
            return jsonify({'error': f'Unknown CDN service: {cdn_name}'}), 400
            
        # Simulate restart by marking as inactive then active
        CDN_SERVICES[cdn_key]['status'] = 'inactive'
        time.sleep(1)  # Simulate restart delay
        CDN_SERVICES[cdn_key]['status'] = 'active'
        
        logger.info(f"Restarted CDN service: {cdn_name} ({cdn_key})")
        
        return jsonify({
            'success': True,
            'message': f'CDN {cdn_name} restarted successfully',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error restarting CDN: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cdn/migrate', methods=['POST'])
def migrate_cdn():
    """Migrate traffic from one CDN to another."""
    try:
        data = request.get_json()
        source = data.get('source')
        destination = data.get('destination')
        
        if not source or not destination:
            return jsonify({'error': 'Both source and destination CDN names are required'}), 400
            
        if source == destination:
            return jsonify({'error': 'Source and destination must be different'}), 400
            
        # Map service names to CDN names
        service_to_cdn = {
            'demo-webapp': 'primary',
            'demo-webapp-cdn2': 'secondary',
            'demo-webapp-cdn3': 'tertiary'
        }
        
        source_key = service_to_cdn.get(source)
        dest_key = service_to_cdn.get(destination)
        
        if not source_key or source_key not in CDN_SERVICES:
            return jsonify({'error': f'Unknown source CDN: {source}'}), 400
            
        if not dest_key or dest_key not in CDN_SERVICES:
            return jsonify({'error': f'Unknown destination CDN: {destination}'}), 400
            
        # Simulate migration by temporarily disabling source and increasing destination weight
        original_source_weight = CDN_SERVICES[source_key]['weight']
        original_dest_weight = CDN_SERVICES[dest_key]['weight']
        
        # Transfer weight from source to destination
        CDN_SERVICES[source_key]['weight'] = 0
        CDN_SERVICES[dest_key]['weight'] += original_source_weight
        
        logger.info(f"Migrated traffic from {source} ({source_key}) to {destination} ({dest_key})")
        
        return jsonify({
            'success': True,
            'message': f'Traffic migrated from {source} to {destination}',
            'timestamp': datetime.now().isoformat(),
            'weights': {
                source_key: CDN_SERVICES[source_key]['weight'],
                dest_key: CDN_SERVICES[dest_key]['weight']
            }
        })
        
    except Exception as e:
        logger.error(f"Error migrating CDN: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting Aurora Shield Load Balancer on port 8090")
    app.run(host='0.0.0.0', port=8090, debug=False)