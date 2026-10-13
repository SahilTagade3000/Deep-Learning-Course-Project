@echo off
setlocal
title Temporal - Install the new interface
set "UI_PROJECT=D:\III_TY All Sub\DL\DL_CP\Temporal_GNN_Streamlit"
if not "%~1"=="" set "UI_PROJECT=%~1"
call "%~dp0select_ui_python.cmd"
if errorlevel 1 goto failed
"%UI_PY%" "%~dp0ui_setup.py" --project "%UI_PROJECT%" --install
if errorlevel 1 goto failed
echo.
echo Installation complete. Open START_UI.cmd inside your project folder.
pause
exit /b 0
:failed
echo.
echo Setup stopped. Read the message above and ui_setup.log if it was created.
echo Keep this window open to copy the error. Your trained files were not replaced.
pause
exit /b 1
