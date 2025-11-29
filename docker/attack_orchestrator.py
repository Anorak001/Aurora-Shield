#!/usr/bin/env python3
"""
Attack Orchestrator Dashboard
Manages fleet of bot containers for realistic DDoS simulation
"""

from flask import Flask, request, jsonify, render_template
import subprocess
import threading
import time
import json
import random
import socket
from datetime import datetime
from collections import defaultdict

app = Flask(__name__, template_folder='templates')

# Fleet state management
fleet_state = {
    'bots': {},  # bot_id -> {container_name, ip, status, stats}
    'attacks': {},  # attack_id -> {type, config, start_time, bots}
    'total_spawned': 0,
    'total_destroyed': 0,
    'last_cleanup': time.time()
}

# Attack statistics
attack_stats = {
    'requests_sent': 0,
    'requests_successful': 0,
    'requests_blocked': 0,
    'bytes_sent': 0,
    'attack_duration': 0,
    'start_time': None
}

def get_next_bot_ip():
    """Generate next available bot IP in range 10.77.0.50-250"""
    base_ip = "10.77.0."
    used_ips = {bot['ip'].split('.')[-1] for bot in fleet_state['bots'].values() if 'ip' in bot}
    
    for i in range(50, 251):
        if str(i) not in used_ips:
            return f"{base_ip}{i}"
    
    # Fallback: random IP in range
    return f"{base_ip}{random.randint(50, 250)}"

def generate_bot_name():
    """Generate unique bot container name"""
    fleet_state['total_spawned'] += 1
    return f"aurora-bot-{fleet_state['total_spawned']:03d}"

@app.route('/')
def dashboard():
    """Main orchestrator dashboard"""
    return render_template('orchestrator_dashboard.html')

@app.route('/api/fleet/status')
def fleet_status():
    """Get current fleet status and statistics"""
    # Clean up stale bots (check containers every 30s)
    current_time = time.time()
    if current_time - fleet_state['last_cleanup'] > 30:
        cleanup_stale_bots()
        fleet_state['last_cleanup'] = current_time
    
    active_bots = len([b for b in fleet_state['bots'].values() if b.get('status') == 'active'])
    
    return jsonify({
        'active_bots': active_bots,
        'total_bots': len(fleet_state['bots']),
        'bots': fleet_state['bots'],
        'attacks': fleet_state['attacks'],
        'stats': attack_stats,
        'fleet_health': calculate_fleet_health(),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/fleet/spawn', methods=['POST'])
def spawn_bots():
    """Spawn N bot containers with unique IPs"""
    try:
        data = request.get_json() or {}
        count = int(data.get('count', 10))
        attack_type = data.get('attack_type', 'http_flood')
        target_url = data.get('target_url', 'http://aurora-shield:8080/proxy/cdn/')
        
        if count > 50:
            return jsonify({'error': 'Maximum 50 bots allowed for safety'}), 400
        
        spawned_bots = []
        failed_spawns = []
        
        for i in range(count):
            try:
                bot_name = generate_bot_name()
                bot_ip = get_next_bot_ip()
                
                # Create bot container
                result = subprocess.run([
                    'docker', 'run', '-d',
                    '--name', bot_name,
                    '--network', 'aurora-net',
                    '-e', f'BOT_IP={bot_ip}',
                    '-e', f'TARGET_URL={target_url}',
                    '-e', f'ATTACK_TYPE={attack_type}',
                    '-e', f'ORCHESTRATOR_URL=http://attack-orchestrator:5000',
                    'aurora-shield-bot-agent'
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    container_id = result.stdout.strip()
                    
                    # Register bot in fleet
                    bot_id = f"bot_{len(fleet_state['bots']) + 1:03d}"
                    fleet_state['bots'][bot_id] = {
                        'container_name': bot_name,
                        'container_id': container_id,
                        'ip': bot_ip,
                        'status': 'spawning',
                        'attack_type': attack_type,
                        'target_url': target_url,
                        'created_at': datetime.now().isoformat(),
                        'requests_sent': 0,
                        'last_heartbeat': time.time()
                    }
                    
                    spawned_bots.append(bot_id)
                    print(f"✅ Spawned bot {bot_name} with IP {bot_ip}")
                    
                else:
                    error_msg = result.stderr.strip() or "Unknown Docker error"
                    failed_spawns.append(f"Bot {i+1}: {error_msg}")
                    print(f"❌ Failed to spawn bot {i+1}: {error_msg}")
                
            except subprocess.TimeoutExpired:
                failed_spawns.append(f"Bot {i+1}: Docker timeout")
            except Exception as e:
                failed_spawns.append(f"Bot {i+1}: {str(e)}")
        
        # Wait for bots to start and register
        time.sleep(3)
        
        # Mark successfully started bots as active
        for bot_id in spawned_bots:
            if bot_id in fleet_state['bots']:
                fleet_state['bots'][bot_id]['status'] = 'active'
        
        return jsonify({
            'success': True,
            'spawned_count': len(spawned_bots),
            'spawned_bots': spawned_bots,
            'failed_count': len(failed_spawns),
            'failed_spawns': failed_spawns[:5],  # Limit error list
            'fleet_size': len(fleet_state['bots']),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Fleet spawn failed: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/fleet/attack', methods=['POST'])
def coordinate_attack():
    """Coordinate swarm attack across all active bots"""
    try:
        data = request.get_json() or {}
        attack_type = data.get('attack_type', 'http_flood')
        duration = int(data.get('duration', 30))
        rate_per_bot = float(data.get('rate_per_bot', 2.0))
        target = data.get('target', 'load-balancer')
        
        active_bots = [bot_id for bot_id, bot in fleet_state['bots'].items() 
                      if bot.get('status') == 'active']
        
        if not active_bots:
            return jsonify({'error': 'No active bots available'}), 400
        
        attack_id = f"attack_{int(time.time())}"
        
        # Configure attack parameters
        attack_config = {
            'type': attack_type,
            'duration': duration,
            'rate_per_bot': rate_per_bot,
            'target': target,
            'total_bots': len(active_bots),
            'expected_total_rps': len(active_bots) * rate_per_bot
        }
        
        # Store attack info
        fleet_state['attacks'][attack_id] = {
            'config': attack_config,
            'start_time': datetime.now().isoformat(),
            'participating_bots': active_bots.copy(),
            'status': 'starting'
        }
        
        # Reset attack stats
        attack_stats.update({
            'requests_sent': 0,
            'requests_successful': 0,
            'requests_blocked': 0,
            'bytes_sent': 0,
            'attack_duration': duration,
            'start_time': time.time()
        })
        
        # Send attack commands to all bots (via environment or API if available)
        successful_commands = 0
        for bot_id in active_bots:
            bot = fleet_state['bots'][bot_id]
            try:
                # Signal bot to start attack via docker exec
                cmd_result = subprocess.run([
                    'docker', 'exec', bot['container_name'],
                    'python', '-c', 
                    f"import requests; "
                    f"print('ATTACK_START:{attack_type}:{duration}:{rate_per_bot}:{target}')"
                ], capture_output=True, text=True, timeout=10)
                
                if cmd_result.returncode == 0:
                    successful_commands += 1
                    bot['status'] = 'attacking'
                    
            except Exception as e:
                print(f"Failed to command bot {bot_id}: {e}")
        
        fleet_state['attacks'][attack_id]['status'] = 'active'
        fleet_state['attacks'][attack_id]['commanded_bots'] = successful_commands
        
        print(f"🚀 Coordinated attack {attack_id}: {successful_commands}/{len(active_bots)} bots")
        
        return jsonify({
            'success': True,
            'attack_id': attack_id,
            'participating_bots': len(active_bots),
            'commanded_bots': successful_commands,
            'expected_rps': attack_config['expected_total_rps'],
            'config': attack_config,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Attack coordination failed: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/fleet/destroy', methods=['POST'])
def destroy_fleet():
    """Destroy all bot containers"""
    try:
        data = request.get_json() or {}
        target_bots = data.get('bots', 'all')  # 'all' or list of bot_ids
        
        if target_bots == 'all':
            target_bots = list(fleet_state['bots'].keys())
        
        destroyed_count = 0
        failed_destroys = []
        
        for bot_id in target_bots:
            if bot_id not in fleet_state['bots']:
                continue
                
            bot = fleet_state['bots'][bot_id]
            try:
                # Stop and remove container
                subprocess.run(['docker', 'stop', bot['container_name']], 
                             capture_output=True, timeout=10)
                subprocess.run(['docker', 'rm', bot['container_name']], 
                             capture_output=True, timeout=10)
                
                # Remove from fleet
                del fleet_state['bots'][bot_id]
                destroyed_count += 1
                fleet_state['total_destroyed'] += 1
                
                print(f"💥 Destroyed bot {bot['container_name']}")
                
            except Exception as e:
                failed_destroys.append(f"{bot_id}: {str(e)}")
                print(f"❌ Failed to destroy bot {bot_id}: {e}")
        
        return jsonify({
            'success': True,
            'destroyed_count': destroyed_count,
            'failed_count': len(failed_destroys),
            'failed_destroys': failed_destroys,
            'remaining_bots': len(fleet_state['bots']),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Fleet destruction failed: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/bot/heartbeat', methods=['POST'])
def bot_heartbeat():
    """Receive heartbeat from bot agents"""
    try:
        data = request.get_json() or {}
        bot_ip = data.get('bot_ip')
        container_name = data.get('container_name', '')
        stats = data.get('stats', {})
        
        # Find bot by IP or container name
        bot_id = None
        for bid, bot in fleet_state['bots'].items():
            if bot.get('ip') == bot_ip or bot.get('container_name') == container_name:
                bot_id = bid
                break
        
        if bot_id:
            # Update bot stats
            fleet_state['bots'][bot_id].update({
                'last_heartbeat': time.time(),
                'status': 'active',
                'requests_sent': stats.get('requests_sent', 0),
                'requests_successful': stats.get('requests_successful', 0),
                'requests_blocked': stats.get('requests_blocked', 0)
            })
            
            # Aggregate stats
            attack_stats['requests_sent'] += stats.get('new_requests', 0)
            attack_stats['requests_successful'] += stats.get('new_successful', 0)
            attack_stats['requests_blocked'] += stats.get('new_blocked', 0)
        
        return jsonify({'success': True, 'bot_id': bot_id})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def cleanup_stale_bots():
    """Remove bots that haven't sent heartbeat in 60s"""
    current_time = time.time()
    stale_bots = []
    
    for bot_id, bot in list(fleet_state['bots'].items()):
        if current_time - bot.get('last_heartbeat', 0) > 60:
            stale_bots.append(bot_id)
    
    for bot_id in stale_bots:
        try:
            bot = fleet_state['bots'][bot_id]
            subprocess.run(['docker', 'rm', '-f', bot['container_name']], 
                         capture_output=True, timeout=10)
            del fleet_state['bots'][bot_id]
            print(f"🧹 Cleaned up stale bot {bot_id}")
        except Exception as e:
            print(f"Failed to cleanup bot {bot_id}: {e}")

def calculate_fleet_health():
    """Calculate overall fleet health metrics"""
    if not fleet_state['bots']:
        return {'status': 'empty', 'health_score': 0}
    
    active_count = len([b for b in fleet_state['bots'].values() if b.get('status') == 'active'])
    total_count = len(fleet_state['bots'])
    health_score = (active_count / total_count) * 100 if total_count > 0 else 0
    
    status = 'healthy' if health_score > 80 else ('degraded' if health_score > 50 else 'critical')
    
    return {
        'status': status,
        'health_score': round(health_score, 1),
        'active_bots': active_count,
        'total_bots': total_count
    }

@app.route('/api/system/info')
def system_info():
    """Get orchestrator system information"""
    return jsonify({
        'orchestrator': 'Aurora Shield Attack Orchestrator',
        'version': '1.0.0',
        'capabilities': [
            'Multi-container bot fleet management',
            'Coordinated swarm attacks',
            'Real-time bot monitoring',
            'Distributed IP simulation',
            'Attack statistics aggregation'
        ],
        'limits': {
            'max_bots': 50,
            'max_attack_duration': 300,
            'supported_targets': ['load-balancer', 'aurora-shield', 'direct-cdn']
        },
        'fleet_stats': {
            'total_spawned': fleet_state['total_spawned'],
            'total_destroyed': fleet_state['total_destroyed'],
            'current_active': len([b for b in fleet_state['bots'].values() if b.get('status') == 'active'])
        },
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🎯 Aurora Shield Attack Orchestrator starting on port 5000")
    print("🤖 Ready to manage bot fleet for realistic DDoS simulation")
    app.run(host='0.0.0.0', port=5000, debug=False)