#!/usr/bin/env python3
"""
Complete Aurora Shield Sinkhole/Blackhole System Demonstration
Shows the comprehensive malicious actor isolation system in action.
"""

import sys
import time
import threading
from aurora_shield.shield_manager import AuroraShieldManager
from aurora_shield.dashboard.web_dashboard import WebDashboard
from aurora_shield.mitigation.sinkhole import sinkhole_manager
from aurora_shield.mitigation.advanced_limits import advanced_limiter

def demonstrate_complete_system():
    """Demonstrate the complete integrated Aurora Shield system with sinkhole capabilities."""
    
    print("🛡️ AURORA SHIELD COMPLETE SYSTEM DEMONSTRATION")
    print("=" * 70)
    print("Showcasing comprehensive malicious actor isolation with sinkhole/blackhole")
    print("=" * 70)
    
    # Initialize the complete system
    print("\n1. 🚀 SYSTEM INITIALIZATION")
    print("-" * 30)
    
    print("   Initializing Aurora Shield Manager...")
    shield_manager = AuroraShieldManager()
    
    print("   Initializing Web Dashboard...")
    dashboard = WebDashboard(shield_manager)
    
    print("   ✅ Complete system initialized!")
    print(f"   📊 Dashboard ready on: http://localhost:8080")
    print(f"   🔐 Demo credentials: admin/admin123")
    
    # Demonstrate sinkhole functionality
    print("\n2. 🕳️ SINKHOLE/BLACKHOLE SYSTEM DEMO")
    print("-" * 40)
    
    # Test IPs for demonstration
    test_ips = [
        "192.168.1.100",  # Will be sinkholed
        "10.0.0.50",      # Will be blackholed  
        "203.0.113.25",   # Will auto-escalate
        "198.51.100.75"   # Will be quarantined then escalated
    ]
    
    print("   🎯 Adding manual threats...")
    
    # Manual sinkhole
    sinkhole_manager.add_to_sinkhole(test_ips[0], "ip", "Detected bot activity")
    print(f"   🕳️ Sinkholed: {test_ips[0]} (bot activity)")
    
    # Manual blackhole
    sinkhole_manager.add_to_blackhole(test_ips[1], "ip", "Confirmed malicious actor")
    print(f"   ⚫ Blackholed: {test_ips[1]} (confirmed malicious)")
    
    # Demonstrate auto-escalation
    print("   🔄 Testing automatic escalation...")
    
    # Generate violations for auto-escalation
    for i in range(12):  # Trigger sinkhole threshold (10)
        sinkhole_manager.process_violation(test_ips[2], 'rate_limit_exceeded', 3)
    
    print(f"   📈 Generated 12 violations for {test_ips[2]} (auto-escalation)")
    
    # Generate more violations for blackhole escalation
    for i in range(55):  # Trigger blackhole threshold (50)
        sinkhole_manager.process_violation(test_ips[3], 'malicious_payload', 5)
    
    print(f"   🚨 Generated 55 violations for {test_ips[3]} (blackhole escalation)")
    
    # Show current status
    time.sleep(1)  # Let escalation process
    status = sinkhole_manager.get_detailed_status()
    stats = sinkhole_manager.get_statistics()
    
    print("\n3. 📊 CURRENT THREAT LANDSCAPE")
    print("-" * 35)
    print(f"   🕳️ Active Sinkholes: {stats['counts']['sinkholed_ips']}")
    print(f"   ⚫ Active Blackholes: {stats['counts']['blackholed_ips']}")
    print(f"   ⏳ Quarantined IPs: {stats['counts']['quarantined_ips']}")
    print(f"   📈 Total Requests Processed: {stats['stats']['sinkholed_requests'] + stats['stats']['blackholed_requests']}")
    
    # Demonstrate request processing
    print("\n4. 🔍 REQUEST PROCESSING DEMONSTRATION")
    print("-" * 45)
    
    test_requests = [
        {'ip': test_ips[0], 'path': '/api/data', 'method': 'GET'},    # Should be sinkholed
        {'ip': test_ips[1], 'path': '/admin', 'method': 'POST'},      # Should be blackholed  
        {'ip': '192.168.1.200', 'path': '/login', 'method': 'POST'},  # Should be allowed
        {'ip': test_ips[2], 'path': '/exploit', 'method': 'GET'}      # Should be sinkholed
    ]
    
    for i, req in enumerate(test_requests, 1):
        req['user_agent'] = 'TestBot/1.0'
        req['timestamp'] = time.time()
        
        result = shield_manager.process_request(req)
        
        # Handle both possible result structures
        action = result.get('action', result.get('status', 'unknown'))
        
        action_emoji = {
            'allow': '✅',
            'allowed': '✅', 
            'sinkhole': '🕳️',
            'blackhole': '⚫',
            'drop': '🚫',
            'blocked': '🚫'
        }
        
        emoji = action_emoji.get(action, '❓')
        print(f"   Request {i}: {req['ip']} → {emoji} {action.upper()}")
        
        if action in ['sinkhole', 'blackhole']:
            print(f"      └─ Reason: {result.get('reason', 'Threat isolation')}")
    
    # Show advanced statistics
    print("\n5. 🎯 ADVANCED SYSTEM STATISTICS")
    print("-" * 40)
    
    advanced_stats = shield_manager.get_advanced_stats()
    overview = advanced_stats['overview']
    sinkhole_protection = advanced_stats['sinkhole_protection']
    
    print(f"   System Uptime: {overview['uptime_seconds']}s")
    print(f"   Total Requests: {overview['total_requests']}")
    print(f"   Block Rate: {overview['block_rate']:.1f}%")
    print(f"   System Health: {overview['system_health']}/100")
    
    print(f"\n   Sinkhole Statistics:")
    sinkhole_stats = sinkhole_protection['statistics']
    print(f"   • Sinkholed IPs: {sinkhole_stats['counts']['sinkholed_ips']}")
    print(f"   • Blackholed IPs: {sinkhole_stats['counts']['blackholed_ips']}")
    print(f"   • Total Malicious IPs: {sinkhole_stats['stats']['total_malicious_ips']}")
    
    # Show recent actions
    print("\n6. 📝 RECENT SECURITY ACTIONS")
    print("-" * 35)
    
    recent_actions = status.get('recent_actions', [])[-5:]  # Last 5 actions
    for action in recent_actions:
        timestamp = time.strftime('%H:%M:%S', time.localtime(action['timestamp']))
        action_emoji = '🕳️' if action['action'] == 'sinkhole' else '⚫' if action['action'] == 'blackhole' else '⏳'
        print(f"   [{timestamp}] {action_emoji} {action['action'].title()}: {action['target']}")
        if action.get('reason'):
            print(f"      └─ {action['reason']}")
    
    # Start dashboard for live monitoring
    print("\n7. 🌐 STARTING LIVE DASHBOARD")
    print("-" * 35)
    
    def run_dashboard():
        try:
            dashboard.run(host='localhost', port=8080, debug=False)
        except Exception as e:
            print(f"Dashboard error: {e}")
    
    dashboard_thread = threading.Thread(target=run_dashboard, daemon=True)
    dashboard_thread.start()
    
    print("   🚀 Dashboard starting on http://localhost:8080")
    print("   🕳️ Sinkhole tab available for threat management")
    print("   🔐 Login with: admin/admin123")
    
    # Wait a moment for dashboard to start
    time.sleep(3)
    
    print("\n" + "=" * 70)
    print("✅ DEMONSTRATION COMPLETE!")
    print("=" * 70)
    print("COMPREHENSIVE SINKHOLE/BLACKHOLE SYSTEM FEATURES:")
    print("• ✅ Multi-tier threat isolation (quarantine → sinkhole → blackhole)")
    print("• ✅ Automatic escalation based on violation patterns")
    print("• ✅ Honeypot responses to waste attacker resources")  
    print("• ✅ Real-time threat monitoring and management")
    print("• ✅ Manual threat addition via web dashboard")
    print("• ✅ Advanced violation tracking and behavior analysis")
    print("• ✅ Integration with main Aurora Shield protection layers")
    print("• ✅ Professional web interface for threat management")
    print("")
    print("🎯 The system now provides comprehensive malicious actor isolation")
    print("   beyond basic blocking, with intelligent threat redirection and")
    print("   automatic escalation capabilities.")
    print("")
    print("🌐 Visit http://localhost:8080 and check the 🕳️ Sinkhole tab")
    print("   to see the threat management interface in action!")
    print("=" * 70)
    
    # Keep the dashboard running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 System shutdown requested")
        return True

if __name__ == "__main__":
    try:
        demonstrate_complete_system()
    except KeyboardInterrupt:
        print("\n⚠️ Demonstration interrupted")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)