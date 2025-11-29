# 🎉 Aurora Shield Attack Simulator - Web Interface Created!

## ✅ **What's New**

### **🌐 Web-Based Attack Simulator**
- **URL 1**: http://localhost:5001 (Primary Simulator)
- **URL 2**: http://localhost:5002 (Secondary Simulator)
- **URL 3**: http://localhost:5003 (Tertiary Simulator)
- **Always Running**: Multiple client containers now run continuously with web interfaces
- **Interactive Configuration**: Set attack parameters through beautiful web UIs
- **Real-Time Monitoring**: Live statistics and attack progress tracking across all instances

### **⚔️ Attack Types Available**

#### **1. HTTP Flood Attack** 🚨
- **Purpose**: High-volume HTTP requests to overwhelm target
- **Configuration**:
  - Requests per second (1-1000)
  - Duration (5-300 seconds)
  - Target selection (Aurora Shield direct or Load Balancer)
- **Use Case**: Test rate limiting and connection handling

#### **2. Slowloris Attack** 🐌
- **Purpose**: Connection exhaustion using slow, partial requests
- **Configuration**:
  - Concurrent connections (1-100)
  - Duration (10-300 seconds)
  - Target selection
- **Use Case**: Test connection timeout handling

#### **3. Normal Traffic Simulation** 🌐
- **Purpose**: Legitimate user traffic baseline
- **Configuration**:
  - Requests per second (1-20)
  - Duration (30-600 seconds)
  - Target selection
- **Use Case**: Establish normal traffic patterns

### **🎯 Target Selection**
- **Aurora Shield (Direct)**: Bypass load balancer, hit Aurora Shield directly
- **Load Balancer (Intercepted)**: Send through load balancer → Aurora Shield intercepts and processes

### **📊 Real-Time Statistics**
- Total requests sent
- Successful requests
- Blocked requests (detected by Aurora Shield)
- Failed requests
- Current request rate
- Active attack count

## 🚀 **How to Use**

### **1. Start Aurora Shield Environment**
```powershell
.\docker\setup.bat
```

### **2. Access Attack Simulators**
- Open browser to: **http://localhost:5001** (Primary Simulator)
- Open browser to: **http://localhost:5002** (Secondary Simulator)
- Open browser to: **http://localhost:5003** (Tertiary Simulator)
- Select attack type and configure parameters on each instance
- Choose target (direct to Aurora Shield or through Load Balancer)
- Click launch to start attacks from multiple simulators
- Monitor real-time statistics across all instances

### **3. Key Features**
- **⏹️ Stop Controls**: Stop individual attacks or all attacks
- **🔄 Reset Stats**: Clear statistics to start fresh
- **📊 Live Updates**: Statistics refresh every 2 seconds
- **🎨 Visual Feedback**: Attack cards pulse during active attacks

## 🔧 **Technical Details**

### **Container Changes**
- **Client Containers**: Now run Flask web servers on ports 5001, 5002, and 5003
- **Always Running**: `restart: unless-stopped` policy
- **Dependencies**: Added Flask to requirements

### **Architecture Flow**
```
Attack Simulators (Ports 5001, 5002, 5003) 
    ↓ (Configure attacks)
Client Containers 
    ↓ (Send requests to...)
Target Options:
    → Aurora Shield Direct (Port 8080)
    → Load Balancer (Port 8090) → Aurora Shield (intercepts)
```

### **Service Integration**
- **Service Dashboard**: http://localhost:5000 (includes attack simulator monitoring)
- **Aurora Shield**: http://localhost:8080 (main protection dashboard)
- **Load Balancer**: http://localhost:8090 (entry point for intercepted traffic)

## 📋 **All Services Running**

| Service | Port | Purpose |
|---------|------|---------|
| **Aurora Shield** | 8080 | Main DDoS protection |
| **Attack Simulator 1** | 5001 | **NEW** Web-based attack configuration |
| **Attack Simulator 2** | 5002 | **NEW** Web-based attack configuration |
| **Attack Simulator 3** | 5003 | **NEW** Web-based attack configuration |
| **Service Dashboard** | 5000 | Service management |
| **Protected Web App** | 80 | Demo application |
| **Load Balancer** | 8090 | Traffic routing |
| **Kibana** | 5601 | Log visualization |
| **Grafana** | 3000 | Metrics dashboard |
| **Prometheus** | 9090 | Metrics collection |
| **Elasticsearch** | 9200 | Log storage |
| **Redis** | 6379 | Caching |

## 🎯 **Attack Testing Scenarios**

### **Scenario 1: Direct Aurora Shield Testing**
1. Configure HTTP Flood: 100 req/s for 30 seconds
2. Target: "Aurora Shield (Direct)"
3. Monitor how Aurora Shield detects and blocks the attack
4. Check Aurora Shield dashboard for protection metrics

### **Scenario 2: Load Balancer Interception**
1. Configure Normal Traffic: 5 req/s for 60 seconds
2. Target: "Load Balancer (Intercepted)"
3. Observe how traffic flows through load balancer to Aurora Shield
4. Compare blocked vs. successful requests

### **Scenario 3: Mixed Attack Patterns**
1. Start Normal Traffic (background baseline)
2. Launch HTTP Flood attack
3. Add Slowloris attack
4. Monitor how Aurora Shield handles multiple attack types

## ✨ **Benefits**

1. **Easy Configuration**: No command-line parameters needed
2. **Visual Feedback**: See attacks in progress with real-time stats
3. **Target Flexibility**: Test both direct and intercepted traffic flows
4. **Educational**: Perfect for demonstrating Aurora Shield's capabilities
5. **Integrated**: Works seamlessly with existing monitoring stack

Your Aurora Shield environment now has a powerful, user-friendly attack simulation interface! 🛡️⚔️