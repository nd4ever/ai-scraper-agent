@echo off
setlocal

set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python312\python.exe"
if not exist "%PYTHON_EXE%" (
  echo Python 3.12 was not found at:
  echo %PYTHON_EXE%
  echo.
  echo Install Python or update this script path, then try again.
  pause
  exit /b 1
)

cd /d "%~dp0"
echo Refreshing output.json and starting unified web server...
echo Open http://127.0.0.1:8000 for the dashboard.
echo Use the tabs to switch between Dashboard and Weekly Report views.
echo Press Ctrl+C in this window to stop the server.
echo.
start "Azure Headlines Dashboard" "%PYTHON_EXE%" serve_unified.py --port 8000

if errorlevel 1 (
  echo.
  echo Launch failed. See messages above.
  pause
)

endlocal
