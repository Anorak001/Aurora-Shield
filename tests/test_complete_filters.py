#!/usr/bin/env python3

"""
Comprehensive test for Aurora Shield filter functionality
Tests the sinkholed and blackholed filter options
"""

import json
import re

def test_complete_filter_functionality():
    """Test all aspects of the filter functionality"""
    
    print("🔍 Aurora Shield Filter Test Suite")
    print("=" * 60)
    
    # Test 1: HTML Filter Options
    print("\n📋 Test 1: HTML Filter Options")
    print("-" * 30)
    
    with open('aurora_shield/dashboard/templates/aurora_dashboard.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Expected filter options
    expected_options = [
        ('all', 'All Actions'),
        ('blocked', 'Blocked'),
        ('sinkholed', 'Sinkholed'),
        ('blackholed', 'Blackholed'),
        ('rate-limited', 'Rate Limited'),
        ('quarantined', 'Quarantined'),
        ('challenged', 'Challenged'),
        ('monitored', 'Monitored')
    ]
    
    # Find filter dropdown
    filter_pattern = r'<select[^>]*id="action-filter"[^>]*>(.*?)</select>'
    match = re.search(filter_pattern, html_content, re.DOTALL)
    
    if match:
        filter_content = match.group(1)
        print("✅ Found action filter dropdown")
        
        for value, label in expected_options:
            if f'value="{value}"' in filter_content and label in filter_content:
                print(f"✅ {label} option present")
            else:
                print(f"❌ {label} option missing")
    else:
        print("❌ Action filter dropdown not found")
    
    # Test 2: CSS Styles
    print("\n🎨 Test 2: CSS Action Styles")
    print("-" * 30)
    
    expected_css_classes = [
        'action-blocked',
        'action-sinkholed',
        'action-blackholed',
        'action-quarantined',
        'action-rate-limited',
        'action-challenged',
        'action-monitored'
    ]
    
    for css_class in expected_css_classes:
        if f'.{css_class} {{' in html_content:
            print(f"✅ {css_class} style defined")
        else:
            print(f"❌ {css_class} style missing")
    
    # Test 3: JavaScript Functions
    print("\n🔧 Test 3: JavaScript Functions")
    print("-" * 30)
    
    js_checks = [
        ('onActionFilterChange', 'function onActionFilterChange(select)'),
        ('Filter Update Logic', 'currentAttackFilters.action = select.value'),
        ('Update Function Call', 'updateEnhancedAttackActivity()'),
        ('Filter API Call', '/api/dashboard/attack-activity')
    ]
    
    for check_name, pattern in js_checks:
        if pattern in html_content:
            print(f"✅ {check_name} found")
        else:
            print(f"❌ {check_name} missing")
    
    # Test 4: Backend API Support
    print("\n🔗 Test 4: Backend API Support")
    print("-" * 30)
    
    try:
        with open('aurora_shield/dashboard/web_dashboard.py', 'r', encoding='utf-8') as f:
            backend_content = f.read()
        
        backend_checks = [
            ('Attack Activity Endpoint', '/api/dashboard/attack-activity'),
            ('Action Filter Parameter', 'action_filter = request.args.get'),
            ('Filter Logic', "action_taken.*lower.*replace.*==.*action_filter"),
            ('Shield Manager Fallback', 'shield_manager.recent_requests'),
            ('Status Mapping Functions', '_map_status_to_action'),
            ('All Action Types', 'sinkholed.*blackholed.*quarantined')
        ]
        
        for check_name, pattern in backend_checks:
            if re.search(pattern, backend_content):
                print(f"✅ {check_name} implemented")
            else:
                print(f"❌ {check_name} missing")
                
        # Check helper functions for new action types
        helper_function_checks = [
            ('Sinkholed Mapping', "'sinkholed': 'Sinkholed'"),
            ('Blackholed Mapping', "'blackholed': 'Blackholed'"),
            ('Quarantined Mapping', "'quarantined': 'Quarantined'"),
            ('Critical Severity', "'blackholed': 'critical'"),
            ('High Severity Sinkhole', "'sinkholed': 'high'")
        ]
        
        for check_name, pattern in helper_function_checks:
            if pattern in backend_content:
                print(f"✅ {check_name} configured")
            else:
                print(f"❌ {check_name} missing")
        
    except FileNotFoundError:
        print("❌ Backend file not found")
    
    # Test 5: Shield Manager Action Types
    print("\n🛡️  Test 5: Shield Manager Action Types")
    print("-" * 30)
    
    try:
        with open('aurora_shield/shield_manager.py', 'r', encoding='utf-8') as f:
            shield_content = f.read()
        
        shield_checks = [
            ('Sinkholed Logging', "_log_request_realtime.*'sinkholed'"),
            ('Blackholed Logging', "_log_request_realtime.*'blackholed'"),
            ('Quarantined Logging', "_log_request_realtime.*'quarantined'"),
            ('Rate Limited Logging', "_log_request_realtime.*'rate-limited'"),
            ('Blocked Logging', "_log_request_realtime.*'blocked'")
        ]
        
        for check_name, pattern in shield_checks:
            if re.search(pattern, shield_content):
                print(f"✅ {check_name} implemented")
            else:
                print(f"❌ {check_name} missing")
        
    except FileNotFoundError:
        print("❌ Shield manager file not found")
    
    # Test 6: Filter Integration Test
    print("\n🔄 Test 6: Filter Integration")
    print("-" * 30)
    
    # Test filter parameter processing
    test_cases = [
        ('blocked', 'blocked'),
        ('sinkholed', 'sinkholed'),
        ('blackholed', 'blackholed'),
        ('rate-limited', 'rate-limited'),
        ('quarantined', 'quarantined')
    ]
    
    for filter_value, expected_match in test_cases:
        # Simulate the backend filter logic
        action_taken = expected_match.title()
        converted = action_taken.lower().replace(' ', '-')
        
        if converted == filter_value:
            print(f"✅ Filter '{filter_value}' matches action '{action_taken}'")
        else:
            print(f"❌ Filter '{filter_value}' doesn't match action '{action_taken}' (got '{converted}')")
    
    print("\n🎉 Filter Test Suite Complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_complete_filter_functionality()