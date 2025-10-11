#!/usr/bin/env python3
"""Quick status check for attacking IPs and sinkhole."""

import requests
import json

def quick_status_check():
    session = requests.Session()
    
    # Login
    login_data = {'username': 'admin', 'password': 'admin123'}
    login_response = session.post("http://localhost:8080/login", data=login_data)
    
    if login_response.status_code == 200:
        print("✅ Logged in successfully")
        
        # Check attacking IPs
        attacking_response = session.get("http://localhost:8080/api/dashboard/attacking-ips")
        if attacking_response.status_code == 200:
            attacking_data = attacking_response.json()
            print(f"\n📊 Attacking IPs found: {len(attacking_data)}")
            
            for ip_data in attacking_data:
                print(f"  🎯 IP: {ip_data.get('ip', 'Unknown')}")
                print(f"     Attacks: {ip_data.get('attack_count', 0)}")
                print(f"     Action: {ip_data.get('action_taken', 'None')}")
                print(f"     Last seen: {ip_data.get('last_seen', 'Unknown')}")
                print()
        else:
            print(f"❌ Failed to get attacking IPs: {attacking_response.status_code}")
            print(f"Response: {attacking_response.text}")
        
        # Check sinkhole status
        sinkhole_response = session.get("http://localhost:8080/api/dashboard/sinkhole-status")
        if sinkhole_response.status_code == 200:
            sinkhole_data = sinkhole_response.json()
            print(f"🕳️  Sinkhole Status:")
            print(f"   Total sinkholed: {sinkhole_data.get('total_sinkholed', 0)}")
            print(f"   Active sinkholes: {sinkhole_data.get('active_sinkholes', 0)}")
            
            if sinkhole_data.get('sinkholed_ips'):
                print(f"\n🔒 Sinkholed IPs:")
                for ip_info in sinkhole_data['sinkholed_ips']:
                    print(f"  - {ip_info.get('ip', 'Unknown')}: {ip_info.get('reason', 'No reason')}")
            else:
                print("   No IPs currently sinkholed")
        else:
            print(f"❌ Failed to get sinkhole status: {sinkhole_response.status_code}")
            print(f"Response: {sinkhole_response.text}")
    else:
        print(f"❌ Login failed: {login_response.status_code}")

if __name__ == "__main__":
    quick_status_check()