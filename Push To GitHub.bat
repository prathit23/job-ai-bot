@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

set "GIT_EXE="
where git >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    for /f "delims=" %%G in ('where git') do (
        if not defined GIT_EXE set "GIT_EXE=%%G"
    )
)

if not defined GIT_EXE (
    set "GIT_EXE=%~dp0tools\mingit\cmd\git.exe"
)

if not exist "%GIT_EXE%" (
    echo Git was not found. Installing portable Git into this project...
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "$ErrorActionPreference='Stop';" ^
        "$ProgressPreference='SilentlyContinue';" ^
        "$root=(Resolve-Path '.').Path;" ^
        "$tools=Join-Path $root 'tools';" ^
        "$zip=Join-Path $tools 'MinGit-2.54.0-64-bit.zip';" ^
        "$dest=Join-Path $tools 'mingit';" ^
        "New-Item -ItemType Directory -Force -Path $tools | Out-Null;" ^
        "if (-not (Test-Path $zip)) { Invoke-WebRequest -Uri 'https://github.com/git-for-windows/git/releases/download/v2.54.0.windows.1/MinGit-2.54.0-64-bit.zip' -OutFile $zip -UseBasicParsing };" ^
        "if (Test-Path $dest) { Remove-Item -LiteralPath $dest -Recurse -Force };" ^
        "New-Item -ItemType Directory -Force -Path $dest | Out-Null;" ^
        "Expand-Archive -LiteralPath $zip -DestinationPath $dest -Force;"
    if errorlevel 1 (
        echo.
        echo Portable Git install failed. Install Git for Windows manually, then run this file again:
        echo https://git-scm.com/download/win
        echo.
        pause
        exit /b 1
    )
)

if not exist "%GIT_EXE%" (
    echo Git is still missing at:
    echo %GIT_EXE%
    pause
    exit /b 1
)

echo.
echo Using Git:
"%GIT_EXE%" --version

echo.
echo Running tests...
set "PY_EXE=C:\Users\prath\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%PY_EXE%" (
    "%PY_EXE%" -m unittest discover -s tests
) else (
    python -m unittest discover -s tests
)
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Tests failed. Nothing was pushed.
    pause
    exit /b 1
)

echo.
echo Preparing GitHub push...
"%GIT_EXE%" remote get-url origin >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    "%GIT_EXE%" remote add origin https://github.com/prathit23/job-ai-bot.git
)

"%GIT_EXE%" config --global --add safe.directory "%CD%" >nul 2>nul
"%GIT_EXE%" status -sb

echo.
echo Staging project files...
"%GIT_EXE%" add -A

"%GIT_EXE%" diff --cached --quiet
if %ERRORLEVEL% EQU 0 (
    echo No code changes to commit. Pulling and pushing anyway...
) else (
    "%GIT_EXE%" commit -m "Improve job assistant pipeline"
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo Commit failed. Check the message above.
        pause
        exit /b 1
    )
)

echo.
echo Syncing with GitHub...
"%GIT_EXE%" pull --rebase origin main
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Pull/rebase failed. Resolve the issue shown above, then run this file again.
    pause
    exit /b 1
)

echo.
echo Pushing to GitHub...
"%GIT_EXE%" push -u origin main
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Push failed. If GitHub asks for login, complete the browser/device login and run this again.
    pause
    exit /b 1
)

echo.
echo Done. GitHub now has the latest code.
pause
