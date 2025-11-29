#!/bin/bash

# Aurora Shield Service Dashboard Launcher

echo "🛡️ Starting Aurora Shield Service Dashboard..."
echo ""
echo "This will start the Aurora Shield main dashboard at http://localhost:5000"
echo "You can monitor and manage all Aurora Shield services from there."
echo ""
echo "✨ New Features in Optimized Version:"
echo "   - Sinkhole/Blackhole protection integrated"
echo "   - Virtual Attack Orchestrator with multi-subnet bots"
echo "   - Streamlined 4-service architecture"
echo "   - Real-time attack monitoring and mitigation"
echo ""
echo "Press Ctrl+C to stop the dashboard"
echo ""

cd "$(dirname "$0")"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH."
    echo "Please install Python 3.7+ and try again."
    exit 1
fi

# Install required packages if needed
echo "Installing required Python packages..."
pip3 install flask docker requests > /dev/null 2>&1

# Start the dashboard
echo ""
echo "🚀 Starting Service Dashboard..."
echo "Open your browser to: http://localhost:5000"
echo ""
echo "Additional Access Points:"
echo "   Aurora Shield Dashboard: http://localhost:8080"
echo "   Virtual Attack Orchestrator: http://localhost:5000 (if running via Docker)"
echo ""
python3 service_dashboard.py