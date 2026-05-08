#!/bin/sh
set -e

python serve_web.py --bind 0.0.0.0 --port "${PORT:-8000}"
