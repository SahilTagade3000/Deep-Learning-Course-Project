@echo off
setlocal
title Temporal - Transaction Risk Intelligence
set "UI_PROJECT=%~dp0"
call "%~dp0select_ui_python.cmd"
if errorlevel 1 goto failed
"%UI_PY%" "%~dp0ui_setup.py" --project "%UI_PROJECT%" --launch
if errorlevel 1 goto failed
exit /b 0
:failed
echo.
echo The application stopped. Copy the error above if you need help.
pause
exit /b 1
