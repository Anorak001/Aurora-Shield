#!/usr/bin/env python3

"""
Test to verify removal of sinkhole management UI elements
"""

import re

def test_sinkhole_sections_removed():
    """Test that all requested sinkhole sections have been removed"""
    
    print("🧹 Sinkhole Cleanup Test")
    print("=" * 50)
    
    with open('aurora_shield/dashboard/templates/aurora_dashboard.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Test 1: Check removed stats section
    print("\n📊 Test 1: Stats Section Removal")
    print("-" * 30)
    
    removed_stats = [
        ('sinkholed-ips', 'Sinkholed IPs stat'),
        ('blackholed-ips', 'Blackholed IPs stat'),
        ('blocked-requests', 'Blocked Requests stat'),
        ('sinkhole-efficiency', 'Efficiency stat'),
        ('sinkhole-status-grid', 'Status grid container')
    ]
    
    for element_id, description in removed_stats:
        if element_id in content:
            print(f"❌ {description} still present")
        else:
            print(f"✅ {description} removed")
    
    # Test 2: Check removed list sections
    print("\n📋 Test 2: List Sections Removal")
    print("-" * 30)
    
    removed_lists = [
        ('Active Sinkhole Entries', 'Sinkhole entries section'),
        ('Active Blackhole Entries', 'Blackhole entries section'),
        ('No sinkhole entries yet', 'Sinkhole placeholder'),
        ('No blackhole entries yet', 'Blackhole placeholder'),
        ('sinkhole-list', 'Sinkhole list container'),
        ('blackhole-list', 'Blackhole list container')
    ]
    
    for text, description in removed_lists:
        if text in content and 'innerHTML' not in content[content.find(text):content.find(text)+100]:
            print(f"❌ {description} still present")
        else:
            print(f"✅ {description} removed")
    
    # Test 3: Check removed JavaScript functions
    print("\n🔧 Test 3: JavaScript Functions Removal")
    print("-" * 30)
    
    removed_js_functions = [
        ('updateSinkholeStats', 'Update stats function'),
        ('updateSinkholeList', 'Update sinkhole list function'),
        ('updateBlackholeList', 'Update blackhole list function')
    ]
    
    for func_name, description in removed_js_functions:
        if f'function {func_name}(' in content:
            print(f"❌ {description} still present")
        else:
            print(f"✅ {description} removed")
    
    # Test 4: Check removed CSS classes
    print("\n🎨 Test 4: CSS Classes Removal")
    print("-" * 30)
    
    removed_css = [
        ('sinkhole-status-grid', 'Status grid CSS'),
        ('sinkhole-stat-card', 'Stat card CSS'),
        ('sinkhole-list-section', 'List section CSS'),
        ('blackhole-list-section', 'Blackhole section CSS'),
        ('sinkhole-entry', 'Entry CSS'),
        ('blackhole-entry', 'Blackhole entry CSS')
    ]
    
    for css_class, description in removed_css:
        if f'.{css_class}' in content:
            print(f"❌ {description} still present")
        else:
            print(f"✅ {description} removed")
    
    # Test 5: Check that essential parts remain
    print("\n🔄 Test 5: Essential Functions Preserved")
    print("-" * 30)
    
    preserved_elements = [
        ('🕳️ Sinkhole/Blackhole Management', 'Panel title'),
        ('Add to Sinkhole', 'Add form section'),
        ('target-input', 'Target input field'),
        ('addToSinkhole', 'Add sinkhole function'),
        ('addToBlackhole', 'Add blackhole function'),
        ('removeFromSinkhole', 'Remove sinkhole function')
    ]
    
    for element, description in preserved_elements:
        if element in content:
            print(f"✅ {description} preserved")
        else:
            print(f"❌ {description} missing (should be preserved)")
    
    # Test 6: Check loadSinkholeData simplified
    print("\n⚡ Test 6: LoadSinkholeData Simplified")
    print("-" * 30)
    
    if 'loadSinkholeData()' in content:
        if 'fetch(\'/api/sinkhole/status\')' in content:
            print("❌ LoadSinkholeData still fetching data")
        else:
            print("✅ LoadSinkholeData simplified")
    else:
        print("❌ LoadSinkholeData function missing")
    
    print("\n🎉 Sinkhole Cleanup Test Complete!")
    print("=" * 50)

if __name__ == "__main__":
    test_sinkhole_sections_removed()