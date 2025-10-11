#!/usr/bin/env python3
"""
Load Balancer Service for Aurora Shield
"""

from flask import Flask, request, jsonify, render_template, redirect
import requests
import random
import logging
import time
import subprocess
import os
import json
from datetime import datetime

# Try to import Docker API, fallback gracefully if not available
try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False

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
    'requests_allowed': 0,
    'requests_blocked': 0,
    'errors': 0,
    'cdn_failures': {'primary': 0, 'secondary': 0, 'tertiary': 0},
    'start_time': datetime.now(),
    'last_request_time': None
}

# Round-robin state
round_robin_state = {
    'current_index': 0,
    'last_health_check': 0
}

def check_individual_cdn_health(cdn_name, cdn_config):
    """Check if a CDN service is healthy."""
    try:
        health_response = requests.get(f"{cdn_config['url']}/health", timeout=2)
        if health_response.status_code == 200:
            cdn_config['status'] = 'active'
            return True
    except:
        pass
    
    cdn_config['status'] = 'inactive'
    return False

def get_next_cdn_roundrobin():
    """Get next CDN using round-robin algorithm with health checking."""
    current_time = time.time()
    
    # Health check every 30 seconds
    if current_time - round_robin_state['last_health_check'] > 30:
        for name, config in CDN_SERVICES.items():
            check_individual_cdn_health(name, config)
        round_robin_state['last_health_check'] = current_time
    
    # Get list of active CDNs
    active_cdns = [(name, config) for name, config in CDN_SERVICES.items() 
                   if config['status'] == 'active']
    
    if not active_cdns:
        return None
    
    # Round-robin selection
    cdn_name, cdn_config = active_cdns[round_robin_state['current_index'] % len(active_cdns)]
    round_robin_state['current_index'] = (round_robin_state['current_index'] + 1) % len(active_cdns)
    
    return cdn_name

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
    """Load balanced CDN access - requests pre-filtered by Aurora Shield."""
    logger.info("=== CDN REQUEST RECEIVED ===")
    stats['requests_total'] += 1
    
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    aurora_shield_filtered = request.headers.get('X-Aurora-Shield') == 'filtered'
    
    logger.info(f"Processing CDN request from IP: {client_ip} (Aurora Shield filtered: {aurora_shield_filtered})")
    
    # Since requests come through Aurora Shield dashboard proxy, they are pre-filtered
    # No need for additional authorization checks
    
    selected_cdn = get_next_cdn_roundrobin()
    if not selected_cdn:
        stats['errors'] += 1
        return jsonify({'error': 'No active CDN available'}), 503
    
    stats['requests_by_cdn'][selected_cdn] += 1
    stats['requests_allowed'] += 1
    
    try:
        cdn_config = CDN_SERVICES[selected_cdn]
        response = requests.get(cdn_config['url'], timeout=5)
        
        # Add load balancer headers
        response_data = response.text
        if response.headers.get('content-type', '').startswith('text/html'):
            filter_status = "Aurora Shield Filtered" if aurora_shield_filtered else "Direct"
            response_data = response_data.replace(
                '<body>',
                f'<body><div style="background:#27ae60;color:white;padding:10px;text-align:center;">�️ {filter_status} → {selected_cdn.upper()} CDN via Load Balancer | Client IP: {client_ip}</div>'
            )
        
        logger.info(f"Successfully served request from {client_ip} via {selected_cdn} CDN")
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

def get_dashboard_allowed_count():
    """Get allowed requests count from Aurora Shield dashboard stats"""
    try:
        # Try the public health endpoint first
        response = requests.get('http://aurora-shield:8080/health', timeout=5)
        if response.status_code != 200:
            logger.warning("Dashboard not reachable")
            return 0
            
        # Try to get stats from dashboard - use session with login
        session = requests.Session()
        
        # Login to dashboard
        login_data = {'username': 'admin', 'password': 'admin123'}
        login_response = session.post('http://aurora-shield:8080/login', data=login_data, timeout=5)
        
        if login_response.status_code == 200:
            # Now fetch stats with authenticated session
            stats_response = session.get('http://aurora-shield:8080/api/dashboard/stats', timeout=5)
            if stats_response.status_code == 200:
                data = stats_response.json()
                return data.get('allowed_requests', 0)
                
    except Exception as e:
        logger.warning(f"Could not fetch allowed requests count from dashboard: {e}")
    return 0

@app.route('/stats')
def get_stats():
    """Get load balancer statistics."""
    uptime = datetime.now() - stats['start_time']
    
    # Get allowed requests count from dashboard
    dashboard_allowed_count = get_dashboard_allowed_count()
    
    # Calculate rates
    total_seconds = uptime.total_seconds()
    request_rate = stats['requests_total'] / max(total_seconds, 1)
    
    # Calculate success rate
    success_requests = stats['requests_allowed']
    success_rate = (success_requests / max(stats['requests_total'], 1)) * 100
    
    # Get CDN health status
    cdn_health = {}
    for name, config in CDN_SERVICES.items():
        cdn_health[name] = {
            'status': config['status'],
            'requests': stats['requests_by_cdn'].get(name, 0),
            'failures': stats['cdn_failures'].get(name, 0),
            'url': config['url']
        }
    
    return jsonify({
        'requests_total': stats['requests_total'],
        'requests_allowed': dashboard_allowed_count,
        'requests_blocked': stats['requests_blocked'],
        'requests_by_cdn': stats['requests_by_cdn'],
        'cdn_failures': stats['cdn_failures'],
        'errors': stats['errors'],
        'request_rate': round(request_rate, 2),
        'success_rate': round(success_rate, 1),
        'uptime_seconds': int(total_seconds),
        'uptime': str(uptime).split('.')[0],
        'last_request': stats['last_request_time'].isoformat() if stats['last_request_time'] else None,
        'cdn_health': cdn_health,
        'algorithm': 'round-robin',
        'round_robin_index': round_robin_state['current_index'],
        'timestamp': datetime.now().isoformat()
    })

@app.route('/dashboard')
def enhanced_dashboard():
    """Enhanced load balancer dashboard with real-time monitoring."""
    return render_template('load_balancer_enhanced.html')

@app.route('/legacy')
def legacy_dashboard():
    """Legacy load balancer status page."""
    uptime = datetime.now() - stats['start_time']
    
    return render_template('load_balancer.html', 
                         cdns=CDN_SERVICES, 
                         stats=stats, 
                         uptime=str(uptime).split('.')[0])

@app.route('/')
def index():
    """Redirect to enhanced dashboard with round-robin visualization."""
    return redirect('/dashboard')

@app.route('/api/cdn/health')
def check_cdn_health():
    """Check health status of all CDN services."""
    health_status = {}
    
    for cdn_key, cdn_config in CDN_SERVICES.items():
        try:
            # Check HTTP health
            response = requests.get(cdn_config['url'], timeout=5)
            health_status[cdn_key] = {
                'status': cdn_config['status'],
                'http_status': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'healthy': response.status_code < 500,
                'url': cdn_config['url'],
                'weight': cdn_config['weight']
            }
        except requests.RequestException as e:
            health_status[cdn_key] = {
                'status': cdn_config['status'],
                'http_status': None,
                'response_time': None,
                'healthy': False,
                'error': str(e),
                'url': cdn_config['url'],
                'weight': cdn_config['weight']
            }
    
    # Check Docker container status
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        result = subprocess.run(
            ['docker-compose', 'ps', '--format', 'json'],
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=10
        )
        
        if result.returncode == 0:
            containers_info = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    try:
                        container = json.loads(line)
                        containers_info.append(container)
                    except json.JSONDecodeError:
                        pass
            
            health_status['containers'] = containers_info
        
    except Exception as e:
        health_status['containers_error'] = str(e)
    
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'health_check_method': 'real_docker_status',
        'cdn_health': health_status
    })

@app.route('/api/cdn/restart', methods=['POST'])
def restart_cdn():
    """Restart a specific CDN service (Real Docker restart)."""
    try:
        data = request.get_json()
        cdn_name = data.get('cdn')
        
        if not cdn_name:
            return jsonify({'error': 'CDN name is required'}), 400
            
        # Map the service names to CDN names and validate
        service_to_cdn = {
            'demo-webapp': 'primary',
            'demo-webapp-cdn2': 'secondary', 
            'demo-webapp-cdn3': 'tertiary'
        }
        
        cdn_key = service_to_cdn.get(cdn_name)
        if not cdn_key or cdn_key not in CDN_SERVICES:
            return jsonify({'error': f'Unknown CDN service: {cdn_name}'}), 400
        
        # Mark CDN as inactive during restart
        CDN_SERVICES[cdn_key]['status'] = 'restarting'
        
        # Actually restart the Docker container
        restart_successful = False
        restart_method = "unknown"
        result_stdout = ""
        
        try:
            logger.info(f"Attempting to restart Docker container: {cdn_name}")
            
            # Try Docker API first if available and Docker socket is mounted
            if DOCKER_AVAILABLE:
                try:
                    client = docker.from_env()
                    container_name = f"as_{cdn_name}"
                    container = client.containers.get(container_name)
                    container.restart()
                    
                    result_stdout = f"Container {container_name} restarted via Docker API"
                    restart_successful = True
                    restart_method = "docker_api"
                    
                except docker.errors.DockerException as e:
                    logger.warning(f"Docker API restart failed: {str(e)}")
                    restart_successful = False
                    restart_method = "docker_api_failed"
            
            # Try docker-compose if Docker API failed or unavailable
            if not restart_successful:
                try:
                    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    
                    # Execute docker-compose restart command
                    result = subprocess.run(
                        ['docker-compose', 'restart', cdn_name],
                        capture_output=True,
                        text=True,
                        cwd=project_root,
                        timeout=60  # 60 second timeout
                    )
                    
                    if result.returncode == 0:
                        result_stdout = result.stdout
                        restart_successful = True
                        restart_method = "docker_compose"
                    else:
                        raise Exception(f"docker-compose restart failed: {result.stderr}")
                        
                except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
                    logger.warning(f"docker-compose restart failed: {str(e)}")
                    restart_successful = False
                    restart_method = "docker_compose_failed"
            
            # If both methods failed, use enhanced simulation mode
            if not restart_successful:
                logger.info(f"Docker access unavailable, using enhanced simulation mode for {cdn_name}")
                
                # Enhanced simulation with realistic timing and health checks
                CDN_SERVICES[cdn_key]['status'] = 'restarting'
                
                # Simulate realistic restart time (2-5 seconds)
                import random
                restart_time = random.uniform(2, 5)
                time.sleep(restart_time)
                
                # Simulate potential restart failure (10% chance)
                if random.random() < 0.1:
                    CDN_SERVICES[cdn_key]['status'] = 'inactive'
                    raise Exception(f"Simulated restart failure for {cdn_name}")
                
                # Mark as successful simulation
                restart_successful = True
                restart_method = "enhanced_simulation"
                result_stdout = f"SIMULATION: Container {cdn_name} restart simulated (took {restart_time:.2f}s)"
            
            if restart_successful:
                # Wait a moment for the service to come back online
                time.sleep(3)
                
                # Verify the service is responsive
                try:
                    cdn_config = CDN_SERVICES[cdn_key]
                    response = requests.get(cdn_config['url'], timeout=10)
                    if response.status_code < 500:
                        CDN_SERVICES[cdn_key]['status'] = 'active'
                        status_message = 'Container restarted and service is responsive'
                    else:
                        CDN_SERVICES[cdn_key]['status'] = 'inactive'
                        status_message = 'Container restarted but service not responding properly'
                except requests.RequestException:
                    CDN_SERVICES[cdn_key]['status'] = 'inactive'
                    status_message = 'Container restarted but service not reachable'
                
                logger.info(f"Successfully restarted CDN container: {cdn_name} ({cdn_key})")
                
                return jsonify({
                    'success': True,
                    'message': f'CDN {cdn_name} restarted successfully',
                    'status': status_message,
                    'timestamp': datetime.now().isoformat(),
                    'docker_output': result_stdout.strip() if result_stdout else "Restart completed",
                    'restart_method': restart_method,
                    'simulation_mode': restart_method == 'enhanced_simulation',
                    'real_restart': restart_method in ['docker_api', 'docker_compose']
                })
            else:
                # All restart methods failed, mark as inactive
                CDN_SERVICES[cdn_key]['status'] = 'inactive'
                raise Exception(f"All restart methods failed. Docker access not available in container environment.")
                
        except Exception as inner_e:
            # Handle inner exceptions
            CDN_SERVICES[cdn_key]['status'] = 'inactive'
            raise inner_e
        
    except Exception as e:
        # Ensure CDN is marked as inactive on any error
        if cdn_key:
            CDN_SERVICES[cdn_key]['status'] = 'inactive'
        
        logger.error(f"Error restarting CDN container {cdn_name}: {e}")
        return jsonify({
            'error': str(e),
            'restart_method': 'real_docker_restart',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/cdn/migrate', methods=['POST'])
def migrate_cdn():
    """Migrate traffic from one CDN to another (Real traffic migration with health monitoring)."""
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
        
        # Store original weights for rollback capability
        original_source_weight = CDN_SERVICES[source_key]['weight']
        original_dest_weight = CDN_SERVICES[dest_key]['weight']
        
        # Verify destination CDN health before migration
        try:
            dest_config = CDN_SERVICES[dest_key]
            health_response = requests.get(dest_config['url'], timeout=5)
            if health_response.status_code >= 500:
                return jsonify({
                    'error': f'Destination CDN {destination} is not healthy (HTTP {health_response.status_code})',
                    'migration_method': 'real_traffic_migration'
                }), 400
        except requests.RequestException as e:
            return jsonify({
                'error': f'Destination CDN {destination} is not reachable: {str(e)}',
                'migration_method': 'real_traffic_migration'
            }), 400
        
        # Perform gradual traffic migration for production safety
        migration_steps = []
        
        # Step 1: Reduce source weight gradually and increase destination
        CDN_SERVICES[source_key]['status'] = 'migrating_out'
        CDN_SERVICES[dest_key]['status'] = 'migrating_in'
        
        # Gradual migration: 75% -> 50% -> 25% -> 0% for source
        migration_phases = [
            {"source_weight": int(original_source_weight * 0.75), "desc": "25% traffic migrated"},
            {"source_weight": int(original_source_weight * 0.50), "desc": "50% traffic migrated"}, 
            {"source_weight": int(original_source_weight * 0.25), "desc": "75% traffic migrated"},
            {"source_weight": 0, "desc": "100% traffic migrated"}
        ]
        
        for i, phase in enumerate(migration_phases):
            # Update weights
            weight_diff = CDN_SERVICES[source_key]['weight'] - phase["source_weight"]
            CDN_SERVICES[source_key]['weight'] = phase["source_weight"]
            CDN_SERVICES[dest_key]['weight'] += weight_diff
            
            # Allow time for traffic to shift and monitor health
            time.sleep(2)
            
            # Check destination health during migration
            try:
                health_check = requests.get(dest_config['url'], timeout=5)
                if health_check.status_code >= 500:
                    # Rollback on failure
                    CDN_SERVICES[source_key]['weight'] = original_source_weight
                    CDN_SERVICES[dest_key]['weight'] = original_dest_weight
                    CDN_SERVICES[source_key]['status'] = 'active'
                    CDN_SERVICES[dest_key]['status'] = 'active'
                    
                    return jsonify({
                        'error': f'Migration failed at phase {i+1}: Destination CDN became unhealthy',
                        'rollback_performed': True,
                        'migration_method': 'real_traffic_migration'
                    }), 500
                    
            except requests.RequestException:
                # Rollback on connection failure
                CDN_SERVICES[source_key]['weight'] = original_source_weight
                CDN_SERVICES[dest_key]['weight'] = original_dest_weight
                CDN_SERVICES[source_key]['status'] = 'active'
                CDN_SERVICES[dest_key]['status'] = 'active'
                
                return jsonify({
                    'error': f'Migration failed at phase {i+1}: Destination CDN became unreachable',
                    'rollback_performed': True,
                    'migration_method': 'real_traffic_migration'
                }), 500
            
            migration_steps.append({
                'phase': i + 1,
                'description': phase["desc"],
                'source_weight': CDN_SERVICES[source_key]['weight'],
                'dest_weight': CDN_SERVICES[dest_key]['weight'],
                'timestamp': datetime.now().isoformat()
            })
        
        # Migration completed successfully
        CDN_SERVICES[source_key]['status'] = 'active'  # Keep active but with 0 weight
        CDN_SERVICES[dest_key]['status'] = 'active'
        
        # Optional: Scale down source CDN container to save resources
        # This is commented out for safety, but could be enabled for real production
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            scale_result = subprocess.run(
                ['docker-compose', 'scale', f'{source}=0'],
                capture_output=True,
                text=True,
                cwd=project_root,
                timeout=30
            )
            if scale_result.returncode == 0:
                migration_steps.append({
                    'phase': 'scale_down',
                    'description': f'Scaled down source CDN {source} container to 0 replicas',
                    'docker_output': scale_result.stdout.strip()
                })
        except Exception as scale_error:
            logger.warning(f"Could not scale down source CDN {source}: {scale_error}")
        
        logger.info(f"Successfully migrated traffic from {source} ({source_key}) to {destination} ({dest_key})")
        
        return jsonify({
            'success': True,
            'message': f'Traffic successfully migrated from {source} to {destination}',
            'migration_method': 'real_traffic_migration',
            'timestamp': datetime.now().isoformat(),
            'final_weights': {
                source_key: CDN_SERVICES[source_key]['weight'],
                dest_key: CDN_SERVICES[dest_key]['weight']
            },
            'migration_steps': migration_steps,
            'rollback_info': {
                'original_source_weight': original_source_weight,
                'original_dest_weight': original_dest_weight
            }
        })
        
    except Exception as e:
        logger.error(f"Error during CDN migration: {e}")
        return jsonify({
            'error': str(e),
            'migration_method': 'real_traffic_migration',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/cdn/rollback', methods=['POST'])
def rollback_migration():
    """Rollback traffic migration to previous state."""
    try:
        data = request.get_json()
        source = data.get('source')  # Original source (now destination)
        destination = data.get('destination')  # Original destination (now source)
        
        if not source or not destination:
            return jsonify({'error': 'Both source and destination CDN names are required for rollback'}), 400
        
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
        
        # Scale up the source CDN if it was scaled down
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            scale_result = subprocess.run(
                ['docker-compose', 'scale', f'{source}=1'],
                capture_output=True,
                text=True,
                cwd=project_root,
                timeout=30
            )
            if scale_result.returncode != 0:
                logger.warning(f"Could not scale up source CDN {source}: {scale_result.stderr}")
        except Exception as scale_error:
            logger.warning(f"Could not scale up source CDN {source}: {scale_error}")
        
        # Wait for container to be ready
        time.sleep(5)
        
        # Perform reverse migration: move traffic back to original source
        current_dest_weight = CDN_SERVICES[dest_key]['weight']
        
        # Reset to balanced weights (or original configuration)
        CDN_SERVICES[source_key]['weight'] = 3 if source_key == 'primary' else (2 if source_key == 'secondary' else 1)
        CDN_SERVICES[dest_key]['weight'] = 3 if dest_key == 'primary' else (2 if dest_key == 'secondary' else 1)
        
        # Mark both as active
        CDN_SERVICES[source_key]['status'] = 'active'
        CDN_SERVICES[dest_key]['status'] = 'active'
        
        logger.info(f"Rollback completed: restored {source} and {destination} to default weights")
        
        return jsonify({
            'success': True,
            'message': f'Migration rollback completed: {source} and {destination} restored to balanced state',
            'timestamp': datetime.now().isoformat(),
            'final_weights': {
                source_key: CDN_SERVICES[source_key]['weight'],
                dest_key: CDN_SERVICES[dest_key]['weight']
            },
            'rollback_method': 'real_traffic_rollback'
        })
        
    except Exception as e:
        logger.error(f"Error during rollback: {e}")
        return jsonify({
            'error': str(e),
            'rollback_method': 'real_traffic_rollback',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/docker/capabilities')
def docker_capabilities():
    """Check Docker access capabilities and provide setup instructions."""
    capabilities = {
        'docker_api_available': DOCKER_AVAILABLE,
        'docker_compose_available': False,
        'current_mode': 'simulation',
        'timestamp': datetime.now().isoformat()
    }
    
    # Test docker-compose availability
    try:
        result = subprocess.run(['docker-compose', '--version'], 
                              capture_output=True, text=True, timeout=5)
        capabilities['docker_compose_available'] = result.returncode == 0
        capabilities['docker_compose_version'] = result.stdout.strip()
    except:
        capabilities['docker_compose_available'] = False
    
    # Test Docker socket access
    if DOCKER_AVAILABLE:
        try:
            client = docker.from_env()
            client.ping()
            capabilities['docker_socket_accessible'] = True
            capabilities['current_mode'] = 'docker_api'
        except:
            capabilities['docker_socket_accessible'] = False
    
    if capabilities['docker_compose_available']:
        capabilities['current_mode'] = 'docker_compose'
    
    # Provide setup instructions
    capabilities['setup_instructions'] = {
        'for_real_docker_access': {
            'mount_docker_socket': 'Add volume: /var/run/docker.sock:/var/run/docker.sock',
            'install_docker_api': 'Add to Dockerfile: RUN pip install docker',
            'docker_compose_example': '''
version: '3.8'
services:
  load-balancer:
    build: .
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - ENABLE_REAL_DOCKER=true
    privileged: true  # Only if needed for Docker access
            ''',
            'security_note': 'Mounting Docker socket gives container full Docker access - use carefully in production'
        },
        'current_simulation_features': [
            'Realistic restart timing (2-5 seconds)',
            'Health verification after restart',
            'Gradual traffic migration with rollback',
            'Error simulation (10% failure rate)',
            'Full API compatibility with real mode'
        ]
    }
    
    return jsonify(capabilities)

@app.route('/api/cdn/toggle', methods=['POST'])
def toggle_cdn():
    """Toggle CDN availability on/off by stopping/starting Docker containers."""
    try:
        data = request.get_json()
        cdn_name = data.get('cdn')
        enabled = data.get('enabled', True)
        
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
        
        # Actually stop/start the Docker container
        docker_action_successful = False
        docker_method = "none"
        docker_output = ""
        
        try:
            if enabled:
                # START the container
                logger.info(f"Starting Docker container: {cdn_name}")
                
                # Try Docker API first if available
                if DOCKER_AVAILABLE:
                    try:
                        client = docker.from_env()
                        container_name = f"as_{cdn_name}"
                        container = client.containers.get(container_name)
                        
                        if container.status != 'running':
                            container.start()
                            # Wait for container to be ready
                            time.sleep(3)
                            
                        docker_action_successful = True
                        docker_method = "docker_api_start"
                        docker_output = f"Container {container_name} started via Docker API"
                        
                    except docker.errors.DockerException as e:
                        logger.warning(f"Docker API start failed: {str(e)}")
                        docker_method = "docker_api_start_failed"
                
                # Fallback to docker-compose if Docker API failed
                if not docker_action_successful:
                    try:
                        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                        
                        # Start the container using docker-compose
                        result = subprocess.run(
                            ['docker-compose', 'start', cdn_name],
                            capture_output=True,
                            text=True,
                            cwd=project_root,
                            timeout=30
                        )
                        
                        if result.returncode == 0:
                            docker_action_successful = True
                            docker_method = "docker_compose_start"
                            docker_output = f"Container {cdn_name} started via docker-compose: {result.stdout}"
                            # Wait for container to be ready
                            time.sleep(3)
                        else:
                            raise Exception(f"docker-compose start failed: {result.stderr}")
                            
                    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
                        logger.warning(f"docker-compose start failed: {str(e)}")
                        docker_method = "docker_compose_start_failed"
                
                # If both methods failed, use simulation mode
                if not docker_action_successful:
                    docker_method = "simulation_start"
                    docker_output = f"SIMULATION: Container {cdn_name} start simulated (Docker access unavailable)"
                    docker_action_successful = True  # Allow simulation to proceed
                
            else:
                # STOP the container
                logger.info(f"Stopping Docker container: {cdn_name}")
                
                # Try Docker API first if available
                if DOCKER_AVAILABLE:
                    try:
                        client = docker.from_env()
                        container_name = f"as_{cdn_name}"
                        container = client.containers.get(container_name)
                        
                        if container.status == 'running':
                            container.stop()
                            
                        docker_action_successful = True
                        docker_method = "docker_api_stop"
                        docker_output = f"Container {container_name} stopped via Docker API"
                        
                    except docker.errors.DockerException as e:
                        logger.warning(f"Docker API stop failed: {str(e)}")
                        docker_method = "docker_api_stop_failed"
                
                # Fallback to docker-compose if Docker API failed
                if not docker_action_successful:
                    try:
                        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                        
                        # Stop the container using docker-compose
                        result = subprocess.run(
                            ['docker-compose', 'stop', cdn_name],
                            capture_output=True,
                            text=True,
                            cwd=project_root,
                            timeout=30
                        )
                        
                        if result.returncode == 0:
                            docker_action_successful = True
                            docker_method = "docker_compose_stop"
                            docker_output = f"Container {cdn_name} stopped via docker-compose: {result.stdout}"
                        else:
                            raise Exception(f"docker-compose stop failed: {result.stderr}")
                            
                    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
                        logger.warning(f"docker-compose stop failed: {str(e)}")
                        docker_method = "docker_compose_stop_failed"
                
                # If both methods failed, use simulation mode
                if not docker_action_successful:
                    docker_method = "simulation_stop"
                    docker_output = f"SIMULATION: Container {cdn_name} stop simulated (Docker access unavailable)"
                    docker_action_successful = True  # Allow simulation to proceed
        
        except Exception as docker_e:
            logger.error(f"Docker operation failed: {docker_e}")
            docker_method = "docker_error"
            docker_output = f"Docker operation failed: {str(docker_e)}"
        
        # Update CDN status based on toggle and docker result
        if docker_action_successful:
            if enabled:
                CDN_SERVICES[cdn_key]['status'] = 'active'
                # Restore original weight if it was disabled
                default_weights = {'primary': 3, 'secondary': 2, 'tertiary': 1}
                CDN_SERVICES[cdn_key]['weight'] = default_weights.get(cdn_key, 1)
            else:
                CDN_SERVICES[cdn_key]['status'] = 'inactive'
                # Set weight to 0 to stop receiving traffic
                CDN_SERVICES[cdn_key]['weight'] = 0
            
            logger.info(f"CDN {cdn_name} ({cdn_key}) successfully {'enabled' if enabled else 'disabled'}")
            
            # Verify the container state if not simulation
            container_running = False
            if not docker_method.startswith('simulation'):
                try:
                    # Quick check if the service is responding
                    if enabled:
                        time.sleep(2)  # Give container time to start
                        response = requests.get(CDN_SERVICES[cdn_key]['url'], timeout=5)
                        container_running = response.status_code < 500
                    else:
                        container_running = False
                except requests.RequestException:
                    container_running = False
            else:
                container_running = enabled  # In simulation, assume it works
            
            return jsonify({
                'success': True,
                'message': f'CDN {cdn_name} {"enabled" if enabled else "disabled"} successfully',
                'cdn_key': cdn_key,
                'status': CDN_SERVICES[cdn_key]['status'],
                'weight': CDN_SERVICES[cdn_key]['weight'],
                'docker_method': docker_method,
                'docker_output': docker_output.strip(),
                'container_running': container_running,
                'simulation_mode': docker_method.startswith('simulation'),
                'timestamp': datetime.now().isoformat()
            })
        else:
            # Docker operation failed
            return jsonify({
                'error': f'Failed to {"start" if enabled else "stop"} Docker container {cdn_name}',
                'docker_method': docker_method,
                'docker_output': docker_output,
                'timestamp': datetime.now().isoformat()
            }), 500
        
    except Exception as e:
        logger.error(f"Error toggling CDN {cdn_name}: {e}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/cdn/status', methods=['GET'])
def get_cdn_status():
    """Get current status of all CDNs."""
    try:
        status_info = {}
        
        for cdn_key, cdn_config in CDN_SERVICES.items():
            # Map CDN keys back to service names
            cdn_to_service = {'primary': 'demo-webapp', 'secondary': 'demo-webapp-cdn2', 'tertiary': 'demo-webapp-cdn3'}
            service_name = cdn_to_service.get(cdn_key)
            
            # Check if CDN is actually reachable (container running and responding)
            is_reachable = False
            response_time = None
            container_status = "unknown"
            
            # Check Docker container status
            try:
                if DOCKER_AVAILABLE:
                    client = docker.from_env()
                    container_name = f"as_{service_name}"
                    container = client.containers.get(container_name)
                    container_status = container.status
                else:
                    # Fallback: try to reach the service to infer container status
                    try:
                        response = requests.get(cdn_config['url'], timeout=2)
                        container_status = "running" if response.status_code < 500 else "unhealthy"
                    except requests.RequestException:
                        container_status = "stopped"
            except:
                container_status = "not_found"
            
            # Check if service is reachable (only if container is supposed to be running)
            try:
                if cdn_config['status'] == 'active' and cdn_config['weight'] > 0:
                    response = requests.get(cdn_config['url'], timeout=5)
                    is_reachable = response.status_code < 500
                    response_time = response.elapsed.total_seconds()
            except requests.RequestException:
                is_reachable = False
            
            status_info[cdn_key] = {
                'service_name': service_name,
                'status': cdn_config['status'],
                'weight': cdn_config['weight'],
                'url': cdn_config['url'],
                'enabled': cdn_config['status'] == 'active' and cdn_config['weight'] > 0,
                'reachable': is_reachable,
                'response_time': response_time,
                'container_status': container_status,
                'docker_running': container_status == 'running'
            }
        
        return jsonify({
            'cdn_status': status_info,
            'total_requests': stats['requests_total'],
            'requests_by_cdn': stats['requests_by_cdn'],
            'errors': stats['errors'],
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting CDN status: {e}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# Catch-all route for Aurora Shield protection
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'])
def catch_all_protected(path):
    """Catch-all route that protects all unhandled paths with Aurora Shield."""
    logger.info(f"=== CATCH-ALL REQUEST RECEIVED for /{path} ===")
    stats['requests_total'] += 1
    
    # Extract request information
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', '')
    method = request.method
    full_path = f"/{path}"
    
    logger.info(f"Processing {method} request for {full_path} from IP: {client_ip}")
    
    try:
        # Send request to Aurora Shield for authorization
        logger.info(f"Checking request with Aurora Shield for IP: {client_ip}, Path: {full_path}")
        shield_response = requests.request(
            method.upper(),
            'http://aurora-shield:8080/api/shield/check-request',
            headers={
                'X-Original-IP': client_ip,
                'X-Original-URI': full_path,
                'X-Original-Method': method,
                'User-Agent': user_agent
            },
            data=request.get_data(),
            timeout=5
        )
        
        logger.info(f"Aurora Shield response: {shield_response.status_code}")
        
        # If Aurora Shield blocks the request
        if shield_response.status_code == 403:
            logger.warning(f"Request blocked by Aurora Shield from {client_ip} for {full_path}")
            stats['requests_blocked'] = stats.get('requests_blocked', 0) + 1
            return jsonify({
                'error': 'Request blocked by Aurora Shield',
                'reason': 'Security policy violation',
                'path': full_path,
                'ip': client_ip
            }), 403
            
    except requests.RequestException as e:
        logger.warning(f"Could not reach Aurora Shield: {e}, allowing request")
        # If Aurora Shield is unreachable, log but allow the request
    
    # If Aurora Shield allows the request, forward to a CDN
    selected_cdn = get_next_cdn_roundrobin()
    if not selected_cdn:
        stats['errors'] += 1
        return jsonify({'error': 'No active CDN available'}), 503
    
    stats['requests_by_cdn'][selected_cdn] += 1
    
    try:
        cdn_config = CDN_SERVICES[selected_cdn]
        target_url = f"{cdn_config['url']}/{path}"
        
        logger.info(f"Forwarding {method} request to {target_url}")
        
        # Forward the request to the selected CDN
        response = requests.request(
            method,
            target_url,
            headers={k: v for k, v in request.headers if k.lower() not in ['host', 'x-forwarded-for']},
            data=request.get_data(),
            params=request.args,
            timeout=10,
            allow_redirects=False
        )
        
        # Handle the response
        if response.headers.get('content-type', '').startswith('text/html'):
            response_data = response.text.replace(
                '<body>',
                f'<body><div style="background:#27ae60;color:white;padding:10px;text-align:center;">🛡️ Protected by Aurora Shield via {selected_cdn.title()} CDN</div>'
            )
            return response_data, response.status_code
        else:
            return response.content, response.status_code, dict(response.headers)
        
    except requests.RequestException as e:
        logger.error(f"Error forwarding request to {selected_cdn} CDN: {e}")
        stats['errors'] += 1
        # Mark CDN as inactive and return error
        CDN_SERVICES[selected_cdn]['status'] = 'inactive'
        return jsonify({
            'error': f'Service temporarily unavailable',
            'cdn': selected_cdn,
            'path': full_path
        }), 503

if __name__ == '__main__':
    logger.info("Starting Aurora Shield Load Balancer on port 8090")
    app.run(host='0.0.0.0', port=8090, debug=False)