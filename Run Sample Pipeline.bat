@echo off
setlocal
cd /d "%~dp0"
set "PY=C:\Users\prath\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

echo.
echo AI Job Application Assistant - Sample Pipeline
echo =============================================
echo.
echo This loads sample jobs, scores them, and writes daily_queue files.
echo.

if not exist "%PY%" (
  echo Bundled Python was not found:
  echo %PY%
  echo.
  echo Edit this file and set PY to your Python path.
  pause
  exit /b 1
)

echo [1/2] Loading sample jobs...
"%PY%" -m jobbot seed-sample
if errorlevel 1 (
  echo.
  echo Sample ingest failed. Check the error above.
  pause
  exit /b 1
)

echo.
echo [2/3] Rescoring jobs...
"%PY%" -m jobbot rescore
if errorlevel 1 (
  echo.
  echo Rescoring failed. Check the error above.
  pause
  exit /b 1
)

echo.
echo [3/3] Writing daily review queue...
"%PY%" -m jobbot write-queue
if errorlevel 1 (
  echo.
  echo Queue generation failed. Check the error above.
  pause
  exit /b 1
)

echo.
echo Done. Open the newest files in the daily_queue folder.
echo.
start "" "%~dp0daily_queue"
pause
