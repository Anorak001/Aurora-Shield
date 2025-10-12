#!/bin/bash
# Aurora Shield Optimized Docker Setup Script
# Virtual IP Attack Orchestrator with Streamlined Architecture

echo "🛡️  Aurora Shield - Optimized Multi-Vector Protection Platform"
echo "============================================================="

# Change to the root directory where docker-compose.yml is located
cd "$(dirname "$0")/.."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Download from: https://www.docker.com/get-started"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"

# Create logs directory
mkdir -p logs

# Ensure the external network exists for docker-compose
echo "🔗 Checking for required external network 'aurora-net'..."
if ! docker network inspect aurora-net > /dev/null 2>&1; then
    echo "Creating external network 'aurora-net'..."
    docker network create --driver bridge aurora-net || {
        echo "❌ Failed to create 'aurora-net'. Please check Docker network settings."
        exit 1
    }
    echo "✅ External network 'aurora-net' created successfully"
else
    echo "✅ External network 'aurora-net' already exists"
fi

# Stop any existing containers
echo "🧹 Stopping any existing containers..."
docker-compose down --remove-orphans > /dev/null 2>&1

echo "✅ Environment cleaned. Setting up optimized architecture..."

# Build the Aurora Shield images
echo "🔨 Building Aurora Shield Docker images..."
docker-compose build --pull
if [ $? -ne 0 ]; then
    echo "❌ Failed to build Docker images. Please check the build logs above."
    exit 1
fi

# Start the streamlined environment
echo "🚀 Starting Aurora Shield Optimized Environment..."
docker-compose up -d --remove-orphans
if [ $? -ne 0 ]; then
    echo "❌ Failed to start services. Please check the logs above."
    exit 1
fi

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
echo "Press Ctrl+C to skip waiting..."
sleep 15 &
wait $!

# Enhanced verification
echo
echo "🔎 Verifying streamlined services..."
echo "-- Running containers:"
docker-compose ps

echo
echo "🧪 Testing core services..."
echo "Testing Aurora Shield Dashboard (port 8080)..."
curl -s -o /dev/null -w "Aurora Shield: %{http_code}\n" http://localhost:8080 || echo "Aurora Shield: Not ready"

echo "Testing Attack Orchestrator (port 5000)..."
curl -s -o /dev/null -w "Attack Orchestrator: %{http_code}\n" http://localhost:5000 || echo "Attack Orchestrator: Not ready"

echo "Testing Load Balancer (port 8090)..."
curl -s -o /dev/null -w "Load Balancer: %{http_code}\n" http://localhost:8090 || echo "Load Balancer: Not ready"

echo "Testing Demo Application Primary (port 80)..."
curl -s -o /dev/null -w "Demo App Primary: %{http_code}\n" http://localhost:80 || echo "Demo App Primary: Not ready"

echo "Testing Demo Application CDN2 (port 8081)..."
curl -s -o /dev/null -w "Demo App CDN2: %{http_code}\n" http://localhost:8081 || echo "Demo App CDN2: Not ready"

echo "Testing Demo Application CDN3 (port 8082)..."
curl -s -o /dev/null -w "Demo App CDN3: %{http_code}\n" http://localhost:8082 || echo "Demo App CDN3: Not ready"

echo
echo "✅ Setup complete! Optimized architecture deployed."
echo
echo "🎉 Aurora Shield Optimized Environment is ready!"
echo
echo "📊 Main Access Points:"
echo "   🛡️  Aurora Shield Dashboard: http://localhost:8080"
echo "   �️  DDoS protection and sinkhole management"
echo "   📊  Real-time attack monitoring and mitigation"
echo "   🔐  Login: admin/admin123 or user/user123"
echo
echo "⚔️  Virtual Attack Orchestrator (NEW):"
echo "   🌐  Attack Orchestrator Dashboard: http://localhost:5000"
echo "   🤖  Create virtual bots across different subnets"
echo "   �  Simulate multi-vector DDoS attacks"
echo "   🪶  No real container spawning - lightweight virtual IPs"
echo "   🎮  Individual bot control and configuration"
echo "   📊  Real-time attack statistics and monitoring"
echo
echo "🌐 Demo Application & Load Balancer:"
echo "   📡  Demo Application Primary: http://localhost:80"
echo "   📡  Demo Application CDN2: http://localhost:8081"
echo "   📡  Demo Application CDN3: http://localhost:8082"
echo "   ⚖️  Load Balancer Control: http://localhost:8090"
echo "   🔄  Traffic routing and load distribution"
echo "   💓  Service health monitoring"
echo
echo "✨ Key Features:"
echo "   🌍  Virtual IP Generation: Algorithm creates IPs across 8+ subnet ranges"
echo "   �️  Sinkhole Integration: All virtual attacks feed into Aurora Shield"
echo "   🪶  Lightweight Architecture: 4 services instead of 12"
echo "   📊  Real-time Monitoring: Live attack statistics and bot management"
echo "   🌐  Multi-subnet Attacks: Distributed attack simulation"
echo
echo "🧪 Testing Commands:"
echo "   Test Aurora Shield: curl http://localhost:8080/health"
echo "   Test Attack Orchestrator: curl http://localhost:5000/health"
echo "   Test Load Balancer: curl http://localhost:8090/"
echo "   Test Demo App Primary: curl http://localhost:80/"
echo "   Test Demo App CDN2: curl http://localhost:8081/"
echo "   Test Demo App CDN3: curl http://localhost:8082/"
echo
echo "🤖 Virtual Bot Management (API):"
echo "   Create HTTP Flood Bot:"
echo "     curl -X POST http://localhost:5000/api/bots \\"
echo "          -H \"Content-Type: application/json\" \\"
echo "          -d '{\"attack_type\":\"http_flood\",\"target\":\"http://localhost:8080\"}'"
echo
echo "   Create DDoS Burst Bot:"
echo "     curl -X POST http://localhost:5000/api/bots \\"
echo "          -H \"Content-Type: application/json\" \\"
echo "          -d '{\"attack_type\":\"ddos_burst\",\"target\":\"http://localhost:8080\"}'"
echo
echo "   View Bot Statistics: curl http://localhost:5000/api/bots/stats"
echo "   Stop All Bots: curl -X DELETE http://localhost:5000/api/bots/stop-all"
echo
echo "🛑 Management Commands:"
echo "   Stop everything: docker-compose down"
echo "   View logs: docker-compose logs -f [service-name]"
echo "   Services: aurora-shield, attack-orchestrator, load-balancer, demo-app, demo-app-cdn2, demo-app-cdn3"