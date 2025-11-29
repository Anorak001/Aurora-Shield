#!/bin/bash

echo "🚀 Building Aurora Shield Attack Orchestrator System"

# Build bot agent image
echo "📦 Building bot agent image..."
cd docker
docker build -f Dockerfile.bot-agent -t aurora-shield-bot-agent .

# Build orchestrator image  
echo "📦 Building orchestrator image..."
docker build -f Dockerfile.orchestrator -t aurora-shield-orchestrator .

# Return to root
cd ..

# Update docker-compose with orchestrator
echo "🔧 Updating docker-compose configuration..."

# Start the orchestrator
echo "🎯 Starting attack orchestrator..."
docker-compose up -d attack-orchestrator

echo "✅ Attack Orchestrator System Ready!"
echo ""
echo "🎯 Attack Orchestrator Dashboard: http://localhost:5000"
echo "📊 Load Balancer Dashboard: http://localhost:8090"
echo "🛡️ Aurora Shield Dashboard: http://localhost:8080"
echo ""
echo "Demo Commands:"
echo "1. Access orchestrator: http://localhost:5000"
echo "2. Spawn 10 bots"
echo "3. Launch coordinated attack (30s duration, 2 rps per bot)"
echo "4. Monitor real-time blocking in Aurora Shield dashboard"
echo "5. Check load balancer stats for failover behavior"
echo ""
echo "Advanced Testing:"
echo "curl -X POST http://localhost:5000/api/fleet/spawn -H 'Content-Type: application/json' -d '{\"count\": 20, \"attack_type\": \"http_flood\"}'"
echo "curl -X POST http://localhost:5000/api/fleet/attack -H 'Content-Type: application/json' -d '{\"duration\": 60, \"rate_per_bot\": 3.0}'"