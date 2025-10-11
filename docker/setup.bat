@echo off
REM Aurora Shield Docker Demo Setup Script
REM INFOTHON 5.0 - Multi-CDN Load Balancer Environment

echo [Aurora Shield] - INFOTHON 5.0 Multi-CDN Demo Setup
echo ======================================================

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

echo [OK] Environment cleaned. Setting up fresh environment...

REM Build the Aurora Shield image
echo [INFO] Building Aurora Shield Docker images...
docker-compose build --pull
if %errorlevel% neq 0 (
    echo [ERROR] Failed to build Docker images. Please check the build logs above.
    pause
    exit /b 1
)

REM Start the complete environment
echo [INFO] Starting Aurora Shield Demo Environment...
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
echo [SUCCESS] Aurora Shield Demo Environment is ready!
echo.
echo === Main Access Points ===
echo    Aurora Shield Dashboard: http://localhost:8080
echo    Service Management Dashboard: http://localhost:5000
echo    Login: admin/admin123 or user/user123
echo.
echo === CDN Services (Content Delivery Network) ===
echo    CDN Primary (demo-webapp): http://localhost:80
echo    CDN Secondary (demo-webapp-cdn2): http://localhost:8081
echo    CDN Tertiary (demo-webapp-cdn3): http://localhost:8082
echo.
echo === Load Balancer Control Panel ===
echo    URL: http://localhost:8090
echo    Manage CDN restart and migration operations
echo    Traffic routing: http://localhost:8090/cdn/ (load balanced)
echo    Direct routing: /cdn/primary/, /cdn/secondary/, /cdn/tertiary/
echo.
echo === Monitoring Stack ===
echo    Kibana (Logs): http://localhost:5601
echo    Grafana (Metrics): http://localhost:3000 (admin/admin)
echo    Prometheus: http://localhost:9090
echo.
echo === Attack Simulation (Independent Multi-Vector Testing) ===
echo    Attack Simulator Web Interface 1: http://localhost:5001
echo    Attack Simulator Web Interface 2: http://localhost:5002
echo    Attack Simulator Web Interface 3: http://localhost:5003
echo    Configure attacks, set request rates, target selection
echo    Real-time attack statistics and monitoring
echo    Each simulator can target different CDNs independently
echo    Support for concurrent multi-vector attack scenarios
echo.
echo === Load Balancer Features ===
echo    CDN Restart: Select and restart individual CDN services
echo    CDN Migration: Migrate traffic between CDN services
echo    Load Distribution: Weighted routing (Primary:3, Secondary:2, Tertiary:1)
echo    Service Status: Monitor CDN health and availability
echo.
echo === CDN Testing Commands ===
echo    Test load balancer UI: curl http://localhost:8090/
echo    Test load balanced CDNs: curl http://localhost:8090/cdn/
echo.
echo === Management Commands ===
echo    Stop everything: docker-compose down
echo    View logs: docker-compose logs -f [service-name]
echo    Service dashboard: Access at http://localhost:5000
echo.
pause