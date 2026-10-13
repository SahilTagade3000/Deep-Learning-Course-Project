@echo off
setlocal
title Temporal - Light Theme
set "UI_PROJECT=%~dp0."
call "%~dp0select_ui_python.cmd"
if errorlevel 1 goto failed
"%UI_PY%" -m streamlit run "%UI_PROJECT%\app_intelligence.py" --server.port 8502 --server.address 127.0.0.1 --theme.base light --theme.primaryColor "#087F70" --theme.backgroundColor "#F5F7FA" --theme.secondaryBackgroundColor "#EBF0F5" --theme.textColor "#22354A"
if errorlevel 1 goto failed
exit /b 0
:failed
echo.
echo Could not start the light theme. Copy the error above for help.
pause
exit /b 1
