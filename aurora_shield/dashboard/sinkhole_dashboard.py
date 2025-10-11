"""
Sinkhole Management Dashboard
Web interface for managing sinkhole/blackhole operations
"""

from flask import Flask, request, jsonify, render_template
from aurora_shield.mitigation.sinkhole import sinkhole_manager
import time
import json

sinkhole_app = Flask(__name__, template_folder='templates')

@sinkhole_app.route('/')
def dashboard():
    """Main sinkhole management dashboard"""
    return render_template('sinkhole_dashboard.html')

@sinkhole_app.route('/api/sinkhole/status')
def get_status():
    """Get current sinkhole/blackhole status"""
    try:
        status = sinkhole_manager.get_detailed_status()
        return jsonify({
            'success': True,
            'data': status,
            'timestamp': time.time()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': time.time()
        }), 500

@sinkhole_app.route('/api/sinkhole/add', methods=['POST'])
def add_to_sinkhole():
    """Add IP/subnet/fingerprint to sinkhole"""
    try:
        data = request.get_json()
        target = data.get('target', '').strip()
        target_type = data.get('type', 'ip')
        reason = data.get('reason', 'manual_addition')
        
        if not target:
            return jsonify({
                'success': False,
                'error': 'Target is required'
            }), 400
        
        if target_type not in ['ip', 'subnet', 'fingerprint']:
            return jsonify({
                'success': False,
                'error': 'Invalid target type'
            }), 400
        
        sinkhole_manager.add_to_sinkhole(target, target_type, reason)
        
        return jsonify({
            'success': True,
            'message': f'Added {target} to sinkhole',
            'target': target,
            'type': target_type,
            'reason': reason,
            'timestamp': time.time()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': time.time()
        }), 500

@sinkhole_app.route('/api/blackhole/add', methods=['POST'])
def add_to_blackhole():
    """Add IP/subnet to blackhole"""
    try:
        data = request.get_json()
        target = data.get('target', '').strip()
        target_type = data.get('type', 'ip')
        reason = data.get('reason', 'manual_addition')
        
        if not target:
            return jsonify({
                'success': False,
                'error': 'Target is required'
            }), 400
        
        if target_type not in ['ip', 'subnet']:
            return jsonify({
                'success': False,
                'error': 'Invalid target type for blackhole'
            }), 400
        
        sinkhole_manager.add_to_blackhole(target, target_type, reason)
        
        return jsonify({
            'success': True,
            'message': f'Added {target} to blackhole',
            'target': target,
            'type': target_type,
            'reason': reason,
            'timestamp': time.time()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': time.time()
        }), 500

@sinkhole_app.route('/api/quarantine/add', methods=['POST'])
def add_to_quarantine():
    """Add IP to quarantine"""
    try:
        data = request.get_json()
        ip = data.get('ip', '').strip()
        duration = int(data.get('duration', 3600))  # Default 1 hour
        reason = data.get('reason', 'manual_quarantine')
        
        if not ip:
            return jsonify({
                'success': False,
                'error': 'IP is required'
            }), 400
        
        if duration < 60 or duration > 86400:  # 1 minute to 24 hours
            return jsonify({
                'success': False,
                'error': 'Duration must be between 60 and 86400 seconds'
            }), 400
        
        sinkhole_manager.quarantine_ip(ip, duration, reason)
        
        return jsonify({
            'success': True,
            'message': f'Quarantined {ip} for {duration} seconds',
            'ip': ip,
            'duration': duration,
            'reason': reason,
            'timestamp': time.time()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': time.time()
        }), 500

@sinkhole_app.route('/api/threat-intel/export')
def export_threat_intelligence():
    """Export threat intelligence data"""
    try:
        intel_data = sinkhole_manager.export_threat_intelligence()
        return jsonify({
            'success': True,
            'data': intel_data,
            'timestamp': time.time()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': time.time()
        }), 500

@sinkhole_app.route('/api/config/update', methods=['POST'])
def update_config():
    """Update sinkhole configuration"""
    try:
        data = request.get_json()
        
        # Validate configuration
        valid_keys = [
            'auto_sinkhole_threshold',
            'auto_blackhole_threshold',
            'quarantine_duration',
            'honeypot_delay_min',
            'honeypot_delay_max',
            'data_collection_enabled',
            'learning_mode'
        ]
        
        config_updates = {}
        for key, value in data.items():
            if key in valid_keys:
                config_updates[key] = value
        
        if not config_updates:
            return jsonify({
                'success': False,
                'error': 'No valid configuration keys provided'
            }), 400
        
        # Update configuration
        sinkhole_manager.config.update(config_updates)
        
        return jsonify({
            'success': True,
            'message': 'Configuration updated',
            'updated_config': config_updates,
            'timestamp': time.time()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': time.time()
        }), 500

@sinkhole_app.route('/api/stats/violations')
def get_violation_stats():
    """Get violation statistics for analysis"""
    try:
        # Get top violating IPs
        violations_summary = {}
        current_time = time.time()
        
        for ip, violations in sinkhole_manager.behavior_patterns.items():
            recent_violations = [
                v for v in violations 
                if current_time - v['timestamp'] < 3600  # Last hour
            ]
            
            if recent_violations:
                violations_summary[ip] = {
                    'total_violations': len(recent_violations),
                    'total_severity': sum(v['severity'] for v in recent_violations),
                    'violation_types': list(set(v['type'] for v in recent_violations)),
                    'last_violation': max(v['timestamp'] for v in recent_violations),
                    'subnet': sinkhole_manager._get_subnet(ip)
                }
        
        # Sort by severity
        top_violators = sorted(
            violations_summary.items(),
            key=lambda x: x[1]['total_severity'],
            reverse=True
        )[:20]
        
        return jsonify({
            'success': True,
            'data': {
                'top_violators': dict(top_violators),
                'summary': {
                    'total_ips_with_violations': len(violations_summary),
                    'total_violations': sum(v['total_violations'] for v in violations_summary.values()),
                    'avg_severity': sum(v['total_severity'] for v in violations_summary.values()) / max(len(violations_summary), 1)
                }
            },
            'timestamp': time.time()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': time.time()
        }), 500

@sinkhole_app.route('/api/honeypot/responses')
def get_honeypot_responses():
    """Get honeypot response statistics"""
    try:
        stats = sinkhole_manager.get_statistics()
        
        return jsonify({
            'success': True,
            'data': {
                'total_interactions': stats['stats']['honeypot_interactions'],
                'sinkholed_requests': stats['stats']['sinkholed_requests'],
                'data_collected': stats['stats']['data_collected'],
                'response_types': {
                    'web': 'Fake web pages with JavaScript honeypots',
                    'api': 'Fake API responses with tracking',
                    'file': 'Fake file downloads',
                    'redirect': 'Redirect loops to waste resources'
                }
            },
            'timestamp': time.time()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': time.time()
        }), 500

if __name__ == '__main__':
    print("🕳️ Starting Sinkhole Management Dashboard on port 5100")
    sinkhole_app.run(host='0.0.0.0', port=5100, debug=False)