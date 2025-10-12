# 🛡️ Aurora Shield - INFOTHON 5.0

**Real-World DDoS Protection Framework with Docker Simulation**

Aurora Shield demonstrates enterprise-level DDoS protection through complete Docker environment simulation. Built for INFOTHON 5.0, it replicates production deployment patterns locally without cloud costs.

## 🌍 Real-World Simulation

### 🏢 Production Architecture Replicated
```
[Client] → [Aurora Shield Gateway] → [Nginx Load Balancer] → [Protected Web App] 
                      ↓
            [Redis (Caching Layer)]
                      ↓
[Prometheus] ← [Aurora Shield Gateway] → [Elasticsearch]
                      ↓
            [Grafana]   [Kibana]
```

### 🐳 Local Docker Environment
- **Aurora Shield Gateway** (Port 8080) - Main protection engine
- **Protected Web App** (Port 80,8081,8082) - Application being secured  
- **Load Balancer** (Port 8090) - Traffic distribution
- **Attack Simulator**(Port 5000) - Realistic threat testing

## ✨ Features

### 🔍 **Real-Time Detection**
- **Rule-Based Anomaly Detection**: Monitors traffic patterns and identifies DDoS attacks in real-time
- **Statistical Analysis**: Reduces false positives using pattern recognition
- **Multi-Layer Protection**: IP reputation tracking, rate limiting, and behavioral analysis

### 🛡️ **Intelligent Mitigation**
- **Rate Limiting**: Token bucket algorithm for fair request throttling
- **IP Reputation System**: Dynamic scoring and automatic blacklisting
- **Challenge-Response**: Proof-of-work verification for suspicious clients
- **Adaptive Thresholds**: Adjusts protection levels based on threat severity

### 🔄 **Auto-Recovery**
- **Automatic Failover**: Seamless switching to backup servers
- **Auto-Scaling**: Dynamic capacity adjustment based on load
- **Traffic Redirection**: CDN integration and intelligent routing
- **Self-Healing**: Automatic recovery from attack conditions

### 📊 **Monitoring & Analytics**
- **Web Dashboard**: Beautiful, real-time monitoring interface
- **ELK Integration**: Elasticsearch, Logstash, Kibana for log analysis
- **Prometheus Metrics**: Time-series metrics for Grafana dashboards
- **Attack Simulation**: Built-in tools for testing protection mechanisms

### 🌐 **Edge Gateway**
- **Flask-Based Gateway**: Production-ready HTTP gateway
- **Nginx/HAProxy Compatible**: Works with existing load balancers
- **API-First Design**: RESTful API for integration

### ☁️ **Cloud Integration**
- **Boto3 Cloud Mock**: Simulates AWS operations for testing
- **Multi-Cloud Ready**: Designed for AWS, Azure, GCP
- **Containerized**: Docker-ready for easy deployment

## 🚀 Quick Docker Demo

### Prerequisites
- Docker Desktop installed
- 8GB+ RAM available  
- Ports 80, 5000, 8080, 8090, free

### Start Complete Environment
```bash
# Clone repository
git clone https://github.com/Anorak001/Aurora-Shield.git
cd Aurora-Shield

# Start all services (one command!)
docker-compose up -d

# Access dashboard
open http://localhost:8080/dashboard
# Login: admin/admin123
```

### Run Client Simulation
```bash
# Automated client simulation
docker-compose run --rm client

# Or use dashboard buttons for manual testing
```

## 🎯 Architecture Components

```
aurora_shield/
├── core/           # Detection algorithms
├── mitigation/     # Protection mechanisms  
├── auto_recovery/  # Self-healing logic
├── dashboard/      # Web interface
├── gateway/        # Edge protection
└── integrations/   # ELK/Prometheus

docker/
├── Dockerfile              # Aurora Shield container
├── docker-compose.yml      # Complete environment
├── client.py     # Client simulator (formerly attack_simulator)
└── monitoring/             # ELK + Grafana configs
```

## 📊 Access Points

| Service | Purpose | URL | Credentials |
|---------|---------|-----|-------------|
| **Aurora Shield** | Main dashboard | http://localhost:8080 | admin/admin123 |
| **Protected App** | Secured application | http://localhost:80 | - |
git clone https://github.com/Anorak001/Aurora-Shield.git
cd Aurora-Shield

# Install dependencies
pip install -r requirements.txt

# Or install as a package
pip install -e .
```

### Run the Dashboard

```bash
# Start Aurora Shield with web dashboard
python main.py
```

The dashboard will be available at `http://localhost:8080`

### Basic Usage

```python
from aurora_shield.shield_manager import AuroraShieldManager
from aurora_shield.config import DEFAULT_CONFIG

# Initialize Aurora Shield
shield = AuroraShieldManager(DEFAULT_CONFIG)

# Process a request
request_data = {
    'ip': '192.168.1.100',
    'timestamp': time.time(),
    'payload_size': 1024
}

result = shield.process_request(request_data)

if result['allowed']:
    # Process the request
    print("Request allowed")
else:
    # Block the request
    print(f"Request blocked: {result['reason']}")
```

## 📖 Documentation

### Project Structure

```
Aurora-Shield/
├── aurora_shield/           # Main package
│   ├── core/               # Anomaly detection engine
│   ├── mitigation/         # Rate limiting, IP reputation, challenges
│   ├── auto_recovery/      # Failover and auto-scaling
│   ├── attack_sim/         # Attack simulation tools
│   ├── integrations/       # ELK and Prometheus integrations
│   ├── gateway/            # Flask edge gateway
│   ├── dashboard/          # Web dashboard
│   ├── config/             # Configuration
│   ├── cloud_mock.py       # Boto3 cloud mock
│   └── shield_manager.py   # Main coordinator
├── examples/               # Example scripts
├── dashboards/             # Kibana and Grafana configs
├── main.py                 # Main entry point
└── requirements.txt        # Dependencies
```

### Components

#### 1. Anomaly Detector
Monitors request patterns and detects anomalies based on configurable thresholds.

```python
from aurora_shield.core.anomaly_detector import AnomalyDetector

detector = AnomalyDetector({
    'request_window': 60,      # Time window in seconds
    'rate_threshold': 100      # Max requests per window
})

result = detector.check_request('192.168.1.100')
```

#### 2. Rate Limiter
Token bucket rate limiting for fair request throttling.

```python
from aurora_shield.mitigation.rate_limiter import RateLimiter

limiter = RateLimiter({
    'rate': 10,    # Tokens per second
    'burst': 20    # Max token capacity
})

result = limiter.allow_request('192.168.1.100')
```

#### 3. IP Reputation
Tracks IP behavior and assigns reputation scores.

```python
from aurora_shield.mitigation.ip_reputation import IPReputation

reputation = IPReputation()

# Record violations
reputation.record_violation('10.0.0.1', 'anomaly', severity=20)

# Check reputation
status = reputation.get_reputation('10.0.0.1')
```

#### 4. Auto Recovery
Automatic failover and scaling based on system metrics.

```python
from aurora_shield.auto_recovery.recovery_manager import RecoveryManager

recovery = RecoveryManager({'max_capacity': 5})

# Assess situation
assessment = recovery.assess_situation({
    'cpu_usage': 85,
    'request_rate': 1500,
    'error_rate': 0.15
})

# Execute recovery actions
for action in assessment['actions']:
    recovery.execute_recovery(action)
```

### Examples

Run the included examples to see Aurora Shield in action:

```bash
# Basic protection example
python examples/basic_protection.py

# Attack simulation example
python examples/attack_simulation.py
```

## 📊 Dashboard Features

The web dashboard provides:

- **Real-time Metrics**: Live updates of protection status
- **Attack Visualization**: Visual representation of detected attacks
- **IP Management**: View and manage blocked/whitelisted IPs
- **Control Panel**: Manual controls for testing and management
- **Statistics**: Comprehensive system statistics

## 🔧 Configuration

Configure Aurora Shield by modifying the config dictionary:

```python
config = {
    'anomaly_detector': {
        'request_window': 60,
        'rate_threshold': 100,
    },
    'rate_limiter': {
        'rate': 10,
        'burst': 20,
    },
    'ip_reputation': {
        'initial_score': 100,
    },
    'recovery_manager': {
        'max_capacity': 5,
    }
}

shield = AuroraShieldManager(config)
```
## 🧪 Testing

Aurora Shield includes attack simulation tools for testing:

```python
from aurora_shield.attack_sim.simulator import AttackSimulator

simulator = AttackSimulator()

# Simulate HTTP flood
result = simulator.simulate_http_flood(
    target='example.com',
    duration=60,
    requests_per_second=150
)

# Simulate distributed attack
result = simulator.simulate_distributed_attack(
    target='example.com',
    bot_count=100,
    duration=60
)
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with Flask for web components
- Uses NumPy for ML calculations
- Boto3 integration for cloud operations
- Inspired by modern DDoS protection solutions

## 📞 Support

For issues, questions, or contributions, please open an issue on GitHub.

---

**Made with ❤️ by the Aurora Shield Team**
