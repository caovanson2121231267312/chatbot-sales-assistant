@echo off
echo ========================================
echo   E-Commerce Chatbot Launcher
echo ========================================
echo.

echo Checking Python installation...
python --version
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo.
echo Starting Action Server...
start "Action Server" cmd /k "rasa run actions"

timeout /t 5 /nobreak > nul

echo.
echo Starting Rasa Server...
start "Rasa Server" cmd /k "rasa run --enable-api --cors *"

echo.
echo ========================================
echo   Servers are starting...
echo ========================================
echo.
echo Action Server: http://localhost:5055
echo Rasa Server: http://localhost:5005
echo.
echo Open rasa-webchat/index.html in your browser
echo.
echo Press any key to exit...
pause > nul
