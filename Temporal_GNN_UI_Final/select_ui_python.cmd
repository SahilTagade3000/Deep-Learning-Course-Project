@echo off
set "UI_PY="
if exist "%UI_PROJECT%\.venv\Scripts\python.exe" set "UI_PY=%UI_PROJECT%\.venv\Scripts\python.exe"
if not defined UI_PY if exist "%UI_PROJECT%\.venv311\Scripts\python.exe" set "UI_PY=%UI_PROJECT%\.venv311\Scripts\python.exe"
if defined UI_PY exit /b 0
echo Could not find your existing Python environment in:
echo %UI_PROJECT%
echo Expected .venv\Scripts\python.exe or .venv311\Scripts\python.exe.
echo Do not delete your project or artifacts. Share this message for help.
exit /b 1
