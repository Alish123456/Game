#!/bin/bash
# Quick start script for Zagreus' Descent

echo "Starting Zagreus' Descent..."
echo ""

# Check if Python 3 is available
if command -v python3 &> /dev/null; then
    python3 zagreus_dungeon.py
elif command -v python &> /dev/null; then
    python zagreus_dungeon.py
else
    echo "Error: Python 3 is required but not found."
    echo "Please install Python 3.6 or higher."
    exit 1
fi
