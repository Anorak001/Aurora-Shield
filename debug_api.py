#!/usr/bin/env python3
"""Debug the attacking IPs API response."""

import requests
import json

def debug_api():
    session = requests.Session()
    
    # Login
    login_data = {'username': 'admin', 'password': 'admin123'}
    login_response = session.post("http://localhost:8080/login", data=login_data)
    
    if login_response.status_code == 200:
        print("✅ Logged in successfully")
        
        # Check attacking IPs - debug response
        attacking_response = session.get("http://localhost:8080/api/dashboard/attacking-ips")
        print(f"\nAttacking IPs API Response:")
        print(f"Status Code: {attacking_response.status_code}")
        print(f"Content-Type: {attacking_response.headers.get('Content-Type')}")
        print(f"Raw Response: {attacking_response.text}")
        
        if attacking_response.status_code == 200:
            try:
                attacking_data = attacking_response.json()
                print(f"\nParsed JSON Type: {type(attacking_data)}")
                print(f"Data: {attacking_data}")
                
                if attacking_data:
                    print(f"\nFirst element type: {type(attacking_data[0])}")
                    print(f"First element: {attacking_data[0]}")
            except Exception as e:
                print(f"JSON parsing error: {e}")

if __name__ == "__main__":
    debug_api()