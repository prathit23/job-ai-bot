@echo off
setlocal
cd /d "%~dp0"
set "PY=C:\Users\prath\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

echo.
echo AI Job Application Assistant - Dashboard
echo =======================================
echo.

if not exist "%PY%" (
  echo Bundled Python was not found:
  echo %PY%
  echo.
  echo Edit this file and set PY to your Python path.
  pause
  exit /b 1
)

echo Starting dashboard at http://127.0.0.1:8765
echo Keep this window open while using the dashboard.
echo.
start "" "http://127.0.0.1:8765"
"%PY%" -m jobbot serve
pause
