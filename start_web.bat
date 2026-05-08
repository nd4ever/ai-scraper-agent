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
echo Refreshing output.json and starting web servers...
echo Open http://127.0.0.1:8000 for the main dashboard.
echo Open http://127.0.0.1:8001 for the PDF report.
echo Press Ctrl+C in these windows to stop the servers.
echo.
start "Web Dashboard" "%PYTHON_EXE%" serve_web.py --port 8000
start "PDF Report" "%PYTHON_EXE%" serve_pdf.py --port 8001

if errorlevel 1 (
  echo.
  echo Launch failed. See messages above.
  pause
)

endlocal
