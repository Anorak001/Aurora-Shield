# Aurora Shield - Task List for Hackathon Demo

## Overview
Implementing a comprehensive DDoS protection system with advanced mitigations, real-time monitoring, and realistic attack simulation capabilities.

---

## 🔥 CRITICAL FIXES (Must complete first)

### ✅ Milestone 1: Load Balancer Pipeline Stability
- [ ] **Fix LB stats tracking in `load_balanced()` and `direct_cdn()`**
  - [ ] Always increment `requests_total`, `requests_allowed/blocked`, `last_request_time`
  - [ ] Ensure CDN failover loop when one CDN fails
  - [ ] Add header forwarding to Shield: `User-Agent`, `Referer`, `Accept-Language`, `Cookie`
  - [ ] Set `AS-Session` cookie on successful responses
  - [ ] File: `docker/load_balancer_app.py`

- [ ] **Shield Manager Request Processing**
  - [ ] Ensure `process_request()` appends to ring buffer for live stream
  - [ ] File: `aurora_shield/shield_manager.py`

**Acceptance:** http://localhost:8090/cdn shows rising totals; blocks increment on 403

---

## 🎯 HIGH PRIORITY FEATURES

### ✅ Milestone 2: Real-time Live Requests Stream
- [ ] **Backend API Implementation**
  - [ ] Add `GET /api/dashboard/live-requests` endpoint
  - [ ] Return `{items: [...], ts: iso}` format
  - [ ] Optional: Add SSE stream for real-time updates
  - [ ] File: `aurora_shield/dashboard/web_dashboard.py`

- [ ] **Frontend Live Updates**
  - [ ] Live Requests tab polls every 1s
  - [ ] Show: timestamp, IP, method, path, decision, reason
  - [ ] Overview tab uses real data from same buffer
  - [ ] File: `aurora_shield/dashboard/templates/aurora_dashboard.html`

**Acceptance:** Live Requests shows real entries with accurate timestamps

### ✅ Milestone 3: Attack Simulator Overhaul
- [ ] **Fix Existing Simulators**
  - [ ] Fix rate calculation: `sleep = 1.0/rate` not `60/rate`
  - [ ] Target `/cdn` endpoints on port 8090
  - [ ] Assign static IPs: 10.0.1.100, 10.0.1.101, 10.0.1.102
  - [ ] File: `docker/attack_simulator_web.py`

- [x] **NEW: Multi-Container Attack Dashboard**
  - [x] Create `docker/attack_orchestrator.py` (Flask app on port 5000)
  - [x] Create `docker/bot_agent.py` (individual bot logic)
  - [x] Create `docker/Dockerfile.bot-agent` (bot container image)
  - [x] Create `docker/Dockerfile.orchestrator` (orchestrator container)
  - [x] Dashboard at `/` with spawn/destroy/coordinate controls
  - [x] API endpoints: `/api/fleet/status`, `/api/fleet/spawn`, `/api/fleet/attack`
  - [x] Bot IP range: 10.77.0.50-250 (50 unique IPs for testing)
  - [ ] Create `docker/attack_orchestrator.py` - main dashboard
  - [ ] Create `docker/bot_agent.py` - lightweight attack client
  - [ ] Create `docker/Dockerfile.orchestrator` - dashboard container
  - [ ] Create `docker/Dockerfile.bot` - bot agent container
  - [ ] Add docker-compose service definitions
  - [ ] Implement bot fleet management API:
    - [ ] `POST /api/fleet/spawn` - create N bot containers
    - [ ] `GET /api/fleet/status` - list active bots with IPs
    - [ ] `POST /api/fleet/attack` - coordinate swarm attack
    - [ ] `POST /api/fleet/destroy` - cleanup bot containers

- [ ] **Swarm Attack Implementation**
  - [ ] Add "Swarm" controls in simulator UI
  - [ ] Spawn N threads with deterministic pseudo-IPs
  - [ ] Show bot count and distribution in UI

**Acceptance:** 20 real containers attacking with unique IPs, visible in Live Requests

### ✅ Milestone 4: Advanced Mitigations
- [x] **Multi-Key Rate Limiting**
  - [x] Create `aurora_shield/mitigation/advanced_limits.py`
  - [x] Implement `AdvancedRateLimiter` with per-IP, per-subnet, per-fingerprint limits
  - [x] Add behavior pattern analysis and fair queuing
  - [x] Integrate in `AuroraShieldManager.process_request()`
  - [x] Global surge protection and suspicious behavior detection

- [ ] **Behavior Rules Engine**
  - [ ] Create `aurora_shield/config/behaviors.yaml`
  - [ ] Create `aurora_shield/core/behavior_rules.py`
  - [ ] Add path/method/header based rules

- [ ] **Legitimate User Detection**
  - [ ] Cookie-based session tracking
  - [ ] Referrer and browser signal analysis
  - [ ] Reputation scoring integration

**Acceptance:** Swarm shows "adv:per_subnet24", "global:concurrency" blocks; browser requests pass

---

## 🎨 MEDIUM PRIORITY ENHANCEMENTS

### ✅ Milestone 5: Dashboard Polish
- [ ] **Load Balancer UI**
  - [ ] Ensure 1-2s polling of `/stats`
  - [ ] Show algorithm, round-robin index, health indicators
  - [ ] Visual CDN offline indicators
  - [ ] File: `docker/templates/load_balancer_enhanced.html`

- [ ] **Aurora Shield UI**
  - [ ] Real-time counters (1s updates)
  - [ ] Recent attacks from live buffer
  - [ ] Performance metrics display

**Acceptance:** UIs update every 2s; CDN toggle shows immediate failover

### ✅ Milestone 6: Observability
- [ ] **Timestamp Consistency**
  - [ ] Millisecond precision on all events
  - [ ] "Last updated" displays in UI
  - [ ] System time synchronization

- [ ] **Logging**
  - [ ] Structured console logs
  - [ ] Optional ELK integration
  - [ ] Performance metrics

**Acceptance:** UI times match system time; clean demo logs

---

## 🚀 STRETCH GOALS (If time permits)

### ✅ Milestone 7: Edge Protection
- [ ] **Nginx Rate Limiting**
  - [ ] Add `limit_req`/`limit_conn` to CDN containers
  - [ ] Update nginx configs
  - [ ] Files: `docker/nginx*.conf`

### ✅ Milestone 8: Monitoring Integration
- [ ] **Prometheus Metrics**
  - [ ] Export LB and Shield counters
  - [ ] Update Grafana dashboard
  - [ ] File: `dashboards/grafana_dashboard.json`

---

## 📋 DEMO CHECKLIST

### Pre-Demo Setup
- [ ] `docker-compose build --no-cache`
- [ ] `docker-compose up -d`
- [ ] Verify all services running
- [ ] Test basic functionality

### Demo Flow (5 minutes)
1. [ ] **Show Normal Traffic**
   - [ ] Start 3 simulators with normal traffic (1 rps × 10s)
   - [ ] Show LB dashboard: round-robin distribution
   - [ ] Show Aurora dashboard: Live Requests stream

2. [ ] **Launch Swarm Attack**
   - [ ] Use new orchestrator to spawn 20 bot containers
   - [ ] Each bot: 2 rps for 30s
   - [ ] Show mitigation in action: rate limits, blocks

3. [ ] **Demonstrate Legitimate Traffic**
   - [ ] Browser visit to http://localhost:8090/cdn/
   - [ ] Show "Allowed" entries with cookie/referrer
   - [ ] Contrast with blocked bot traffic

4. [ ] **Show Failover**
   - [ ] Toggle CDN off in LB UI
   - [ ] Show traffic redistribution
   - [ ] Demonstrate system resilience

### Success Criteria
- [ ] 20+ containers attacking with unique IPs
- [ ] Live Requests showing real decisions (1s updates)
- [ ] Clear separation of legitimate vs attack traffic
- [ ] Round-robin load balancing with failover
- [ ] Multiple mitigation layers visible

---

## 🔧 FILES TO MODIFY/CREATE

### Existing Files
- [ ] `docker/load_balancer_app.py` - stats tracking, header forwarding
- [ ] `aurora_shield/shield_manager.py` - ring buffer, advanced limits
- [ ] `aurora_shield/dashboard/web_dashboard.py` - live requests API
- [ ] `aurora_shield/dashboard/templates/aurora_dashboard.html` - real-time UI
- [ ] `docker/attack_simulator_web.py` - rate fixes, static IPs

### New Files
- [ ] `docker/attack_orchestrator.py` - multi-container attack dashboard
- [ ] `docker/bot_agent.py` - lightweight attack client
- [ ] `docker/Dockerfile.orchestrator` - dashboard container
- [ ] `docker/Dockerfile.bot` - bot agent container
- [ ] `docker/templates/orchestrator_dashboard.html` - fleet management UI
- [ ] `aurora_shield/mitigation/advanced_limits.py` - multi-key limiting
- [ ] `aurora_shield/core/behavior_rules.py` - rules engine
- [ ] `aurora_shield/config/behaviors.yaml` - behavior rules config

---

## 🎯 IMMEDIATE NEXT STEPS

1. **Start with Milestone 1** - Fix LB stats tracking (30 min)
2. **Implement Multi-Container Orchestrator** - New attack dashboard (2 hours)
3. **Add Advanced Mitigations** - Multi-key limiting (1 hour)
4. **Wire Live Requests Stream** - Real-time updates (1 hour)
5. **Polish and Test** - End-to-end demo (1 hour)

---

## 📊 PROGRESS TRACKING

**Current Status:** 🟡 In Progress
- ✅ Round-robin load balancer implemented
- ✅ Enhanced dashboards created
- ✅ Basic attack simulators working
- 🟡 Stats tracking needs fixes
- 🔴 Multi-container orchestration needed
- 🔴 Advanced mitigations missing
- 🔴 Live stream needs real data

**Target Completion:** Next 6-8 hours
**Demo Readiness:** 85% → 100%

---

*Last Updated: 2025-10-11 21:25:00*
*Next Review: After each milestone completion*