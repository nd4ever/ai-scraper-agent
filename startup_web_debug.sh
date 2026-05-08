#!/bin/bash
set -e

export PYTHONUNBUFFERED=1

# Log environment
echo "Python version:"
python --version
echo "Current directory:"
pwd
echo "Directory contents:"
ls -la

# Install dependencies if not already installed
if [ -f requirements.txt ]; then
  echo "Installing requirements..."
  pip install --no-cache-dir -r requirements.txt
else
  echo "WARNING: requirements.txt not found"
fi

# Show installed packages
echo "Installed packages:"
pip list

# Start the web server
echo "Starting serve_web.py on port 0.0.0.0:${PORT:-8000}"
python serve_web.py --bind 0.0.0.0 --port "${PORT:-8000}"
