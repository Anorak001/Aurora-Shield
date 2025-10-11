# 🐳 Aurora Shield Docker Demo - INFOTHON 5.0

Complete local Docker simulation environment for Aurora Shield DDoS Protection System.

## 🚀 Quick Start

### Prerequisites
- Docker Desktop installed
- Docker Compose installed
- 8GB+ RAM available
- Ports 80, 3000, 5601, 6379, 8080, 8090, 9090, 9200 available

### Windows Setup
```bash
cd Aurora-Shield
docker\setup.bat
```

### Linux/Mac Setup
```bash
cd Aurora-Shield
chmod +x docker/setup.sh
./docker/setup.sh
```

### Manual Setup
```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop everything
docker-compose down
```

## 🌐 Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| **Aurora Shield Dashboard** | http://localhost:8080 | admin/admin123 |
| **Protected Web App** | http://localhost:80 | - |
| **Load Balancer** | http://localhost:8090 | - |
| **Kibana (Logs)** | http://localhost:5601 | - |
| **Grafana (Monitoring)** | http://localhost:3000 | admin/admin |
| **Prometheus** | http://localhost:9090 | - |

## 🚨 Attack Simulation

### Run Complete Demo Scenario
```bash
docker-compose run --rm attack-simulator
```

### Manual Attack Testing
```bash
# HTTP Flood
curl -X POST http://localhost:8080/api/dashboard/simulate \
  -H "Content-Type: application/json" \
  -d '{"type": "http_flood"}'

# Distributed Attack
curl -X POST http://localhost:8080/api/dashboard/simulate \
  -H "Content-Type: application/json" \
  -d '{"type": "distributed"}'

# Slowloris Attack
curl -X POST http://localhost:8080/api/dashboard/simulate \
  -H "Content-Type: application/json" \
  -d '{"type": "slowloris"}'
```

## 📊 Demo Flow for INFOTHON 5.0

1. **Start Environment**: `docker-compose up -d`
2. **Open Dashboard**: http://localhost:8080 (admin/admin123)
3. **Show Protected App**: http://localhost:80
4. **Run Attack Simulation**: `docker-compose run --rm attack-simulator`
5. **Monitor in Real-time**: 
   - Dashboard for live stats
   - Kibana for detailed logs
   - Grafana for metrics visualization
6. **Show Recovery**: Watch auto-scaling and traffic redirection

## 🏗️ Architecture

```
[Internet] → [Load Balancer:8090] → [Aurora Shield:8080] → [Protected App:80]
                                           ↓
[Monitoring Stack: Kibana:5601, Grafana:3000, Prometheus:9090]
                                           ↓
[Data Storage: Elasticsearch:9200, Redis:6379]
```

## 📈 Monitoring Stack

- **Elasticsearch**: Log storage and search
- **Kibana**: Log visualization and analysis
- **Prometheus**: Metrics collection
- **Grafana**: Advanced metrics dashboard
- **Redis**: Caching and session storage

## 🛠️ Troubleshooting

### Service Not Starting
```bash
# Check service status
docker-compose ps

# View specific service logs
docker-compose logs aurora-shield
docker-compose logs elasticsearch
```

### Port Conflicts
Edit `docker-compose.yml` to change port mappings:
```yaml
ports:
  - "8080:8080"  # Change first number
```

### Memory Issues
```bash
# Check resource usage
docker stats

# Restart with more memory
docker-compose down
docker-compose up -d
```

## 🎯 INFOTHON 5.0 Demo Script

1. **Introduction** (2 min)
   - Show architecture diagram
   - Explain Aurora Shield components

2. **Normal Operation** (3 min)
   - Login to dashboard
   - Show real-time monitoring
   - Display protected application

3. **Attack Simulation** (5 min)
   - Start attack simulator
   - Show real-time detection
   - Demonstrate mitigation

4. **Advanced Monitoring** (3 min)
   - Open Kibana for log analysis
   - Show Grafana metrics
   - Explain auto-scaling

5. **Recovery & Scaling** (2 min)
   - Show auto-recovery
   - Traffic redirection
   - System optimization

## 🔧 Development

### Adding New Features
```bash
# Edit source code
# Rebuild container
docker-compose build aurora-shield

# Restart service
docker-compose restart aurora-shield
```

### Custom Attack Simulations
Edit `docker/attack_simulator.py` to add new attack types.

### Dashboard Customization
Modify `aurora_shield/dashboard/web_dashboard.py` for UI changes.

## 📦 Production Deployment

This Docker setup is perfect for:
- ✅ INFOTHON 5.0 demos
- ✅ Development testing
- ✅ Proof of concept
- ❌ Production use (needs security hardening)

For production, consider:
- SSL/TLS certificates
- Proper authentication
- Resource limits
- Security scanning
- High availability setup

## 🎉 Success Metrics

Your demo is successful if:
- ✅ All services start without errors
- ✅ Dashboard shows real-time data
- ✅ Attack simulations trigger alerts
- ✅ Monitoring shows mitigation
- ✅ Auto-recovery works
- ✅ Judges understand the technology

---

**Created for INFOTHON 5.0** - Aurora Shield DDoS Protection System