@echo off
REM Aurora Shield Docker Demo Setup Script for Windows
REM INFOTHON 5.0 - Complete Local Environment

echo 🛡️  Aurora Shield - INFOTHON 5.0 Docker Demo Setup
echo ==================================================

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

REM Stop any existing containers
echo 🧹 Stopping any existing containers...
docker-compose down -v

REM Build the Aurora Shield image
echo 🔨 Building Aurora Shield Docker image...
docker-compose build

REM Start the complete environment
echo 🚀 Starting Aurora Shield Demo Environment...
docker-compose up -d

REM Wait for services to be ready
echo ⏳ Waiting for services to start...
timeout /t 30 /nobreak

echo.
echo 🎉 Aurora Shield Demo Environment is ready!
echo.
echo 📊 Access Points:
echo    Aurora Shield Dashboard: http://localhost:8080
echo    Login: admin/admin123 or user/user123
echo.
echo    Protected Web App: http://localhost:80
echo    Load Balancer: http://localhost:8090
echo.
echo 📈 Monitoring:
echo    Kibana (Logs): http://localhost:5601
echo    Grafana (Metrics): http://localhost:3000 (admin/admin)
echo    Prometheus: http://localhost:9090
echo.
echo 🚨 To start attack simulation:
echo    docker-compose run --rm attack-simulator
echo.
echo 🛑 To stop everything:
echo    docker-compose down
echo.
echo 📋 To view logs:
echo    docker-compose logs -f aurora-shield
echo.
pause