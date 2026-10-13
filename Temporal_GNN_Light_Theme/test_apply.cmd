@echo off
setlocal
set "PROJECT=C:\Users\LENOVO\Documents\Codex\2026-09-24\https-chatgpt-com-share-6ab52214-703c\work\final_acceptance_project"
if not exist "%PROJECT%\intelligence\theme.py" goto missing
if not exist "%PROJECT%\select_ui_python.cmd" goto missing
if not exist "%~dp0intelligence\theme.py" goto missing
if not exist "%PROJECT%\intelligence\theme.before_light.py.bak" (
  copy /Y "%PROJECT%\intelligence\theme.py" "%PROJECT%\intelligence\theme.before_light.py.bak" >nul
  if errorlevel 1 goto failed
)
copy /Y "%~dp0intelligence\theme.py" "%PROJECT%\intelligence\theme.py" >nul
if errorlevel 1 goto failed
copy /Y "%~dp0START_LIGHT.cmd" "%PROJECT%\START_LIGHT.cmd" >nul
if errorlevel 1 goto failed
echo.
echo LIGHT THEME INSTALLED.
echo In your existing VS Code project terminal, run: .\START_LIGHT.cmd
echo Stop the previous dashboard with Ctrl+C first.
echo The model and artifacts have not been changed.
rem pause
exit /b 0
:missing
echo Could not find the installed dashboard or the extracted update files.
echo Extract the whole ZIP and keep your existing Temporal_GNN_Streamlit folder in place.
:failed
echo Update did not complete. Copy the message above for help.
rem pause
exit /b 1
