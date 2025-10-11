#!/usr/bin/env python3
"""
Quick debug script to check sinkhole manager status structure.
"""

from aurora_shield.mitigation.sinkhole import sinkhole_manager
import json

# Test what the actual structure looks like
print("🔍 Debugging sinkhole manager status structure...")

# Add a test IP
sinkhole_manager.add_to_sinkhole("192.168.1.100", "ip", "Debug test")

# Get detailed status
status = sinkhole_manager.get_detailed_status()
print("Detailed Status Structure:")
print(json.dumps(status, indent=2, default=str))

print("\n" + "="*40)

# Get statistics  
stats = sinkhole_manager.get_statistics()
print("Statistics Structure:")
print(json.dumps(stats, indent=2, default=str))