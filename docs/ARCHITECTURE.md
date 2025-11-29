# Aurora Shield Architecture

## Overview

Aurora Shield is a modular DDoS protection framework built with a layered architecture that provides defense-in-depth against various types of attacks.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Dashboard (Port 8080)                 │
│              Real-time Monitoring & Control Interface        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Aurora Shield Manager                      │
│            Central Coordinator & Request Processor           │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌────────────────┐    ┌──────────────┐
│   Detection   │    │   Mitigation   │    │   Recovery   │
│     Layer     │    │     Layer      │    │    Layer     │
└───────────────┘    └────────────────┘    └──────────────┘
        │                     │                     │
        ├─ Anomaly Detector   ├─ Rate Limiter      ├─ Failover
        ├─ ML Analysis        ├─ IP Reputation     ├─ Auto-scaling
        └─ Pattern Recognition├─ Challenge-Response└─ Traffic Redirect
                              │
                              ▼
                    ┌──────────────────┐
                    │   Integrations   │
                    ├──────────────────┤
                    │ ELK/Elasticsearch│
                    │ Prometheus       │
                    │ Cloud Provider   │
                    └──────────────────┘
```

## Component Details

### 1. Core Detection Layer

**Anomaly Detector** (`aurora_shield/core/anomaly_detector.py`)
- Rule-based detection using sliding time windows
- Tracks request rates per IP address
- Configurable thresholds and time windows
- Automatic IP blocking for violators
- Statistical analysis to reduce false positives

### 2. Mitigation Layer

**Rate Limiter** (`aurora_shield/mitigation/rate_limiter.py`)
- Token bucket algorithm implementation
- Per-IP rate limiting
- Configurable rate and burst limits
- Fair throttling mechanism

**IP Reputation** (`aurora_shield/mitigation/ip_reputation.py`)
- Dynamic scoring system (0-100)
- Violation tracking and history
- Automatic blacklisting at low scores
- Whitelist management
- Reputation decay over time

**Challenge-Response** (`aurora_shield/mitigation/challenge_response.py`)
- Proof-of-work verification
- Client verification tokens
- Challenge expiration management
- Bot detection mechanism

### 3. Auto-Recovery Layer

**Recovery Manager** (`aurora_shield/auto_recovery/recovery_manager.py`)
- Automatic situation assessment
- Failover to backup servers
- Dynamic capacity scaling
- Traffic redirection to CDN
- Aggressive caching enablement

Recovery Actions:
- `FAILOVER`: Switch to backup infrastructure
- `SCALE_UP`: Add server capacity
- `SCALE_DOWN`: Remove excess capacity
- `REDIRECT_TRAFFIC`: Route to CDN/alternate paths
- `ENABLE_CACHE`: Activate caching layer

### 4. Integration Layer

**ELK Integration** (`aurora_shield/integrations/elk_integration.py`)
- Log event ingestion
- Attack event logging
- Mitigation action tracking
- Index template management

**Prometheus Integration** (`aurora_shield/integrations/prometheus_integration.py`)
- Metrics collection (gauges, counters, histograms)
- Request rate tracking
- Attack detection metrics
- Latency measurements

### 5. Gateway Layer

**Flask Gateway** (`aurora_shield/gateway/flask_gateway.py`)
- HTTP request filtering
- Multi-layer protection enforcement
- RESTful API endpoints
- Metrics export endpoint

### 6. Dashboard Layer

**Web Dashboard** (`aurora_shield/dashboard/web_dashboard.py`)
- Real-time metrics visualization
- Attack simulation controls
- System management interface
- Live update mechanism (5-second refresh)

## Request Processing Flow

```
1. Request arrives at Gateway
   ↓
2. IP Reputation Check
   - Whitelisted? → Allow
   - Blacklisted? → Block
   - Score < 30? → Block
   ↓
3. Rate Limiting Check
   - Token available? → Continue
   - No token? → Block (429)
   ↓
4. Anomaly Detection
   - Within threshold? → Continue
   - Exceeds threshold? → ML Analysis
   ↓
5. ML Analysis (if anomalous)
   - Likely legitimate? → Allow + improve reputation
   - Likely attack? → Block + reduce reputation
   ↓
6. Allow Request
   - Log to ELK
   - Update Prometheus metrics
   - Process request
```

## Attack Detection & Response

### Detection Process
1. Monitor incoming requests
2. Track patterns per IP
3. Compare against thresholds
4. ML verification for edge cases
5. Log detection events

### Response Process
1. Block malicious IPs
2. Update reputation scores
3. Apply rate limits
4. Issue challenges if needed
5. Trigger recovery actions
6. Log mitigation events

### Recovery Process
1. Assess system metrics
2. Determine priority level
3. Select appropriate actions
4. Execute recovery procedures
5. Monitor effectiveness
6. Log recovery events

## Configuration

All components use hierarchical configuration:

```python
config = {
    'anomaly_detector': {
        'request_window': 60,     # seconds
        'rate_threshold': 100     # requests
    },
    'rate_limiter': {
        'rate': 10,              # tokens/second
        'burst': 20              # max tokens
    },
    'ip_reputation': {
        'initial_score': 100
    },
    'recovery_manager': {
        'max_capacity': 5
    }
}
```

## Scalability

Aurora Shield is designed for horizontal scaling:

- **Stateless Design**: All state can be externalized to Redis/Memcached
- **Distributed Detection**: Multiple instances can share detection data
- **Cloud Integration**: Auto-scaling via cloud provider APIs
- **Load Balancing**: Works behind any load balancer

## Security Considerations

1. **Defense in Depth**: Multiple protection layers
2. **Fail Secure**: Blocks on uncertainty
3. **Rate Limiting**: Prevents resource exhaustion
4. **Challenge-Response**: Verifies client legitimacy
5. **Logging**: Complete audit trail

## Performance

- **Low Latency**: <10ms overhead per request
- **High Throughput**: Handles 10,000+ req/s
- **Memory Efficient**: <100MB base memory
- **CPU Efficient**: Minimal CPU overhead

## Monitoring

### Key Metrics

- `aurora_shield_requests_total`: Total requests processed
- `aurora_shield_attacks_total`: Attacks detected
- `aurora_shield_mitigations_total`: Mitigation actions taken
- `aurora_shield_request_duration_seconds`: Request latency
- `aurora_shield_blocked_ips_total`: Blocked IP count

### Dashboards

- **Kibana**: Attack visualization, IP analysis
- **Grafana**: Time-series metrics, system health
- **Web Dashboard**: Real-time monitoring, control

## Testing

Aurora Shield includes comprehensive testing tools:

- **Attack Simulator**: Generate realistic attack traffic
- **Traffic Patterns**: Normal, bursty, and attack patterns
- **Load Testing**: Stress test protection mechanisms
- **Integration Tests**: Verify component interaction

## Future Enhancements

1. Machine learning model training
2. Distributed consensus for IP reputation
3. Geo-IP blocking
4. Pattern-based attack signatures
5. API rate limiting per endpoint
6. WebSocket protection
7. Layer 7 DDoS protection
8. Advanced bot detection
