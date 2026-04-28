@echo off
setlocal
cd /d "%~dp0"
set "PY=C:\Users\prath\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

echo.
echo AI Job Application Assistant - Live Pipeline
echo ===========================================
echo.
echo This will fetch configured ATS jobs, score them, and write daily_queue files.
echo.

if not exist "%PY%" (
  echo Bundled Python was not found:
  echo %PY%
  echo.
  echo Edit this file and set PY to your Python path.
  pause
  exit /b 1
)

echo [1/2] Running live ingest...
"%PY%" -m jobbot ingest
if errorlevel 1 (
  echo.
  echo Live ingest failed. Check the error above.
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
