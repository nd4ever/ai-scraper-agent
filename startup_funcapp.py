#!/usr/bin/env python3
import subprocess
import sys
import os

# Ensure pip is up to date and install requirements
print("Installing Python dependencies...")
subprocess.run([sys.executable, "-m", "pip", "install", "--no-cache-dir", "-r", "requirements.txt"], check=False)

print("Starting Azure Functions Worker...")
subprocess.run([sys.executable, "-m", "azure.functions.worker", "--host", "0.0.0.0"], check=False)
