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
echo Refreshing output.json and starting web server...
echo Open http://127.0.0.1:8000 after startup.
echo Press Ctrl+C in this window to stop the server.
echo.
"%PYTHON_EXE%" serve_web.py --days 7 --port 8000

if errorlevel 1 (
  echo.
  echo Launch failed. See messages above.
  pause
)

endlocal
