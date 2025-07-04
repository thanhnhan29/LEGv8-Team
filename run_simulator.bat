@echo off
echo ====================================
echo LEGv8 Simulator Setup and Run Script
echo ====================================

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed. Installing Python 3.9...
    
    :: Download Python 3.9 installer
    echo Downloading Python 3.9 installer...
    curl -o python-3.9.exe https://www.python.org/ftp/python/3.9.13/python-3.9.13-amd64.exe
    
    :: Install Python silently
    echo Installing Python 3.9...
    python-3.9.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    
    :: Clean up installer
    del python-3.9.exe
    
    :: Refresh PATH
    echo Please restart your command prompt and run this script again.
    pause
    exit /b
) else (
    echo Python is already installed.
    python --version
)

:: Check if pip is available
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Pip is not available. Installing pip...
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    python get-pip.py
    del get-pip.py
)

:: Create requirements.txt if it doesn't exist
if not exist requirements.txt (
    echo Creating requirements.txt...
    echo Flask==2.3.3> requirements.txt
    echo flask-cors==4.0.0>> requirements.txt
)

:: Install dependencies
echo Installing Python dependencies...
pip install -r requirements.txt

:: Check if installation was successful
if %errorlevel% neq 0 (
    echo Error: Failed to install dependencies.
    pause
    exit /b 1
)

:: Start the simulator
echo.
echo ====================================
echo Starting LEGv8 Simulator...
echo ====================================
echo.
echo The simulator will be available at: http://localhost:5010
echo Press Ctrl+C to stop the simulator
echo.

python app.py

pause