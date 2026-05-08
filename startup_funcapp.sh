#!/bin/bash
set -e

export PYTHONUNBUFFERED=1
echo "Installing Python dependencies..."
pip install --no-cache-dir -r requirements.txt 2>&1 | tail -20

echo "Starting Azure Functions..."
exec /home/site/wwwroot/antares.py
