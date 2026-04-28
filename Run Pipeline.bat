@echo off
setlocal
cd /d "%~dp0"
set "PY=C:\Users\prath\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
set "PY_READY=0"
if exist "%PY%" set "PY_READY=1"
if not exist "%PY%" (
  where python >nul 2>nul
  if not errorlevel 1 (
    set "PY=python"
    set "PY_READY=1"
  )
)

echo.
echo AI Job Application Assistant - Live Pipeline
echo ===========================================
echo.
echo This will fetch configured ATS jobs, score them, and write daily_queue files.
echo.

if "%PY_READY%"=="0" (
  echo Bundled Python was not found:
  echo %PY%
echo.
echo Install Python or edit this file and set PY to your Python path.
  pause
  exit /b 1
)

echo [1/3] Running live ingest...
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
