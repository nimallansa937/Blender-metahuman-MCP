@echo off
cd /d "%~dp0"
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo WARNING: Virtual environment not found. Run setup.bat first.
    echo Attempting to run with system Python...
)
python -m mcp_server.server %*
