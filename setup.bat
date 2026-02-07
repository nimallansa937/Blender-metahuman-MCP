@echo off
echo ============================================
echo  Blender MetaHuman MCP - Setup
echo ============================================
echo.

REM Create virtual environment
echo [1/3] Creating Python virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create venv. Ensure Python 3.10+ is installed.
    pause
    exit /b 1
)

REM Activate and install dependencies
echo [2/3] Installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

echo [3/3] Setup complete!
echo.
echo ============================================
echo  Next Steps:
echo ============================================
echo.
echo  1. Install the Blender addon:
echo     - Open Blender ^>= 4.0
echo     - Edit ^> Preferences ^> Add-ons ^> Install
echo     - Navigate to: %~dp0blender_addon\
echo     - Select __init__.py and install
echo     - Enable "MCP: MetaHuman Face Editor"
echo.
echo  2. Configure Claude Code:
echo     - Copy mcp.json config to your Claude Code settings
echo     - Or add the server entry from mcp.json to your existing config
echo.
echo  3. Run the MCP server:
echo     - Use run_server.bat
echo     - Or: python -m mcp_server.server
echo.
pause
