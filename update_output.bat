@echo off
setlocal

set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python312\python.exe"
if not exist "%PYTHON_EXE%" (
  echo Python 3.12 was not found at:
  echo %PYTHON_EXE%
  exit /b 1
)

cd /d "%~dp0"
rem update_output.py always pulls the most recently completed Monday-Sunday week.
"%PYTHON_EXE%" update_output.py --out output.json
exit /b %errorlevel%
