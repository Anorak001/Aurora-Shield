## Aurora Shield — Contributor Manual

Welcome! This manual is written for contributors of all levels — from beginners to advanced engineers — who want to understand, run, extend, or contribute to Aurora Shield. It explains the project's purpose, architecture, every technology used, cloud and security concepts, the attacks simulated here, mitigations implemented, and practical contribution guidelines.

This document aims to be thorough and beginner-friendly. If anything is unclear or you'd like a deeper dive on a specific area, open an issue or a pull request with your suggestion.

---

## Table of contents

- Project overview
- Quick start (local + Docker demo)
- Code structure and important files
- Complete technology glossary and how each is used here
  - Python & Flask
  - Jinja templating
  - Redis
  - Docker & docker-compose
  - Nginx (reverse proxy / load balancer)
  - Prometheus
  - Grafana
  - Elasticsearch & Kibana (ELK)
  - aiohttp / requests / async clients
  - Chart.js and front-end components
  - Other Python libraries (prometheus_client, elasticsearch-py, redis-py)
- Cloud & networking concepts (detailed)
  - Load balancing, reverse proxies, CDN, edge vs origin
  - VPC, subnets, public/private endpoints
  - Autoscaling, health checks, and failover
  - TLS, certificates, and secure transport
  - DNS, Anycast, and geo-routing
  - WAFs, API gateways, and rate limiting at the edge
- Attacks explained (detailed, with detection signals)
  - HTTP(S) flood (application-layer DDoS)
  - Slowloris / slow-read & slow-post attacks
  - SYN / TCP-level floods (overview)
  - UDP / amplification (overview)
  - Botnet / distributed attacks and distinguishing signals
  - Application-layer business logic abuse
- Mitigations implemented in Aurora Shield (what, why, how)
  - Rate limiting
  - IP reputation & black/whitelisting
  - Challenge-response (CAPTCHA-like puzzles)
  - Circuit breakers / fail-open vs fail-closed decisions
  - Auto-recovery (traffic shaping, restart logic)
  - Observability and alerting
- Security considerations & best practices for contributors
  - Secrets management
  - Secure defaults (cookies, sessions, headers)
  - Authentication & authorization
  - Input validation & content security
  - Logging, retention, and PII concerns
- Observability & incident response
  - Important metrics and logs used in the project
  - Dashboards and alerts (Grafana / Kibana pointers)
  - Forensics & post-incident analysis
- How to extend the project and common contribution patterns
  - Adding a new mitigation rule or detector
  - Adding a new integration (Prometheus, Grafana dashboard, ELK parser)
  - Tests and CI guidance
  - Pull request checklist
- Glossary (short definitions)
- Further reading and references

---

## Project overview

Aurora Shield is a learning and demonstration project focused on detecting and mitigating network- and application-level attack traffic (notably DDoS-style events) at the application edge. It provides:

- A Flask-based control plane and dashboard for configuration and monitoring.
- A set of detectors and mitigation strategies implemented in Python modules.
- An attack simulator (local/demo) so contributors can reproduce and test mitigation strategies.
- Integrations for observability (Prometheus metrics + Grafana dashboards) and logging/search (Elasticsearch + Kibana).

The repository contains modular components: core detection logic, mitigation hooks, a dashboard, and integrations so that contributors can experiment with strategies and visualizations.

## Quick start (developer-friendly)

These commands assume you have Python 3.9+ and optionally Docker installed.

1) Create a virtual environment and install Python dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2) Run the app locally (development):

```powershell
python main.py
# open http://127.0.0.1:5000

```

3) Run the Docker demo (if you want the full stack: Nginx demo app, load balancer, Prometheus, Grafana, Elasticsearch, Kibana, attack-simulator):

```powershell
docker-compose up --build
# or use provided scripts: docker\setup.bat (Windows) or docker/setup.sh (Unix)
```

Note: The project had several Docker helper files and a demo scenario. The Docker demo is useful because it creates isolated services locally and replicates an environment closer to a real-world deployment.

---

## Code structure and important files

Top-level files:

- `main.py` — Entry point for running the Flask dashboard and starting necessary background components in development.
- `requirements.txt` — Python dependencies used by the project.
- `setup.py` — Packaging metadata (minimal usage in this repo).
- `README.md`, `DOCKER_DEMO.md` — User-facing docs and demo instructions.

Package: `aurora_shield/`

- `__init__.py` — package initialization.
- `cloud_mock.py` — a small module faking cloud services for local testing (if present).
- `shield_manager.py` — central manager that coordinates detectors, mitigation modules, and system state.
- `attack_sim/` — attack simulator code that can generate benign and malicious traffic for testing detectors.
- `auto_recovery/` — modules controlling automated recovery actions after mitigation.
- `config/default_config.py` — default configuration values for detectors and mitigation thresholds.
- `core/anomaly_detector.py` — core statistical or ML-based anomaly detection logic.
- `dashboard/web_dashboard.py` — Flask views and API endpoints that provide the UI and REST API.
- `gateway/flask_gateway.py` — an optional HTTP gateway front to the shield logic.
- `integrations/` — integration helpers for Prometheus metrics, Elasticsearch logs, Grafana provisioning, etc.
- `mitigation/` — implementations of mitigation strategies: `rate_limiter.py`, `challenge_response.py`, `ip_reputation.py`, `rate_limiter.py`.
- `ml_analysis/` — optional ML-driven detectors.

When contributing, pick the module relevant to your change. Follow the file comments and read module docstrings.

---


## Technology glossary — what each tech is and how it's used here (expanded)

Below are deeper, practical descriptions for the technologies used in Aurora Shield. Each entry includes an overview, why it matters, how the project uses it, important production considerations, configuration tips, common pitfalls, and short examples or commands where helpful.

### Python (3.9+)

- Overview: Python is a dynamically typed, interpreted language with concise syntax and a rich standard library. It's commonly used for web services, scripting, data analysis, and automation.
- Why it matters here: Rapid prototyping of detectors and mitigations, wide library ecosystem (async IO, ML, HTTP clients), and readability for contributors.
- How Aurora Shield uses it: All server-side logic — dashboard, detectors, mitigation hooks, simulator — are Python modules. The repo structure and packaging assume Python modules importable via normal Python imports.
- Production considerations:
  - Use a WSGI/ASGI server (Gunicorn, Uvicorn) behind a reverse proxy for production.
  - Pin dependency versions in `requirements.txt` or use a lock file (pip-tools/Poetry) to avoid drifting dependencies.
  - Use virtual environments in development and CI containers for reproducible builds.
- Common pitfalls:
  - Blocking operations in the main thread (use async where necessary for high concurrency)
  - Inconsistent dependency versions between dev and production
  - Missing type hints make refactors riskier — consider adding type hints and simple mypy checks for critical modules.

### Flask

- Overview: Small web framework for building APIs and web applications quickly. It uses Werkzeug (WSGI) and Jinja for templating.
- Why it matters: Minimal footprint, flexible routing, and easy to integrate with middleware and extensions.
- How Aurora Shield uses it: The dashboard and API endpoints are built with Flask. It provides session management for demo auth, `render_template()` (Jinja), and endpoint routing.
- Production considerations:
  - Run Flask with a process manager and WSGI server (e.g., Gunicorn with multiple workers) to handle concurrency and manage memory.
  - Configure logging to stdout/stderr so container platforms capture logs.
  - Avoid running the built-in development server in production — it's not hardened for concurrent or adversarial traffic.
- Example run (development):

```powershell
set FLASK_APP=aurora_shield.dashboard.web_dashboard
flask run --host=0.0.0.0 --port=5000
```

- Common pitfalls:
  - Storing secret keys in code (use env vars)
  - Relying on Flask sessions for production auth without secure cookie flags and server-side session stores

### Jinja templating

- Overview: Templating engine allowing variable interpolation, control structures, and inheritance for HTML pages.
- How Aurora Shield uses it: Renders dashboard pages and embeds JavaScript that fetches metrics/APIs.
- Security notes:
  - Always escape untrusted values (Jinja auto-escapes by default for HTML contexts).
  - Avoid constructing HTML by concatenating strings in Python — prefer using templates.

### Redis

- Overview: Fast in-memory data store. Use cases: caching, counters, pub/sub, session storage, sorted sets for leaderboards, simple queues.
- How Aurora Shield uses it: Rate limit counters, IP reputation store, session sharing across containers, and transient state for circuit breakers.
- Production considerations:
  - Use persistence (AOF/RDB) if you need state after restarts, or treat Redis as ephemeral and rebuild state on boot.
  - Configure `requirepass` or ACLs and restrict access via VPC/security-groups.
  - Monitor memory usage and eviction policies; small misconfigurations can lead to surprising data loss.
- Example Redis usage (Python):

```python
import redis
r = redis.Redis(host='redis', port=6379, db=0)
# increment a counter
r.incr('requests:count')
```

- Common pitfalls:
  - Leaving Redis exposed on the public internet
  - Using Redis as a primary datastore for critical data without persistence and backups

### Docker & docker-compose

- Overview: Containerization platform (`docker`) and multi-service orchestration for local setups (`docker-compose`).
- How Aurora Shield uses them: The repo includes Dockerfiles and `docker-compose.yml` to run a demo stack locally (shield app, demo webapp, Nginx, Redis, Prometheus, Grafana, Elasticsearch, Kibana, attack simulator).
- Development tips:
  - Use multi-stage builds to keep images small.
  - Mount source code as volumes in development containers to avoid rebuilding for every change.
  - Use `.dockerignore` to avoid copying unnecessary files into images.
- Example (build+run):

```powershell
docker-compose up --build --detach
docker-compose logs -f aurora-shield
```

- Production notes:
  - For production, prefer orchestrators like Kubernetes or managed container platforms.
  - Do not run `docker-compose` for production-critical infrastructure; it's a local development tool.

### Nginx (reverse proxy / load balancer)

- Overview: High-performance HTTP server and reverse proxy used widely as an edge component.
- How used in Aurora Shield: Demo Nginx config simulates an edge reverse proxy and performs TLS termination, static content serving, and basic rate limiting. It can forward `X-Forwarded-For` to the Python app.
- Production tips:
  - Use `proxy_read_timeout` and `proxy_connect_timeout` to defend against slow-client attacks.
  - Offload TLS at Nginx and use HTTP between internal services.
  - Leverage Nginx `limit_conn` and `limit_req` for coarse rate limiting at the proxy.
- Example snippet (rate limiting):

```
limit_req_zone $binary_remote_addr zone=one:10m rate=30r/s;
server {
  location / {
    limit_req zone=one burst=60 nodelay;
    proxy_pass http://backend;
  }
}
```

### Prometheus

- Overview: Time-series database and monitoring system. Metrics are scraped from instrumented endpoints.
- How used here: The shield exposes metrics (Counters, Gauges, Histograms) via `prometheus_client`. Prometheus scrapes these metrics and stores them for queries and alerting.
- Metrics design tips:
  - Label cardinality matters: avoid high-cardinality labels (e.g., raw client IP) on frequently scraped counters — use top-N aggregation instead.
  - Use histograms for latency and buckets that match your SLOs.
- Example Python metric:

```python
from prometheus_client import Counter, Histogram
REQUESTS = Counter('requests_total', 'Total HTTP requests', ['endpoint', 'method'])
LATENCY = Histogram('request_duration_seconds', 'Request latency', ['endpoint'])

def handle_request(req):
    REQUESTS.labels(endpoint='/api', method='GET').inc()
    with LATENCY.labels(endpoint='/api').time():
        # handle
        pass
```

### Grafana

- Overview: Visualization/UI for time-series data with panels, alerts, and dashboard provisioning.
- How used here: Grafana connects to Prometheus (and Elasticsearch optionally) to show traffic patterns, mitigation events, and heatmaps.
- Tips:
  - Provision dashboards via JSON and YAML to keep dashboards under version control.
  - Use alert rules for sustained anomalies (e.g., 5-minute sustained RPS above baseline).

### Elasticsearch & Kibana (ELK stack)

- Overview: Elasticsearch stores and indexes logs/events; Kibana is used to search and visualize those logs.
- How used here: Structured application logs (JSON) are shipped to Elasticsearch so Kibana can be used for queries and incident forensics (search by IP, endpoint, mitigation action).
- Production tips:
  - Use ILM (Index Lifecycle Management) to control retention and roll-over indices to keep disk usage manageable.
  - Protect Elasticsearch with authentication and network restrictions.
  - Consider sampling or log levels to reduce high-volume noisy logs during attacks.

### aiohttp, requests (HTTP clients & servers)

- Overview: `requests` for synchronous HTTP calls; `aiohttp` for async HTTP clients/servers (high throughput when used correctly).
- How used here: The attack simulator uses `aiohttp` to create many concurrent connections and requests efficiently. `requests` is used for simple single-threaded operations.
- Tips:
  - Use connection pooling and reuse sessions to avoid creating sockets for each request.
  - Limit concurrency to what the local machine can sustain when simulating load.

### Chart.js (front-end)

- Overview: Browser-side charting library using HTML5 Canvas.
- How used here: Visualize time-series and summary metrics in the dashboard. Good for simple visualizations and demos.
- Tip: For high-frequency real-time streams, consider using a WebSocket + chart streaming plugin rather than repeated long-polling requests.

### prometheus_client (Python library)

- Overview: Small library that exposes Prometheus-compatible HTTP endpoints for metrics.
- How used here: Exposes `/metrics` so Prometheus can scrape counters and histograms from the shield.
- Tip: Start the metrics HTTP server on a dedicated port or integrate the metrics endpoint into the Flask app behind /metrics. Ensure metrics exposure is not easily accessible if you have sensitive information.

### elasticsearch-py (Python client)

- Overview: Official Python client to index and query documents in Elasticsearch.
- How used here: Write structured logs and queries used by dashboard endpoints or forensic scripts.
- Tips:
  - Use bulk indexing to improve performance when ingesting many logs.
  - Catch and handle transient network errors; the client can be configured with retries.

### redis-py

- Overview: Python client for Redis with sync APIs. For async use `aredis` or `aioredis`.
- How used here: Read/write counters, TTLs, and simple locks for cross-process synchronization.
- Tips:
  - Use Redis `SETNX` for safe leader election or short-lived locks.
  - Monitor and set `maxmemory` and eviction policy to avoid OOM events.


---

## Cloud & networking concepts (detailed)

This section explains many core cloud and networking concepts and how they relate to Aurora Shield. Reading this will help you understand how the project models real deployment choices.

### Load balancers and reverse proxies

- Purpose: Distribute incoming traffic to multiple backend instances, provide TLS termination, and offload some edge policies.
- Types: Layer 4 (TCP) vs Layer 7 (HTTP) load balancing. Managed cloud LB (AWS ALB/ELB, GCP LB) provide health checks and auto-scaling integration.
- How this project models it: The demo uses Nginx as a simple Layer 7 reverse proxy to mimic a cloud load balancer.

Why it matters for DDoS: The load balancer is the first place to apply simple edge mitigations (e.g., connection rate limiting, geo-blocking, WAF rules).

### CDN and Edge

- Purpose: Cache static content close to users, absorb traffic spikes, and mitigate certain volumetric attacks.
- How: CDNs use many PoPs globally and can drop or challenge suspicious traffic.
- Project relevance: The demo does not run a CDN, but every production deployment should consider a CDN in front of the app to reduce attack surface and cost.

### VPC, subnets, public/private endpoints

- VPC: Virtual Private Cloud isolates networks in cloud providers.
- Public vs private: Public subnets have internet gateways; private subnets don't. Place sensitive services (databases, Elasticsearch, Redis) in private subnets.
- How used here: Locally, Docker networks mimic these separations; in production, you must ensure Elasticsearch and Redis are not publicly exposed.

### Autoscaling, health checks, and failover

- Purpose: Scale out/in based on load and automatically recover unhealthy instances.
- Health checks: Load balancers query endpoints (e.g., `/health`) to decide routing.
- How to use with Aurora Shield: Detection thresholds, auto-recovery strategies and circuit breakers must be used in concert with autoscaling — e.g., don't just block traffic; scale resources where needed and apply mitigations at the edge.

### TLS, Certificates, and Secure Transport

- Use TLS to protect client-server communication.
- In the demo TLS termination may be simulated at Nginx. In production, use strong TLS configurations, managed certs (Let's Encrypt, ACM), and HSTS when appropriate.

### DNS, Anycast, and Geo-routing

- Anycast helps route traffic to the nearest PoP by sharing an IP address from multiple locations — often used by large CDNs and DDoS scrubbing networks.
- DNS-based routing can help shift traffic away from stressed regions.

### WAFs and API Gateways

- WAF: Inspects HTTP requests for known attack patterns (SQLi, XSS) and can block or challenge suspicious requests.
- API gateways can apply rate limits, authentication, and request validation at scale.

### Observability (metrics, logs, traces)

- Metrics: numerical time-series (Prometheus). Useful for real-time alerting.
- Logs: event records (Elasticsearch/Kibana). Useful for forensics and detailed analysis.
- Traces: distributed tracing (OpenTelemetry) helps correlate requests across services.

Aurora Shield combines metrics (Prometheus) for real-time dashboards and logs (ELK) for forensic analysis.

---


## Attacks explained (what they are, how to detect them here) — expanded

This section expands each attack with detection heuristics, instrumentation ideas, typical log entries, Prometheus expressions you can use to alert, and suggested response behaviors. The goal is to make it clear how a detector should behave and what data to record.

### 1) HTTP(S) flood (application-layer DDoS)

- Summary: High volume of HTTP requests aiming to exhaust application resources. These requests often appear syntactically valid (real URLs, valid headers), which makes them harder to filter.
- Detailed detection signals and instrumentation:
  - Sudden RPS spike relative to a rolling baseline. Use moving-window baselines (e.g., compare 1m rate to 1h median).
  - CPU and request-duration histograms increase concurrently with RPS.
  - Error-rate (5xx) increases and backend queue lengths grow.
  - Many requests from previously unseen IPs or from IPs with low reputation.
  - Header/UA entropy: attackers sometimes reuse identical User-Agent, Accept headers, or other fingerprintable values.
  - Abnormal request distribution: disproportionate requests to expensive endpoints (e.g., /search, /report).
- Example logs to emit (structured JSON):

```
{
  "ts":"2025-10-07T12:01:02Z",
  "client_ip":"203.0.113.1",
  "endpoint":"/search",
  "method":"GET",
  "status":200,
  "latency_ms":420,
  "mitigation_action":null
}
```

- Example Prometheus alert expression:

```
# alert when 1m request rate > 3x 1h median
ratio( sum(rate(requests_total[1m])) , sum(median_over_time(rate(requests_total[1h])[1h])) ) > 3
```

- Typical mitigation response:
  - Apply coarse rate limits at the proxy (Nginx) and finer token-bucket limits per IP or API key.
  - Start progressive challenge-response flows for suspicious clients.
  - Cache responses for common URIs to reduce backend load.

### 2) Slowloris / slow-read & slow-post attacks

- Summary: Attackers hold connections open and send bytes extremely slowly to exhaust connection slots.
- Detection signals and instrumentation:
  - Connection durations skew upward; track histogram of connection open time.
  - Many connections with negligible bytes transferred per second.
  - High count of connections in `ESTABLISHED` for long durations.
  - Low request completion rate per established connection.
- Example Prometheus metric to expose:

```
connection_duration_seconds_bucket{le="1"} 123
connection_duration_seconds_bucket{le="10"} 234
connection_duration_seconds_bucket{le="60"} 345
```

- Mitigations:
  - Lower `client_header_timeout`, `client_body_timeout` and similar timeouts at the proxy.
  - Drop idle/slow connections earlier at the edge.
  - Use connection limits per IP and global connection caps.
  - Employ TCP-level protections (SYN cookies on the host) to avoid kernel resource exhaustion.

### 3) SYN flood and TCP-level resource attacks

- Summary: Low-level TCP attacks that aim to fill kernel SYN queues or exhaust socket resources.
- Signals:
  - High rate of incoming SYN packets compared to established connections.
  - Kernel counters like `synack_retries` or high `tcp_max_syn_backlog` usage.
- Detection & response:
  - Kernel-level counters can be exported with node-exporter and monitored in Prometheus.
  - Mitigation often requires network-layer controls: rate-limit SYNs via firewall, enable SYN cookies, or route to scrubbing providers.

### 4) UDP amplification / reflection attacks (overview)

- Summary: Attackers use open UDP services (DNS, NTP, memcached) to reflect and amplify traffic toward a target.
- Project note: Not simulated here, but operationally critical. Detection requires network telemetry; mitigation requires ACLs, upstream scrubbing, and proper service hardening.

### 5) Botnet / distributed attacks

- Summary: Coordinated attacks from many distributed, often low-power clients (IoT devices, compromised hosts). These are high-cardinality source attacks that try to blend in.
- Detection signals and heuristics:
  - High cardinality of source IPs with similar behavior (e.g., same UA, same URI rate patterns) — compute top-k offending IPs and also monitor entropy of UA and accept headers.
  - Sudden growth in first-time-seen IPs.
  - Failed Javascript/Cookie checks (bots often don't execute JS) or lack of expected session flows.
- Mitigations:
  - Progressive challenges (JS-based fingerprinting, CAPTCHA, proof-of-work) — tune challenge difficulty to minimize false positives.
  - Network-level throttles and reputation blocking for known bad CIDR ranges.
  - Behavioral baselining and ML models to identify clusters of similar behavior.

### 6) Application-layer business logic abuse

- Summary: Attackers exploit expensive endpoints (search, aggregate endpoints) by repeatedly calling them; this can be done by a single IP or distributed set.
- Detection signals:
  - Per-endpoint CPU and DB usage correlation.
  - Large or expensive queries repeated often from same source or multiple sources.
- Mitigations:
  - Per-endpoint quotas, time-based throttles, and caching of expensive results.
  - Circuit breakers to trip and return degraded responses (e.g., cached partial results) when backend thresholds exceed SLOs.

---

## Mitigations implemented in Aurora Shield — expanded

This section expands each mitigation with implementation details, interfaces you can use in code, the metrics to expose for each, tuning knobs, and possible failure modes to watch.

### Rate limiting (fine-grained)

- What & why: Limit the number of requests per key (IP, user, token) over time to cap resource consumption.
- Implementation patterns:
  - Fixed-window (simple counters per interval) — easy but can be bursty at window boundaries.
  - Sliding-window or leaky-bucket / token-bucket — smoother rate enforcement.
  - Use Redis to store counters with TTL (single-node) or use distributed counters with Lua scripts (to ensure atomic increment+expire semantics).
- Example Redis Lua pattern: increment counter and set TTL atomically to avoid race conditions.
- API surface in code: a `RateLimiter` class with methods `allow(client_key)` returning (allowed: bool, remaining: int, reset_seconds: int).
- Metrics to expose:
  - `rate_limiter_allowed_total`, `rate_limiter_blocked_total`, `rate_limiter_remaining` (Gauge per key is high-cardinality so avoid exposing per-IP as a metric; instead expose aggregated counts and top-N counters in logs).
- Tuning knobs:
  - Rate (requests per second), burst allowance, penalty duration, and whether enforcement is soft (throttle) or hard (drop/block).
- Failure modes:
  - Overly aggressive defaults causing false positives; require whitelist/allowlist for known bots/search crawlers; gradually ramp rules.

### Progressive challenge-response (staged mitigations)

- What & why: Instead of immediately blocking, the system issues challenges that raise the cost for clients. This reduces collateral damage for legitimate users.
- Implementation details:
  - Stage 0: soft throttle (delays responses) + fingerprint collection
  - Stage 1: lightweight JS challenge (browser must execute JS and set a token)
  - Stage 2: interactive CAPTCHA or proof-of-work
  - Stage 3: hard block / 403
- Code hooks: `challenge_response.issue_challenge(client_key)` and `challenge_response.verify(token)`.
- Metrics: `challenges_issued_total`, `challenges_succeeded_total`, `challenges_failed_total`.
- UX notes: Keep fallback flows for clients that cannot run JS (APIs, non-browser clients).

### IP reputation, black/whitelisting, and CIDR controls

- What: Leverage historical data and external feeds to quickly block known bad actors and avoid blocking good actors.
- Implementation: Maintain a TTL-backed Redis store mapping IP -> score + tags. Use external integrations (`integrations/reputation_*`) to enrich scores.
- Metrics: `reputation_blocked_total`, `reputation_score_distribution` (histogram/buckets).
- Pitfalls: Reputation feeds can be noisy and may cause collateral damage — include manual override and whitelisting paths.

### Circuit breaker & endpoint cost accounting

- What: Prevent backend collapse by tripping and returning safe fallback responses for high-cost endpoints.
- Implementation ideas:
  - Maintain per-endpoint counters for errors, latency, and DB queue length.
  - Use an exponential backoff and half-open probe window to test recovery.
  - Store circuit state in Redis for multi-process availability.
- Metrics: `circuit_open_total`, `circuit_half_open_total`, `circuit_recovered_total`.

### Connection-level protections (proxy/kernel)

- What: Defend against slow and TCP-level attacks at the connection layer.
- Implementation:
  - Configure proxy timeouts (`client_header_timeout`, `client_body_timeout`).
  - Use `limit_conn`/`limit_req` in Nginx for coarse protection.
  - In environments where you control the host, enable SYN cookies, tune `tcp_max_syn_backlog`, and use firewall rules (ipset, nftables) to block offending CIDRs.

### Autoscaling & absorb (cloud-native)

- What: For volumetric traffic, absorbability matters — autoscale and use CDNs or scrubbing services.
- Integration plan for Aurora Shield:
  - Provide hooks in `auto_recovery/recovery_manager.py` to call cloud autoscaling APIs when safe.
  - Add CDN integration points (purge cache, route through scrubbing provider) in `integrations/`.

### Observability-driven mitigation (closed-loop)

- What: Use metrics and logs to drive automation and manual triage.
- Implementation:
  - Expose clear, low-cardinality metrics for alerting.
  - Correlate logs (Elasticsearch) with metrics spikes to find root causes.
  - Provide a single

---

## Security considerations & best practices for contributors

Security is essential. The following are recommended guidelines and changes you should make or check when contributing.

### Secrets management

- Never commit secrets (API keys, passwords, certs) to source control.
- Use environment variables, secret managers (AWS Secrets Manager, Azure Key Vault), or a `.env` file that is gitignored for local development.

### TLS & headers

- Use HTTPS in production and set secure cookie flags: `Secure`, `HttpOnly`, and `SameSite` as appropriate.
- Add security headers: `Content-Security-Policy`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`.

### Authentication & authorization

- The demo uses simple session-based auth for convenience. For any real deployment, use strong authentication, proper password hashing (bcrypt/argon2), and consider OAuth/OIDC for federated identity.

### Input validation & output encoding

- Validate and sanitize all user input. Encode output to avoid XSS.

### Logging & PII

- Avoid logging personal data, API keys, or secrets. Consider masking or hashing sensitive fields.

### Rate limiting and open endpoints

- Apply rate limits to public-facing endpoints, especially authentication, password reset, and any expensive API.

---

## Observability & incident response

This project instruments metrics and logs for visibility. Here are important metrics and what to watch:

- `requests_total` (counter): total incoming HTTP requests.
- `requests_per_endpoint` (labels): the distribution of traffic.
- `mitigations_triggered_total` (counter): how often a mitigation fired.
- `blocked_requests_total` (counter): how many requests were blocked.
- `request_duration_seconds` (histogram): latency distribution.

Logging
- Structured logs (JSON) are forwarded to Elasticsearch in the demo. Key fields include `timestamp`, `client_ip`, `endpoint`, `status`, `mitigation_action`.

Dashboards & alerts
- Grafana dashboards visualize the above metrics. Alerts should be configured for sustained high RPS, high error rates, and high mitigation counts.

Forensics
- In an incident, combine Prometheus metrics (to understand when it started and how severe it was) and Kibana logs (to find offender IPs, identify request patterns, and gather evidence).

---

## How to extend the project and contribution patterns

This project is modular; common contribution patterns include adding detectors, mitigation rules, or integrations.

1) Pick a task and create an issue describing the intended change.

2) Create a feature branch off `main`:

```powershell
git checkout -b feat/my-new-detector
```

3) Implement with tests and documentation:

- Add unit tests for logic in `tests/` (project may not include a tests folder yet — add one next to the relevant module).
- Keep functions small and testable. Decouple side effects (network, Redis) behind interfaces to make unit tests deterministic.

4) Update `requirements.txt` if you add dependencies and explain why.

5) Run linters and tests locally. We recommend `flake8` or `pylint` for style and `pytest` for test runs (if you add tests).

6) Submit PR and include a description of design choices and security considerations. Link to the issue you created.

### Adding a new mitigation

- Steps:
  - Add a module in `mitigation/` implementing a clear interface (e.g., `should_block(request_info) -> (action, metadata)`).
  - Register it with `shield_manager` so it is considered during request evaluation.
  - Add Prometheus metrics for actions the mitigation takes.
  - Add unit tests verifying expected behavior.

### Adding a new integration (e.g., external reputation service)

- Create a client under `integrations/` with a configurable adapter. Keep credentials out of source control; use environment variables.

### Adding dashboards

- Grafana dashboards are JSON — put them in a `grafana/` or `dashboards/` folder and add provisioning YAML for local demos.

### Tests and CI

- Add unit tests for core logic using `pytest`.
- Consider adding a GitHub Actions workflow to run tests and linters on PRs.

### Pull request checklist

- [ ] Code builds and passes linting locally.
- [ ] Unit tests added for new features.
- [ ] README or `manual.md` updated if new behavior is user-visible.
- [ ] No secrets are committed.
- [ ] Add a short design note in the PR describing reasoning and trade-offs.

---

## Glossary (short)

- DDoS: Distributed Denial of Service — many clients attempt to exhaust resources.
- WAF: Web Application Firewall.
- CDN: Content Delivery Network.
- PoP: Point of Presence — CDN/edge location.
- SLI / SLO: Service Level Indicator / Service Level Objective.
- TTL: Time To Live.

---

## Further reading and references

- The practice of system design for DDoS-mitigation: vendor docs (Cloudflare, AWS Shield, Google Cloud Armor)
- Prometheus docs: https://prometheus.io/docs/
- Grafana docs: https://grafana.com/docs/
- Elasticsearch & Kibana: https://www.elastic.co/guide/
- Flask: https://flask.palletsprojects.com/

---

## Closing notes for contributors

This manual should give you a strong starting point to understand the codebase, the technologies it uses, the attacks it simulates, and the mitigations in place. Start small: pick a detector or a dashboard tweak, write tests, and open a PR. If you hit any blockers or have suggestions for improving this manual or the project, open an issue.

Thank you for contributing!
