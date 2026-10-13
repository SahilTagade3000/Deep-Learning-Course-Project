@echo off
setlocal
title Temporal - Check the installed interface
set "UI_PROJECT=%~dp0"
call "%~dp0select_ui_python.cmd"
if errorlevel 1 goto failed
"%UI_PY%" "%~dp0ui_setup.py" --project "%UI_PROJECT%" --check
if errorlevel 1 goto failed
echo.
echo All checks passed.
pause
exit /b 0
:failed
echo.
echo A check failed. See ui_setup.log in this folder for the full output.
pause
exit /b 1
