@echo off
REM Aurora Shield Docker Demo Setup Script for Windows
REM INFOTHON 5.0 - Multi-CDN Load Balancer Environment

echo 🛡️  Aurora Shield - INFOTHON 5.0 Multi-CDN Demo Setup
echo ======================================================

setlocal EnableDelayedExpansion

REM Change to the root directory where docker-compose.yml is located
cd /d "%~dp0.."

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not installed. Please install Docker Desktop first.
    echo    Download from: https://www.docker.com/get-started
    pause
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose is not installed. Please install Docker Compose first.
    pause
    exit /b 1
)

echo ✅ Docker and Docker Compose are installed

REM Create logs directory
if not exist logs mkdir logs

REM Ensure the external network exists for docker-compose
echo Checking for required external network 'as_aurora-net'...
docker network inspect as_aurora-net >nul 2>&1
if %errorlevel% neq 0 (
    echo Creating external network 'as_aurora-net'...
    docker network create --driver bridge as_aurora-net >nul 2>&1
    if %errorlevel% neq 0 (
        echo ❌ Failed to create 'as_aurora-net'. Please check Docker network settings.
        pause
        exit /b 1
    )
    echo ✅ External network 'as_aurora-net' created successfully
) else (
    echo ✅ External network 'as_aurora-net' already exists
)

REM Stop and remove any existing containers (images will NOT be deleted)
echo 🧹 Stopping running containers (will stop and remove containers, not images)...
docker-compose stop
docker-compose rm -f

echo ✅ Containers stopped and removed. Recreating environment now...

REM Build the Aurora Shield image
echo 🔨 Building Aurora Shield Docker image (pulling newer base images when available)...
docker-compose build --pull

REM Start the complete environment
echo 🚀 Starting Aurora Shield Demo Environment...
docker-compose up -d --remove-orphans

REM Wait for services to be ready with skip option
echo ⏳ Waiting 30 seconds for services to start...
echo Press any key to skip waiting...
timeout /t 30

REM Enhanced verification
echo.
echo 🔎 Verifying services...
echo -- Running containers:
docker-compose ps

echo.
echo 🧪 Testing CDN services...
echo Testing CDN Primary (port 80)...
curl -s -o NUL -w "Primary CDN: %%{http_code}" http://localhost:80 2>NUL || echo Primary CDN: Not ready
echo.

echo Testing CDN Secondary (port 8081)...
curl -s -o NUL -w "Secondary CDN: %%{http_code}" http://localhost:8081 2>NUL || echo Secondary CDN: Not ready
echo.

echo Testing CDN Tertiary (port 8082)...
curl -s -o NUL -w "Tertiary CDN: %%{http_code}" http://localhost:8082 2>NUL || echo Tertiary CDN: Not ready
echo.

echo Testing Load Balancer UI (port 8090)...
curl -s -o NUL -w "Load Balancer UI: %%{http_code}" http://localhost:8090 2>NUL || echo Load Balancer UI: Not ready
echo.

echo.
echo ✅ Setup complete! All services have been started.

echo.
echo 🎉 Aurora Shield Demo Environment is ready!
echo.
echo 📊 Main Access Points:
echo    🛡️  Aurora Shield Dashboard: http://localhost:8080
echo    🌐  Service Management Dashboard: python service_dashboard.py (then http://localhost:5000)
echo    🔐  Login: admin/admin123 or user/user123
echo.
echo 🌐 CDN Services (Content Delivery Network):
echo    📡  CDN Primary (demo-webapp): http://localhost:80
echo    📡  CDN Secondary (demo-webapp-cdn2): http://localhost:8081
echo    📡  CDN Tertiary (demo-webapp-cdn3): http://localhost:8082
echo.
echo ⚖️  Load Balancer Control Panel: http://localhost:8090
echo    🎛️  Manage CDN restart and migration operations
echo    🔀  Traffic routing: http://localhost:8090/cdn/ (load balanced)
echo    🎯  Direct routing: /cdn/primary/, /cdn/secondary/, /cdn/tertiary/
echo.
echo 📈 Monitoring Stack:
echo    📊  Kibana (Logs): http://localhost:5601
echo    📈  Grafana (Metrics): http://localhost:3000 (admin/admin)
echo    🎯  Prometheus: http://localhost:9090
echo.
echo ⚔️  Attack Simulation:
echo    🌐  Attack Simulator Web Interface: http://localhost:5001
echo    💥  Configure attacks, set request rates, target selection
echo    📊  Real-time attack statistics and monitoring
echo.
echo 🎛️  Load Balancer Features:
echo    🔄  CDN Restart: Select and restart individual CDN services
echo    🔀  CDN Migration: Migrate traffic between CDN services
echo    ⚖️  Load Distribution: Weighted routing (Primary:3, Secondary:2, Tertiary:1)
echo    📊  Service Status: Monitor CDN health and availability
echo.
echo 🧪 CDN Testing Commands:
echo    Test load balancer UI: curl http://localhost:8090/
echo    Test load balanced CDNs: curl http://localhost:8090/cdn/
echo    Test primary CDN: curl http://localhost:8090/cdn/primary/
echo    Test secondary CDN: curl http://localhost:8090/cdn/secondary/
echo    Test tertiary CDN: curl http://localhost:8090/cdn/tertiary/
echo    Check CDN health: curl http://localhost:8081/health and curl http://localhost:8082/health
echo.
echo 🛑 Management Commands:
echo    Stop everything: docker-compose down
echo    Restart CDN services: docker-compose restart demo-webapp demo-webapp-cdn2 demo-webapp-cdn3
echo    Restart load balancer: docker-compose restart load-balancer
echo    View logs: docker-compose logs -f [service-name]
echo    Service dashboard: python service_dashboard.py
echo.
pause