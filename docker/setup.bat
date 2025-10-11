@echo off
REM Aurora Shield Docker Demo Setup Script
REM INFOTHON 5.0 - Multi-CDN Load Balancer Environment

echo 🛡️  Aurora Shield - INFOTHON 5.0 Multi-CDN Demo Setup
echo ======================================================

REM Change to the root directory where docker-compose.yml is located
cd /d "%~dp0\.."

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not installed. Please install Docker Desktop first.
    echo    Download from: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose is not installed. Please install Docker Desktop which includes Docker Compose.
    pause
    exit /b 1
)

echo ✅ Docker and Docker Compose are installed

REM Create logs directory
if not exist "logs" mkdir logs

REM Ensure the external network exists for docker-compose
echo Checking for required external network 'as_aurora-net'...
docker network inspect as_aurora-net >nul 2>&1
if %errorlevel% neq 0 (
    echo Creating external network 'as_aurora-net'...
    docker network create --driver bridge as_aurora-net
    if %errorlevel% neq 0 (
        echo ❌ Failed to create 'as_aurora-net'. Please check Docker network settings.
        pause
        exit /b 1
    )
    echo ✅ External network 'as_aurora-net' created successfully
) else (
    echo ✅ External network 'as_aurora-net' already exists
)

REM Stop any existing containers
echo 🧹 Stopping any existing containers...
docker-compose stop
docker-compose rm -f

echo ✅ Containers stopped and removed. Recreating environment now...

REM Build the Aurora Shield image
echo 🔨 Building Aurora Shield Docker image (pulling newer base images when available)...
docker-compose build --pull

REM Start the complete environment
echo 🚀 Starting Aurora Shield Demo Environment...
docker-compose up -d --remove-orphans

REM Wait for services to be ready
echo ⏳ Waiting 30 seconds for services to start...
timeout /t 30 /nobreak >nul

REM Enhanced verification
echo.
echo 🔎 Verifying services...
echo -- Running containers:
docker-compose ps

echo.
echo 🧪 Testing CDN services...
echo Testing CDN Primary (port 80)...
curl -s -o nul -w "Primary CDN: %%{http_code}" http://localhost:80 2>nul || echo Primary CDN: Not ready

echo Testing CDN Secondary (port 8081)...
curl -s -o nul -w "Secondary CDN: %%{http_code}" http://localhost:8081 2>nul || echo Secondary CDN: Not ready

echo Testing CDN Tertiary (port 8082)...
curl -s -o nul -w "Tertiary CDN: %%{http_code}" http://localhost:8082 2>nul || echo Tertiary CDN: Not ready

echo Testing Load Balancer UI (port 8090)...
curl -s -o nul -w "Load Balancer UI: %%{http_code}" http://localhost:8090 2>nul || echo Load Balancer UI: Not ready

echo Testing Attack Simulator 1 (port 5001)...
curl -s -o nul -w "Attack Simulator 1: %%{http_code}" http://localhost:5001 2>nul || echo Attack Simulator 1: Not ready

echo Testing Attack Simulator 2 (port 5002)...
curl -s -o nul -w "Attack Simulator 2: %%{http_code}" http://localhost:5002 2>nul || echo Attack Simulator 2: Not ready

echo Testing Attack Simulator 3 (port 5003)...
curl -s -o nul -w "Attack Simulator 3: %%{http_code}" http://localhost:5003 2>nul || echo Attack Simulator 3: Not ready

echo.
echo ✅ Setup complete! All services have been started.
echo.
echo 🎉 Aurora Shield Demo Environment is ready!
echo.
echo 📊 Main Access Points:
echo    🛡️  Aurora Shield Dashboard: http://localhost:8080
echo    🌐  Service Management Dashboard: http://localhost:5000
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
echo ⚔️  Attack Simulation (Independent Multi-Vector Testing):
echo    🌐  Attack Simulator Web Interface 1: http://localhost:5001
echo    🌐  Attack Simulator Web Interface 2: http://localhost:5002
echo    🌐  Attack Simulator Web Interface 3: http://localhost:5003
echo    💥  Configure attacks, set request rates, target selection
echo    📊  Real-time attack statistics and monitoring
echo    🎯  Each simulator can target different CDNs independently
echo    ⚔️  Support for concurrent multi-vector attack scenarios
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
echo    Check CDN health: curl http://localhost:8081/health or http://localhost:8082/health
echo.
echo ⚔️  Attack Simulator Testing Commands:
echo    Test Attack Simulator 1: curl http://localhost:5001/
echo    Test Attack Simulator 2: curl http://localhost:5002/
echo    Test Attack Simulator 3: curl http://localhost:5003/
echo    View Attack Stats: Check /stats endpoint on each simulator
echo.
echo 🛑 Management Commands:
echo    Stop everything: docker-compose down
echo    Restart CDN services: docker-compose restart demo-webapp demo-webapp-cdn2 demo-webapp-cdn3
echo    Restart load balancer: docker-compose restart load-balancer
echo    Restart attack simulators: docker-compose restart client client-2 client-3
echo    View logs: docker-compose logs -f [service-name]
echo    View attack logs: docker-compose logs -f client client-2 client-3
echo    Service dashboard: Access at http://localhost:5000
echo.
pause