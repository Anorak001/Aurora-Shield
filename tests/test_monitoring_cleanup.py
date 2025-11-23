#!/usr/bin/env python3

"""
Test to verify Kibana and Grafana buttons have been removed
"""

def test_monitoring_buttons_removed():
    """Test that Kibana and Grafana buttons have been removed from monitoring tab"""
    
    print("🔍 Monitoring Tab Button Removal Test")
    print("=" * 50)
    
    with open('aurora_shield/dashboard/templates/aurora_dashboard.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Test 1: Check removed buttons
    print("\n🗑️ Test 1: Button Removal")
    print("-" * 30)
    
    removed_buttons = [
        ('Open Grafana', 'Grafana button'),
        ('Open Kibana', 'Kibana button'),
        ('localhost:3000', 'Grafana URL'),
        ('localhost:5601', 'Kibana URL')
    ]
    
    for text, description in removed_buttons:
        if text in content:
            print(f"❌ {description} still present")
        else:
            print(f"✅ {description} removed")
    
    # Test 2: Check preserved functionality
    print("\n🔄 Test 2: Preserved Elements")
    print("-" * 30)
    
    preserved_elements = [
        ('Export Logs', 'Export logs button'),
        ('exportLogs()', 'Export logs function'),
        ('💾', 'Export logs icon')
    ]
    
    for element, description in preserved_elements:
        if element in content:
            print(f"✅ {description} preserved")
        else:
            print(f"❌ {description} missing (should be preserved)")
    
    # Test 3: Check monitoring tab structure
    print("\n📊 Test 3: Monitoring Tab Structure")
    print("-" * 30)
    
    # Count buttons in the monitoring section
    import re
    
    # Find the monitoring tab content - more specific pattern
    monitoring_section = re.search(r'<div id="monitoring-tab".*?</div>\s*</div>\s*<!--.*?Configuration Tab', content, re.DOTALL)
    if monitoring_section:
        monitoring_content = monitoring_section.group(0)
        button_count = len(re.findall(r'<button[^>]*>', monitoring_content))
        print(f"✅ Found monitoring tab with {button_count} button(s)")
        
        # Should only have the Export Logs button now
        if button_count == 1:
            print("✅ Correct number of buttons (1 - Export Logs only)")
        else:
            print(f"⚠️  Expected 1 button, found {button_count}")
            
        # Verify it's the Export Logs button
        if 'Export Logs' in monitoring_content:
            print("✅ Export Logs button found in monitoring tab")
        else:
            print("❌ Export Logs button not found in monitoring tab")
    else:
        print("❌ Could not find monitoring tab")
    
    print("\n🎉 Monitoring Button Removal Test Complete!")
    print("=" * 50)

if __name__ == "__main__":
    test_monitoring_buttons_removed()