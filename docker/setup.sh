#!/bin/bash
# Aurora Shield Docker Demo Setup Script
# INFOTHON 5.0 - Complete Local Environment

echo "🛡️  Aurora Shield - INFOTHON 5.0 Docker Demo Setup"
echo "=================================================="

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

# Stop any existing containers
echo "🧹 Stopping any existing containers..."
docker-compose down -v

# Build the Aurora Shield image
echo "🔨 Building Aurora Shield Docker image..."
docker-compose build

# Start the complete environment
echo "🚀 Starting Aurora Shield Demo Environment..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Check service health
echo "🔍 Checking service health..."

services=(
    "http://localhost:8080:Aurora Shield Dashboard"
    "http://localhost:80:Protected Web Application"
    "http://localhost:8090:Load Balancer"
    "http://localhost:5601:Kibana"
    "http://localhost:3000:Grafana (admin/admin)"
    "http://localhost:9090:Prometheus"
)

for service in "${services[@]}"; do
    url=$(echo $service | cut -d: -f1-2)
    name=$(echo $service | cut -d: -f3-)
    
    if curl -s -f "$url" > /dev/null; then
        echo "✅ $name: $url"
    else
        echo "⚠️  $name: $url (still starting...)"
    fi
done

echo ""
echo "🎉 Aurora Shield Demo Environment is ready!"
echo ""
echo "📊 Access Points:"
echo "   Aurora Shield Dashboard: http://localhost:8080"
echo "   Login: admin/admin123 or user/user123"
echo ""
echo "   Protected Web App: http://localhost:80"
echo "   Load Balancer: http://localhost:8090"
echo ""
echo "📈 Monitoring:"
echo "   Kibana (Logs): http://localhost:5601"
echo "   Grafana (Metrics): http://localhost:3000 (admin/admin)"
echo "   Prometheus: http://localhost:9090"
echo ""
echo "🚨 To start attack simulation:"
echo "   docker-compose run --rm attack-simulator"
echo ""
echo "🛑 To stop everything:"
echo "   docker-compose down"
echo ""
echo "📋 To view logs:"
echo "   docker-compose logs -f aurora-shield"