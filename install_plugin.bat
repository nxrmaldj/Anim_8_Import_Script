@echo off
cd /d "%~dp0"
echo.
where py >nul 2>&1 && (py -3 install_plugin.py & goto :done)
where python >nul 2>&1 && (python install_plugin.py & goto :done)
echo Python was not found. Install Python 3 from python.org, or run from a terminal where Python works.
:done
if errorlevel 1 pause
