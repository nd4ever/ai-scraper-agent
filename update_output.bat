@echo off
setlocal

set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python312\python.exe"
if not exist "%PYTHON_EXE%" (
  echo Python 3.12 was not found at:
  echo %PYTHON_EXE%
  exit /b 1
)

cd /d "%~dp0"
"%PYTHON_EXE%" update_output.py --days 7 --out output.json
exit /b %errorlevel%
