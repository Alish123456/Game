@echo off
REM Quick start script for Zagreus' Descent (Windows)

echo Starting Zagreus' Descent...
echo.

python zagreus_dungeon.py
if errorlevel 1 (
    echo.
    echo Error: Python is required but not found.
    echo Please install Python 3.6 or higher from python.org
    pause
)
