@echo off
setlocal
cd /d "%~dp0"

:menu
cls
echo AI Job Application Assistant
echo ============================
echo.
echo 1. Run live job pipeline
echo 2. Run sample pipeline
echo 3. Start dashboard
echo 4. Open daily_queue folder
echo 5. Exit
echo.
set /p choice=Choose an option: 

if "%choice%"=="1" call "Run Pipeline.bat" & goto menu
if "%choice%"=="2" call "Run Sample Pipeline.bat" & goto menu
if "%choice%"=="3" call "Start Dashboard.bat" & goto menu
if "%choice%"=="4" start "" "%~dp0daily_queue" & goto menu
if "%choice%"=="5" exit /b 0
goto menu
