#!/usr/bin/env python3
"""
Aurora Shield Service Dashboard
A simple web interface to monitor and manage Aurora Shield services
"""

from flask import Flask, render_template, jsonify, request
import docker
import requests
import json
from datetime import datetime
import subprocess
import os

app = Flask(__name__)
client = docker.from_env()

# Service configuration
SERVICES = {
    'aurora-shield': {
        'name': 'Aurora Shield',
        'port': 8080,
        'health_endpoint': '/health',
        'description': 'Main DDoS protection service'
    },
    'demo-webapp': {
        'name': 'Protected Web App',
        'port': 80,
        'health_endpoint': '/',
        'description': 'Demo application protected by Aurora Shield'
    },
    'load-balancer': {
        'name': 'Load Balancer',
        'port': 8090,
        'health_endpoint': '/',
        'description': 'Nginx load balancer'
    },
    'elasticsearch': {
        'name': 'Elasticsearch',
        'port': 9200,
        'health_endpoint': '/_cluster/health',
        'description': 'Log storage and search'
    },
    'kibana': {
        'name': 'Kibana',
        'port': 5601,
        'health_endpoint': '/api/status',
        'description': 'Log visualization'
    },
    'prometheus': {
        'name': 'Prometheus',
        'port': 9090,
        'health_endpoint': '/api/v1/status/flags',
        'description': 'Metrics collection'
    },
    'grafana': {
        'name': 'Grafana',
        'port': 3000,
        'health_endpoint': '/api/health',
        'description': 'Metrics visualization'
    },
    'redis': {
        'name': 'Redis',
        'port': 6379,
        'health_endpoint': None,  # TCP check only
        'description': 'Caching and session storage'
    },
    'client': {
        'name': 'Attack Simulator',
        'port': 5001,
        'health_endpoint': '/api/status',
        'description': 'Web-based attack simulation interface'
    }
}

def get_service_status():
    """Get status of all Aurora Shield services"""
    status = {}
    
    try:
        # Get containers
        containers = client.containers.list(all=True, filters={'label': 'com.docker.compose.project=as'})
        
        for container in containers:
            service_name = container.labels.get('com.docker.compose.service', 'unknown')
            if service_name in SERVICES:
                # Basic container info
                status[service_name] = {
                    'container_id': container.short_id,
                    'status': container.status,
                    'image': container.image.tags[0] if container.image.tags else 'unknown',
                    'created': container.attrs['Created'],
                    'health': 'unknown'
                }
                
                # Check health endpoint if service is running
                if container.status == 'running' and SERVICES[service_name]['port']:
                    port = SERVICES[service_name]['port']
                    endpoint = SERVICES[service_name]['health_endpoint']
                    
                    if endpoint:
                        try:
                            response = requests.get(f'http://localhost:{port}{endpoint}', timeout=5)
                            status[service_name]['health'] = 'healthy' if response.status_code < 400 else 'unhealthy'
                            status[service_name]['response_time'] = response.elapsed.total_seconds()
                        except:
                            status[service_name]['health'] = 'unreachable'
                    else:
                        # For Redis, try TCP connection
                        try:
                            import socket
                            sock = socket.create_connection(('localhost', port), timeout=5)
                            sock.close()
                            status[service_name]['health'] = 'healthy'
                        except:
                            status[service_name]['health'] = 'unreachable'
                            
    except Exception as e:
        print(f"Error getting service status: {e}")
    
    return status

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html', services=SERVICES)

@app.route('/api/status')
def api_status():
    """API endpoint for service status"""
    return jsonify(get_service_status())

@app.route('/api/logs/<service>')
def api_logs(service):
    """Get logs for a specific service"""
    try:
        result = subprocess.run(['docker-compose', 'logs', '--tail=100', service], 
                              capture_output=True, text=True, cwd=os.path.dirname(__file__))
        return {'logs': result.stdout, 'error': result.stderr}
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/api/restart/<service>', methods=['POST'])
def api_restart(service):
    """Restart a specific service"""
    try:
        result = subprocess.run(['docker-compose', 'restart', service], 
                              capture_output=True, text=True, cwd=os.path.dirname(__file__))
        return {'success': True, 'output': result.stdout}
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/api/client/start', methods=['POST'])
def api_start_client():
    """Start the client simulator"""
    try:
        result = subprocess.run(['docker-compose', 'run', '--rm', 'client'], 
                              capture_output=True, text=True, cwd=os.path.dirname(__file__))
        return {'success': True, 'output': result.stdout}
    except Exception as e:
        return {'error': str(e)}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)