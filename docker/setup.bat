@echo off
REM Aurora Shield Optimized Docker Setup Script
REM Virtual IP Attack Orchestrator with Streamlined Architecture

echo [Aurora Shield] - Optimized Multi-Vector Protection Platform
echo ============================================================

REM Change to the root directory where docker-compose.yml is located
cd /d "%~dp0\.."

REM Verify we're in the correct directory
if not exist "docker-compose.yml" (
    echo [ERROR] docker-compose.yml not found in current directory.
    echo    Current directory: %CD%
    echo    Please ensure you're running this script from the correct location.
    pause
    exit /b 1
)

echo [OK] Found docker-compose.yml in: %CD%

REM Check if Docker is installed and running
echo [INFO] Checking Docker installation...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed or not accessible.
    echo    Please install Docker Desktop and ensure it's running.
    echo    Download from: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

REM Check if Docker daemon is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker daemon is not running.
    echo    Please start Docker Desktop and try again.
    pause
    exit /b 1
)

REM Check if Docker Compose is installed
echo [INFO] Checking Docker Compose installation...
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker Compose is not installed.
    echo    Please install Docker Desktop which includes Docker Compose.
    pause
    exit /b 1
)

echo [OK] Docker and Docker Compose are ready

REM Create logs directory
if not exist "logs" mkdir logs

REM Ensure the external network exists for docker-compose
echo [INFO] Checking for required external network 'aurora-net'...
docker network inspect aurora-net >nul 2>&1
if %errorlevel% neq 0 (
    echo Creating external network 'aurora-net'...
    docker network create --driver bridge aurora-net >nul 2>&1
    REM Check if creation was successful or if network already exists
    docker network inspect aurora-net >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create or find 'aurora-net'. Please check Docker network settings.
        pause
        exit /b 1
    )
    echo [OK] External network 'aurora-net' created successfully
) else (
    echo [OK] External network 'aurora-net' already exists
)

REM Stop any existing containers
echo [INFO] Stopping any existing containers...
docker-compose down --remove-orphans >nul 2>&1

echo [OK] Environment cleaned. Setting up optimized architecture...

REM Build the Aurora Shield images
echo [INFO] Building Aurora Shield Docker images...
docker-compose build --pull
if %errorlevel% neq 0 (
    echo [ERROR] Failed to build Docker images. Please check the build logs above.
    pause
    exit /b 1
)

REM Start the streamlined environment
echo [INFO] Starting Aurora Shield Optimized Environment...
docker-compose up -d --remove-orphans
if %errorlevel% neq 0 (
    echo [ERROR] Failed to start services. Please check the logs above.
    pause
    exit /b 1
)

REM Wait for services to be ready
echo [INFO] Waiting for services to start...
timeout /t 10 /nobreak >nul

echo.
echo [OK] Setup complete! All services have been started.
echo.
echo [SUCCESS] Aurora Shield Optimized Environment is ready!
echo.
echo === Main Access Points ===
echo    Aurora Shield Dashboard: http://localhost:8080
echo    - Comprehensive DDoS protection dashboard
echo    - Sinkhole/Blackhole management
echo    - Real-time attack monitoring
echo    Login: admin/admin123 or user/user123
echo.
echo === Virtual Attack Orchestrator (NEW) ===
echo    Attack Orchestrator Dashboard: http://localhost:5000
echo    - Create virtual bots across different subnets
echo    - Simulate multi-vector DDoS attacks
echo    - No real container spawning - lightweight virtual IPs
echo    - Individual bot control and configuration
echo    - Real-time attack statistics and monitoring
echo.
echo === CDN Services (Load Balanced) ===
echo    Demo Application Primary: http://localhost:80
echo    Demo Application CDN2: http://localhost:8081
echo    Demo Application CDN3: http://localhost:8082
echo    Load Balancer Control: http://localhost:8090
echo    - Traffic routing and load distribution
echo    - Service health monitoring
echo    - CDN restart and migration operations
echo.
echo === Key Features ===
echo    Virtual IP Generation: Algorithm creates IPs across 8+ subnet ranges
echo    Sinkhole Integration: All virtual attacks feed into Aurora Shield
echo    Lightweight Architecture: 4 services instead of 12
echo    Real-time Monitoring: Live attack statistics and bot management
echo    Multi-subnet Attacks: Distributed attack simulation
echo.
echo === Testing Commands ===
echo    Test Aurora Shield: curl http://localhost:8080/health
echo    Test Attack Orchestrator: curl http://localhost:5000/health
echo    Test Load Balancer: curl http://localhost:8090/
echo    Test Demo App Primary: curl http://localhost:80/
echo    Test Demo App CDN2: curl http://localhost:8081/
echo    Test Demo App CDN3: curl http://localhost:8082/
echo.
echo === Virtual Bot Management (API) ===
echo    Create HTTP Flood Bot: curl -X POST http://localhost:5000/api/bots -H "Content-Type: application/json" -d "{\"attack_type\":\"http_flood\",\"target\":\"http://localhost:8080\"}"
echo    Create DDoS Burst Bot: curl -X POST http://localhost:5000/api/bots -H "Content-Type: application/json" -d "{\"attack_type\":\"ddos_burst\",\"target\":\"http://localhost:8080\"}"
echo    View Bot Statistics: curl http://localhost:5000/api/bots/stats
echo    Stop All Bots: curl -X DELETE http://localhost:5000/api/bots/stop-all
echo.
echo === Management Commands ===
echo    Stop everything: docker-compose down
echo    View logs: docker-compose logs -f [service-name]
echo    Services: aurora-shield, attack-orchestrator, load-balancer, demo-app, demo-app-cdn2, demo-app-cdn3
echo.
pause