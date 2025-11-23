"""
Aurora Shield Attack Classification and Response Strategy
========================================================

This document outlines how Aurora Shield now properly classifies different types of attacks 
and determines the appropriate response strategy for each.

## Problem Solved
Previously, ALL malicious requests were being tagged as "sinkholed" because the sinkhole 
system was checking first and catching everything. Now we have proper attack classification 
and smart response strategies.

## New Attack Classification System

### 1. IP Reputation Violations
**Attack Types:**
- `sql_injection`: SQL injection attempts in URLs
- `xss_attempt`: Cross-site scripting attempts  
- `directory_traversal`: Path traversal attacks (../../../)
- `brute_force`: Brute force login attempts
- `automated_scanner`: Known security scanners (Nikto, Nessus)
- `command_line_tool`: curl, wget tools
- `zero_reputation`: IPs with reputation score = 0
- `low_reputation`: IPs with score < 30
- `generic_malicious`: Other malicious activity

**Response Strategies:**
- **BLACKHOLE** (Complete block): Critical threats (severity ≥40) or dangerous zero-rep attacks
- **SINKHOLE** (Intelligence): SQL injection, XSS, scanners, zero-rep IPs (severity ≥20)
- **BLOCK** (Standard): Volume attacks, brute force, low-severity threats

### 2. Rate Limiting Violations  
**Attack Types:**
- `automated_flooding`: Bot/crawler flooding
- `behavioral_anomaly`: Suspicious user behavior patterns
- `fingerprint_flooding`: Same fingerprint excessive requests
- `distributed_attack`: Subnet-level coordinated attack
- `ip_flooding`: Single IP excessive requests
- `volume_attack`: Global rate limit exceeded

**Response Logic:**
- **High Severity (≥25)**: Escalate to sinkhole/blackhole consideration
- **Medium Severity (15-24)**: Standard rate limiting with monitoring
- **Low Severity (<15)**: Basic rate limiting

### 3. Anomaly Detection Violations
**Attack Types:**
- `security_scanner`: Known security tools (severity: 35)
- `high_frequency_anomaly`: >100 requests (severity: 30)
- `suspicious_path_anomaly`: Unusual URL patterns (severity: 25)
- `unusual_method_anomaly`: Non-standard HTTP methods (severity: 20)
- `medium_frequency_anomaly`: 50-100 requests (severity: 15)
- `behavioral_anomaly`: General suspicious behavior (severity: 10)

**Response Logic:**
- **High Severity (≥30)**: Consider sinkhole/blackhole escalation
- **Medium Severity (20-29)**: Block with enhanced monitoring
- **Low Severity (<20)**: Standard block

## Escalation Thresholds

### Sinkhole Escalation (Intelligence Gathering)
- SQL injection attempts
- XSS attempts  
- Directory traversal
- Security scanners
- Zero reputation IPs
- High-frequency anomalies

### Blackhole Escalation (Complete Block)
- Critical severity attacks (≥40)
- Repeated dangerous zero-reputation attacks
- Extreme high-frequency attacks
- Known APT signatures

### Standard Blocking
- Volume attacks
- Brute force attempts
- Basic rate limiting violations
- Low-severity anomalies

## Real-time Dashboard Display

The dashboard now shows:
- **BLOCKED**: Standard IP reputation, rate limiting, anomaly blocks
- **RATE-LIMITED**: Advanced and basic rate limiting violations  
- **SINKHOLED**: Intelligence-gathering targets
- **BLACKHOLED**: Complete traffic blocks
- **QUARANTINED**: Temporary isolation
- **ALLOWED**: Legitimate traffic (including bypass system)

## Example Attack Flows

### SQL Injection Attack
1. Request contains SQL keywords in URL
2. Classified as `sql_injection` (severity: 30)
3. **RESPONSE**: Sinkhole for intelligence gathering
4. Dashboard shows: "🕳️ SINKHOLED: Intelligence gathering: sql_injection"

### Volume Flooding Attack  
1. IP exceeds rate limits dramatically
2. Classified as `ip_flooding` (severity: 8)
3. **RESPONSE**: Standard rate limiting block
4. Dashboard shows: "⚠️ RATE-LIMITED: Rate limited: ip_flooding"

### Security Scanner
1. Nikto user-agent detected with high frequency
2. Classified as `security_scanner` (severity: 35)  
3. **RESPONSE**: Sinkhole escalation
4. Dashboard shows: "🕳️ SINKHOLED: Intelligence gathering: security_scanner"

### Brute Force Attack
1. Multiple failed login attempts from same IP
2. Classified as `brute_force` (severity: 20)
3. **RESPONSE**: Standard block  
4. Dashboard shows: "🚫 BLOCKED: Volume attack blocked: brute_force"

This system ensures that:
- ✅ Different attack types get appropriate responses
- ✅ Intelligence-worthy attacks are sinkholed for analysis
- ✅ Volume attacks are blocked efficiently  
- ✅ Critical threats are blackholed immediately
- ✅ Dashboard shows accurate, specific status information
"""