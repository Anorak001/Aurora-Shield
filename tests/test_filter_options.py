#!/usr/bin/env python3

"""
Quick test to verify the dashboard filter options are working correctly
"""

import re

def test_dashboard_filter_options():
    """Test that the new filter options are properly added to the dashboard"""
    
    # Read the dashboard HTML template
    with open('aurora_shield/dashboard/templates/aurora_dashboard.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if the new filter options are present
    filter_options = [
        'blocked',
        'sinkholed', 
        'blackholed',
        'quarantined',
        'rate-limited',
        'challenged',
        'monitored'
    ]
    
    print("🔍 Testing Filter Options in Dashboard...")
    print("=" * 50)
    
    # Find the action filter dropdown
    filter_pattern = r'<select[^>]*id="action-filter"[^>]*>(.*?)</select>'
    match = re.search(filter_pattern, content, re.DOTALL)
    
    if match:
        filter_dropdown = match.group(1)
        print("✅ Found action filter dropdown")
        
        # Check each option
        missing_options = []
        for option in filter_options:
            if f'value="{option}"' in filter_dropdown:
                print(f"✅ Found {option} option")
            else:
                missing_options.append(option)
                print(f"❌ Missing {option} option")
        
        if not missing_options:
            print("\n🎉 All filter options are present!")
        else:
            print(f"\n⚠️  Missing options: {missing_options}")
    else:
        print("❌ Could not find action filter dropdown")
    
    # Check CSS styles for action types
    print("\n🎨 Testing CSS Styles...")
    print("=" * 50)
    
    css_classes = [
        'action-blocked',
        'action-sinkholed',
        'action-blackholed', 
        'action-quarantined',
        'action-rate-limited',
        'action-challenged',
        'action-monitored'
    ]
    
    missing_styles = []
    for css_class in css_classes:
        if f'.{css_class} {{' in content:
            print(f"✅ Found {css_class} style")
        else:
            missing_styles.append(css_class)
            print(f"❌ Missing {css_class} style")
    
    if not missing_styles:
        print("\n🎉 All CSS styles are present!")
    else:
        print(f"\n⚠️  Missing styles: {missing_styles}")
    
    # Test filter JavaScript function
    print("\n🔧 Testing JavaScript Function...")
    print("=" * 50)
    
    if 'function onActionFilterChange(select)' in content:
        print("✅ Found onActionFilterChange function")
    else:
        print("❌ Missing onActionFilterChange function")
    
    if 'currentAttackFilters.action = select.value' in content:
        print("✅ Found filter update logic")
    else:
        print("❌ Missing filter update logic")

if __name__ == "__main__":
    test_dashboard_filter_options()