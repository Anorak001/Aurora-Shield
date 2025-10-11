@echo off
REM Aurora Shield Service Dashboard Launcher

echo 🌐 Starting Aurora Shield Service Dashboard...
echo.
echo This will start a web dashboard at http://localhost:5000
echo You can monitor and manage all Aurora Shield services from there.
echo.
echo Press Ctrl+C to stop the dashboard
echo.

cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH.
    echo Please install Python 3.7+ and try again.
    pause
    exit /b 1
)

REM Install required packages if needed
echo Installing required Python packages...
pip install flask docker requests >nul 2>&1

REM Start the dashboard
echo.
echo 🚀 Starting Service Dashboard...
echo Open your browser to: http://localhost:5000
echo.
python service_dashboard.py

pause