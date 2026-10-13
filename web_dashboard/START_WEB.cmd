@echo off
setlocal
set "WEB_PYTHON="
if exist "%~dp0..\.venv\Scripts\python.exe" set "WEB_PYTHON=%~dp0..\.venv\Scripts\python.exe"
if not defined WEB_PYTHON if exist "%~dp0..\.venv311\Scripts\python.exe" set "WEB_PYTHON=%~dp0..\.venv311\Scripts\python.exe"
if not defined WEB_PYTHON (
    echo Could not find .venv or .venv311 beside the web_dashboard folder.
    echo Put this folder inside your existing project and read READ_ME_FIRST.md.
    pause
    exit /b 1
)
"%WEB_PYTHON%" "%~dp0run_web.py"
if errorlevel 1 (
    echo.
    echo The server stopped. Read the error above and READ_ME_FIRST.md.
    pause
    exit /b 1
)
endlocal
